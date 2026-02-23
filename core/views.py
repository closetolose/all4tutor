import csv
import io
import json
import os
import uuid
import zipfile
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_POST
from django.http import FileResponse
from django.template.loader import render_to_string

from .forms import AddLessonForm, AddSubjectForm, ProfileUpdateForm, RegistrationForm, StudyGroupForm
from .models import (
    ConnectionRequest, FilesLibrary, Homework, HomeworkResponse,
    LessonAttendance, Lessons, StudentTariff, StudyGroups, Subjects,
    Transaction, TutorStudentNote, TutorSubjects, Users, StudentBalance,
)
from .utils import send_telegram_notification, send_verification_email
#from ratelimit.decorators import ratelimit
from django.db.models import ProtectedError
from django.core.paginator import Paginator


@login_required
def index(request):
    user_role = 'guest'
    lessons = []
    total_count = 0
    per_page = 10

    tutor_students = []
    tutor_groups = []
    my_subjects = []
    tariffs_list = []
    attendance_map = {}
    student_debt = 0
    homeworks = []
    files = []
    active_hw_count = 0
    active_tutors = []

    try:
        user_profile = request.user.profile
        user_role = user_profile.role
    except Exception:
        if request.user.is_superuser:
            user_role = 'admin'

    if user_role == 'tutor':
        # 1. Оптимизированный запрос уроков для репетитора
        lessons_qs = Lessons.objects.filter(tutor=user_profile).prefetch_related(
            'attendances__student', 'subject', 'materials', 'group__students'
        ).order_by('start_time')  # Обычно новые/ближайшие уроки лучше видеть сверху

        # 2. Фильтрация
        target = request.GET.get('target')
        if target:
            if target.startswith('s'):
                lessons_qs = lessons_qs.filter(student_id=target[1:])
            elif target.startswith('g'):
                lessons_qs = lessons_qs.filter(group_id=target[1:])

        if request.GET.get('date_from'):
            lessons_qs = lessons_qs.filter(start_time__date__gte=request.GET['date_from'])
        if request.GET.get('date_to'):
            lessons_qs = lessons_qs.filter(start_time__date__lte=request.GET['date_to'])
        if request.GET.get('subject'):
            lessons_qs = lessons_qs.filter(subject_id=request.GET['subject'])

        # Пагинация (первая порция данных)
        total_count = lessons_qs.count()
        lessons = lessons_qs[:per_page]

        # 3. Карта посещаемости (для быстрой отметки в JS)
        for lesson in lessons:
            attendance_map[str(lesson.id)] = [
                {
                    "id": att.id,
                    "name": f"{att.student.first_name} {att.student.last_name}",
                    "present": att.was_present
                } for att in lesson.attendances.all()
            ]

        # 4. Данные для форм и тарифов
        tariffs_qs = StudentTariff.objects.filter(tutor=user_profile).values(
            'student_id', 'group_id', 'subject_id', 'price'
        )
        tariffs_list = []
        for t in tariffs_qs:
            t['price'] = float(t['price'])
            tariffs_list.append(t)

        accepted_ids = ConnectionRequest.objects.filter(
            tutor=user_profile,
            status='confirmed'
        ).values_list('student_id', flat=True)

        tutor_students = Users.objects.filter(id__in=accepted_ids)
        tutor_groups = StudyGroups.objects.filter(tutor=user_profile)
        my_subjects = TutorSubjects.objects.filter(tutor=user_profile).select_related('subject')
        files = FilesLibrary.objects.filter(tutor=user_profile).order_by('-upload_date')

    elif user_role == 'student':
        # 1. Оптимизированный запрос уроков для ученика
        # Ученик должен видеть и личные уроки, и уроки своих групп
        lessons_qs = Lessons.objects.filter(
            Q(student=user_profile) | Q(group__students=user_profile)
        ).distinct().prefetch_related('attendances__student', 'subject').order_by('-start_time')

        total_count = lessons_qs.count()
        lessons = lessons_qs[:per_page]  # Теперь переменная lessons заполнена!

        # 2. Доп. данные ученика
        student_debt = LessonAttendance.objects.filter(
            student=user_profile,
            was_present=True,
            is_paid=False
        ).aggregate(Sum('lesson__price'))['lesson__price__sum'] or 0

        homeworks = Homework.objects.filter(student=user_profile).order_by('deadline')
        active_hw = homeworks.filter(status__in=['pending', 'revision']).select_related('tutor')
        active_hw_count = active_hw.count()
        ctive_tutors = list(set([f"{hw.tutor.first_name} {hw.tutor.last_name}" for hw in active_hw]))

        # Логика обработки POST (добавление/удаление предметов)
    if request.method == 'POST' and user_role == 'tutor':
        if 'add_subject' in request.POST:
            subject_name = request.POST.get('subject_name')
            if subject_name:
                subject_obj, _ = Subjects.objects.get_or_create(name=subject_name)
                TutorSubjects.objects.get_or_create(tutor=user_profile, subject=subject_obj)
            return redirect('index')

        if 'delete_subject' in request.POST:
            subj_id = request.POST.get('subject_id')
            TutorSubjects.objects.filter(tutor=user_profile, subject_id=subj_id).delete()
            return redirect('index')

        if 'save_tariff' in request.POST:
            s_id = request.POST.get('t_student')
            g_id = request.POST.get('t_group')
            subj_id = request.POST.get('t_subject')
            val = request.POST.get('t_price')
            StudentTariff.objects.update_or_create(
                tutor=user_profile,
                student_id=s_id if s_id else None,
                group_id=g_id if g_id else None,
                subject_id=subj_id,
                defaults={'price': val}
            )
            return redirect('index')

    context = {
        'lessons': lessons,
        'total_lessons': total_count,
        'has_more': total_count > per_page,
        'role': user_role,
        'user': request.user,
        'my_subjects': my_subjects,
        'tutor_students': tutor_students,
        'tutor_groups': tutor_groups,
        'add_lesson_form': AddLessonForm(tutor=user_profile) if user_role == 'tutor' else None,
        'tariffs_json': json.dumps(tariffs_list),
        'add_subject_form': AddSubjectForm(),
        'files': files,
        'student_debt': student_debt,
        'homeworks': homeworks,
        'attendance_map_json': attendance_map,
        'active_hw_count': active_hw_count,
        'active_tutors': active_tutors,
    }

    return smart_render(request, 'core/index.html', context)

#@ratelimit(key='ip', rate='5/m', block=True)
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.set_password(form.cleaned_data['password'])
                    user.is_active = False

                    user.save()

                    Users.objects.create(
                        user=user,
                        role=form.cleaned_data['role']
                    )

                    send_verification_email(request, user)

                return render(request, 'core/registration_pending.html', {'email': user.email})

            except Exception:
                messages.error(request, "Произошла ошибка при регистрации. Попробуйте еще раз.")
    else:
        form = RegistrationForm()

    return render(request, 'core/register.html', {'form': form})


@login_required
#@ratelimit(key='ip', rate='5/m', block=True)
def edit_profile(request):
    try:
        profile = request.user.profile
    except Users.DoesNotExist:
        profile = Users.objects.create(user=request.user, role='student')

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ProfileUpdateForm(instance=profile)

    return smart_render(request, 'core/edit_profile.html', {'form': form})

#@ratelimit(key='ip', rate='5/m', block=True)
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def confirmations(request):
    incoming_requests = ConnectionRequest.objects.filter(
        student__user=request.user,
        status='pending'
    )
    return smart_render(request, 'core/confirmations.html', {'requests': incoming_requests})


@login_required
@require_POST
def accept_request(request, request_id):
    if request.method != 'POST':
        return redirect('confirmations')
    conn_request = get_object_or_404(
        ConnectionRequest,
        id=request_id,
        student__user=request.user
    )
    conn_request.status = 'confirmed'
    conn_request.save()
    return redirect('confirmations')


@login_required
@require_POST
def reject_request(request, request_id):
    if request.method != 'POST':
        return redirect('confirmations')
    conn_request = get_object_or_404(
        ConnectionRequest,
        id=request_id,
        student__user=request.user
    )
    conn_request.delete()
    return redirect('confirmations')


@login_required
def my_students(request):
    user_profile = request.user.profile

    # Твоя логика сохранения тарифов (оставляем без изменений)
    if request.method == 'POST' and 'save_tariff' in request.POST:
        StudentTariff.objects.update_or_create(
            tutor=user_profile,
            student_id=request.POST.get('t_student') or None,
            group_id=request.POST.get('t_group') or None,
            subject_id=request.POST.get('t_subject'),
            defaults={'price': request.POST.get('t_price')}
        )
        return smart_render(request, 'core/my_students.html')


    # Твои активные связи
    connections = ConnectionRequest.objects.filter(tutor=user_profile, status='confirmed').select_related('student')
    groups = StudyGroups.objects.filter(tutor=user_profile)
    my_subjects = TutorSubjects.objects.filter(tutor=user_profile).select_related('subject')

    return smart_render(request, 'core/my_students.html', {
        'connections': connections,
        'groups': groups,
        'my_subjects': my_subjects
    })


@login_required
def my_tutors(request):
    confirmed_connections = ConnectionRequest.objects.filter(
        student__user=request.user.id,
        status='confirmed'
    )
    return smart_render(request, 'core/my_tutors.html', {'connections': confirmed_connections})


@login_required
def add_student(request):
    if request.method == 'POST':
        target_username = request.POST.get('username')

        try:
            student_auth = AuthUser.objects.get(username=target_username)

            if hasattr(student_auth, 'profile') and student_auth.profile.role == 'student':
                existing = ConnectionRequest.objects.filter(
                    tutor=request.user.profile,
                    student=student_auth.profile
                ).exists()

                if not existing:
                    ConnectionRequest.objects.create(
                        tutor=request.user.profile,
                        student=student_auth.profile,
                        status='pending'
                    )
                    messages.success(request, f"Заявка отправлена пользователю {student_auth.username}!")
                else:
                    messages.warning(request, "Вы уже отправляли заявку этому ученику.")
            else:
                messages.error(request, "Этот пользователь не является учеником.")

        except AuthUser.DoesNotExist:
            messages.error(request, f"Пользователь с логином '{target_username}' не найден.")

    return smart_render(request, 'core/add_student.html')


#@ratelimit(key='ip', rate='5/m', block=True)
def add_lesson(request):
    if request.user.profile.role != 'tutor':
        return redirect('index')

    if request.method == 'POST':
        form = AddLessonForm(request.POST, tutor=request.user.profile)
        if form.is_valid():
            base_start_time = form.cleaned_data.get('start_time')
            duration = form.cleaned_data.get('duration')

            # Фикс 1: Останавливаем выполнение, если данные неверны
            if not (15 <= duration <= 600):
                messages.error(request, "Введите корректную длительность занятия (15-600 мин)")
                return render(request, 'core/add_lesson.html', {'form': form})

            is_recurring = form.cleaned_data.get('is_recurring')
            new_series_id = uuid.uuid4() if is_recurring else None

            repeat_count = form.cleaned_data.get('repeat_count')
            repeat_until = form.cleaned_data.get('repeat_until')
            selected_weekdays = form.cleaned_data.get('weekdays') or []

            # Определяем лимит даты
            if is_recurring:
                if repeat_until:
                    end_date_limit = repeat_until
                elif repeat_count:
                    end_date_limit = base_start_time.date() + timedelta(weeks=repeat_count)
                else:
                    end_date_limit = base_start_time.date() + timedelta(weeks=4)
            else:
                end_date_limit = base_start_time.date()

            created_count = 0
            current_date = base_start_time.date()

            while current_date <= end_date_limit:
                is_first_day = (current_date == base_start_time.date())
                is_selected_day = str(current_date.weekday()) in selected_weekdays

                if not is_recurring or is_first_day or is_selected_day:
                    # Создаем копию объекта из формы
                    lesson = form.save(commit=False)
                    lesson.pk = None
                    lesson.tutor = request.user.profile
                    lesson.series_id = new_series_id

                    # Работа со временем
                    naive_start = timezone.make_naive(base_start_time)
                    new_naive = naive_start.replace(
                        year=current_date.year, month=current_date.month, day=current_date.day,
                        second=0, microsecond=0
                    )
                    new_start = timezone.make_aware(new_naive)
                    lesson.start_time = new_start
                    lesson.end_time = new_start + timedelta(minutes=duration)

                    # Фикс 2: Глобальная проверка коллизий репетитора
                    # Теперь проверяем, нет ли У РЕПЕТИТОРА другого урока в это время вообще
                    overlap_qs = Lessons.objects.filter(
                        tutor=request.user.profile,
                        start_time__lt=lesson.end_time,
                        end_time__gt=lesson.start_time,
                    )

                    if overlap_qs.exists():
                        messages.error(
                            request,
                            f"Коллизия! Вы уже заняты на время {lesson.start_time.strftime('%H:%M')} ({current_date.strftime('%d.%m')})."
                        )
                        # Для серии уроков лучше просто пропустить этот день и идти дальше
                        current_date += timedelta(days=1)
                        continue

                    # Распределяем тип урока
                    if form.cleaned_data.get('lesson_type') == 'individual':
                        lesson.group = None
                    else:
                        lesson.student = None

                    lesson.save()
                    form.save_m2m()
                    created_count += 1

                    # Создаем записи посещаемости
                    students_to_link = []
                    if lesson.group:
                        students_to_link = lesson.group.students.all()
                    elif lesson.student:
                        students_to_link = [lesson.student]

                    for student in students_to_link:
                        LessonAttendance.objects.get_or_create(lesson=lesson, student=student)

                if not is_recurring:
                    break

                current_date += timedelta(days=1)
                if created_count >= 100:  # Защита от бесконечных циклов
                    break

            messages.success(request, f"Успешно создано занятий: {created_count}")
            return redirect('index')
    else:
        form = AddLessonForm(tutor=request.user.profile)

    return smart_render(request, 'core/add_lesson.html', {'form': form})


@login_required
#@ratelimit(key='ip', rate='5/m', block=True)
@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lessons, id=lesson_id, tutor=request.user.profile)

    if request.method == 'POST':
        form = AddLessonForm(request.POST, instance=lesson, tutor=request.user.profile)
        if form.is_valid():
            updated_lesson = form.save(commit=False)

            # Пересчитываем end_time на основе измененной длительности
            duration = form.cleaned_data.get('duration')
            updated_lesson.end_time = updated_lesson.start_time + timedelta(minutes=duration)

            # Фикс: Проверка пересечений (репетитор не может быть в двух местах одновременно)
            overlap_qs = Lessons.objects.filter(
                tutor=request.user.profile,
                start_time__lt=updated_lesson.end_time,
                end_time__gt=updated_lesson.start_time,
            ).exclude(id=lesson.id)

            if overlap_qs.exists():
                messages.error(request, "Ошибка: Это время уже занято другим вашим уроком.")
            else:
                updated_lesson.save()
                form.save_m2m()
                messages.success(request, "Занятие обновлено!")
                return redirect('index')
    else:
        form = AddLessonForm(instance=lesson, tutor=request.user.profile)

    return smart_render(request, 'core/edit_lesson.html', {'form': form, 'lesson': lesson})


@login_required
@require_POST
def delete_lesson(request, lesson_id):
    # Ищем урок, проверяя, что его удаляет именно тот репетитор, который создал
    lesson = get_object_or_404(Lessons, id=lesson_id, tutor=request.user.profile)

    if request.method == 'POST':
        now = timezone.now()

        # 1. Проверяем, прошел ли урок
        is_past = lesson.start_time < now

        # 2. Проверяем, есть ли записи о посещаемости/оплате
        has_attendance = LessonAttendance.objects.filter(lesson=lesson).exists()

        if is_past and has_attendance:
            # Блокируем удаление
            messages.error(
                request,
                "Критическая ошибка: Нельзя удалить прошедший урок, на котором отмечены ученики. "
                "Это необходимо для сохранности истории оплат и балансов."
            )
            return redirect('my_lessons')  # Или страница журнала

        # Если урок будущий или на нем никого не было — удаляем
        lesson.delete()
        messages.success(request, "Урок успешно удален из расписания.")

    return redirect('index')


@login_required
#@ratelimit(key='ip', rate='5/m', block=True)
def edit_group(request, group_id):
    group = get_object_or_404(StudyGroups, id=group_id, tutor=request.user.profile)

    if request.method == 'POST':
        form = StudyGroupForm(request.POST, instance=group, tutor=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Группа '{group.name}' обновлена!")
            return redirect('my_students')
    else:
        form = StudyGroupForm(instance=group, tutor=request.user.profile)

    return smart_render(request, 'core/edit_group.html', {'form': form, 'group': group})


@login_required
@require_POST
def delete_group(request, group_id):
    group = get_object_or_404(StudyGroups, id=group_id, tutor=request.user.profile)
    if request.method == 'POST':
        group.delete()
        messages.success(request, "Группа удалена.")
    return redirect('my_students')


@login_required
@require_POST
def remove_student(request, connection_id):
    connection = get_object_or_404(ConnectionRequest, id=connection_id, tutor=request.user.profile)
    if request.method == 'POST':
        student_name = connection.student.user.get_full_name()
        connection.delete()
        messages.success(request, f"Ученик {student_name} удален из списка.")
    return redirect('my_students')


@login_required
@require_POST
def add_group(request):
    if request.method == 'POST':
        form = StudyGroupForm(request.POST, tutor=request.user.profile)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.tutor = request.user.profile
            new_group.save()
            form.save_m2m()
            messages.success(request, f"Группа '{new_group.name}' успешно создана!")
            return redirect('my_students')
    else:
        form = StudyGroupForm(tutor=request.user.profile)

    return smart_render(request, 'core/create_group.html', {'form': form})


@login_required
@require_POST
#@ratelimit(key='ip', rate='5/m', block=True)
def bulk_action_lessons(request):
    if request.method == 'POST' and request.user.profile.role == 'tutor':
        ids_str = request.POST.get('lesson_ids', '')
        action = request.POST.get('action_type')

        if not ids_str:
            return redirect('index')

        id_list = [i for i in ids_str.split(',') if i.strip()]
        queryset = Lessons.objects.filter(id__in=id_list,tutor=request.user.profile).select_related('group', 'student', 'subject').prefetch_related('group__students')

        if action == 'delete':
            count = queryset.count()
            queryset.delete()
            messages.success(request, f"Удалено занятий: {count}")


        elif action == 'mass_edit':
            new_date = request.POST.get('mass_date')
            new_time = request.POST.get('mass_time')
            new_student = request.POST.get('mass_student')
            new_group = request.POST.get('mass_group')
            new_subject = request.POST.get('mass_subject')
            new_duration = request.POST.get('mass_duration')
            new_price = request.POST.get('mass_price')
            selected_materials = request.POST.getlist('materials')
            new_notes = request.POST.get('notes')

            with transaction.atomic():
                for lesson in queryset:
                    if new_date or new_time:
                        d = new_date if new_date else lesson.start_time.strftime('%Y-%m-%d')
                        t = new_time if new_time else lesson.start_time.strftime('%H:%M')
                        naive_dt = datetime.strptime(f"{d} {t}", '%Y-%m-%d %H:%M')
                        lesson.start_time = timezone.make_aware(naive_dt).replace(second=0, microsecond=0)
                        dur = int(new_duration) if new_duration else lesson.duration
                        lesson.end_time = lesson.start_time + timedelta(minutes=dur)

                    if new_student:
                        lesson.student_id = new_student
                        lesson.group = None
                    elif new_group:
                        lesson.group_id = new_group
                        lesson.student = None

                    if new_subject:
                        lesson.subject_id = new_subject
                    if new_duration:
                        lesson.duration = int(new_duration)
                    if new_price:
                        lesson.price = Decimal(new_price)
                    if new_notes:
                        lesson.notes = new_notes

                    lesson.save()

                    if 'materials_updated' in request.POST:
                        # Очищаем от пустых строк на всякий случай
                        valid_materials = [m for m in selected_materials if m.strip()]
                        lesson.materials.set(valid_materials)

                    if new_student or new_group:
                        lesson.attendances.all().delete()
                        students_to_add = [lesson.student] if lesson.student else []
                        if lesson.group:
                            students_to_add = lesson.group.students.all()
                        attendances = [LessonAttendance(lesson=lesson, student=s) for s in students_to_add]
                        LessonAttendance.objects.bulk_create(attendances)

            messages.success(request, f"Обновлено занятий: {queryset.count()}")

    return redirect('index')


@login_required
@require_POST
#@ratelimit(key='ip', rate='5/m', block=True)
def toggle_attendance_pay(request, attendance_id):
    attendance = get_object_or_404(
        LessonAttendance,
        id=attendance_id,
        lesson__tutor=request.user.profile,
    )

    tutor = request.user.profile

    with transaction.atomic():
        balance_obj, _ = StudentBalance.objects.select_for_update().get_or_create(
            tutor=tutor,
            student=attendance.student,
        )
        price = attendance.lesson.price

        if not attendance.is_paid:
            if price <= 0:
                return JsonResponse({'status': 'error', 'message': 'Цена должна быть > 0'}, status=400)

            if balance_obj.balance < price:
                return JsonResponse({'status': 'error', 'message': 'Недостаточно средств'}, status=400)

            balance_obj.balance -= price
            attendance.is_paid = True
            Transaction.objects.create(
                student=attendance.student,
                tutor=tutor,
                attendance=attendance,
                amount=price,
                type='withdrawal',
                description=f"Оплата: {attendance.lesson.subject.name} ({attendance.lesson.start_time.strftime('%d.%m')})",
            )
        else:
            balance_obj.balance += price
            attendance.is_paid = False
            Transaction.objects.filter(
                attendance=attendance,
                type='withdrawal',
            ).delete()

        balance_obj.save()
        attendance.save()

    # перерасчёт долга именно перед этим репетитором
    now = timezone.now()
    new_total_debt = LessonAttendance.objects.filter(
        student=attendance.student,
        lesson__tutor=tutor,
        was_present=True,
        lesson__start_time__lt=now,
        is_paid=False,
    ).aggregate(total=Sum('lesson__price'))['total'] or 0
    new_total_debt = max(0, new_total_debt - balance_obj.balance)

    return JsonResponse({
        'status': 'ok',
        'is_paid': attendance.is_paid,
        'new_balance': float(balance_obj.balance),
        'new_total_debt': float(new_total_debt),
    })


@login_required
#@ratelimit(key='ip', rate='5/m', block=True)
def student_card(request, student_id):
    tutor = request.user.profile
    student = get_object_or_404(Users, id=student_id)
    now = timezone.now()
    note_obj, created = TutorStudentNote.objects.get_or_create(tutor=tutor, student=student)
    if request.user.profile.role != 'tutor':
        return redirect('index')
    has_access = ConnectionRequest.objects.filter(
        tutor=tutor,
        student=student,
        status__in=['confirmed', 'archived']
    ).exists()
    if not has_access:
        messages.error(request, "Ошибка доступа: это не ваш ученик.")
        return redirect('my_students')
    # Пополнение баланса
    if request.method == 'POST' and 'update_balance' in request.POST:
        raw_amount = request.POST.get('amount', '').replace(',', '.')
        try:
            amount = Decimal(raw_amount)
        except Exception:
            messages.error(request, "Некорректная сумма пополнения.")
            return redirect('student_card', student_id=student.id)

        if amount <= 0:
            messages.error(request, "Сумма пополнения должна быть больше нуля")
            return redirect('student_card', student_id=student.id)

        desc = request.POST.get('description', 'Пополнение баланса')
        custom_date = request.POST.get('date')

        try:
            tx_date = (
                datetime.strptime(custom_date, '%Y-%m-%dT%H:%M')
                if custom_date else timezone.now()
            )
        except ValueError:
            messages.error(request, "Некорректная дата.")
            return redirect('student_card', student_id=student.id)

        with transaction.atomic():
            balance_obj, _ = StudentBalance.objects.select_for_update().get_or_create(
                tutor=tutor,
                student=student,
            )

            Transaction.objects.create(
                student=student,
                tutor=tutor,
                amount=amount,
                type='deposit',
                description=desc,
                date=tx_date,
            )

            balance_obj.balance += amount
            balance_obj.save()

        messages.success(request, "Баланс пополнен")
        return redirect('student_card', student_id=student.id)

    # Сохранение заметки
    if request.method == 'POST' and 'save_tutor_note' in request.POST:
        note_obj.text = request.POST.get('tutor_note_text')
        note_obj.save()
        messages.success(request, "Заметка сохранена")
        return redirect('student_card', student_id=student.id)

    # Данные для отображения
    attendances = LessonAttendance.objects.filter(
        student=student,
        lesson__tutor=tutor,
        was_present=True,
        lesson__start_time__lt=now,
    ).select_related('lesson', 'lesson__subject').order_by('-lesson__start_time')

    total_debt = attendances.filter(is_paid=False).aggregate(
        total=Sum('lesson__price')
    )['total'] or 0

    homeworks = Homework.objects.filter(
        student=student,
        tutor=tutor,
    ).prefetch_related('files', 'responses').order_by('-created_at')

    tutor_files = FilesLibrary.objects.filter(tutor=tutor).order_by('-upload_date')
    subjects = Subjects.objects.filter(tutorsubjects__tutor=tutor)

    # баланс ученика у этого репетитора
    balance_obj, _ = StudentBalance.objects.get_or_create(
        tutor=tutor,
        student=student,
    )

    context = {
        'student': student,
        'attendances': attendances,
        'total_debt': total_debt,
        'homeworks': homeworks,
        'tutor_files': tutor_files,
        'subjects': subjects,
        'transactions': student.transactions.filter(tutor=tutor).order_by('-date'),
        'performance': student.performance.all().order_by('-date')[:10],
        'tutor_note': note_obj.text,
        'balance': balance_obj.balance,
    }

    return smart_render(request, 'core/student_card.html', context)


@login_required
#@ratelimit(key='ip', rate='5/m', block=True)
def add_homework(request, student_id):
    if request.method == 'POST':
        tutor = request.user.profile
        student = get_object_or_404(Users, id=student_id)

        subject_id = request.POST.get('subject')
        subject_obj = get_object_or_404(Subjects, id=subject_id)

        deadline_raw = request.POST.get('deadline')
        description = request.POST.get('description')

        hw = Homework.objects.create(
            tutor=tutor,
            student=student,
            subject=subject_obj,
            description=description,
            deadline=deadline_raw or None
        )

        deadline_obj = parse_datetime(deadline_raw) if deadline_raw else None
        deadline_display = deadline_obj.strftime('%d.%m %H:%M') if deadline_obj else 'Не задан'

        msg = (
            f"📚 <b>Новое задание!</b>\n"
            f"Предмет: {subject_obj.name}\n"
            f"Преподаватель: {tutor.first_name}\n"
            f"Срок: {deadline_display}\n\n"
            f"Посмотреть: <a href='https://all4tutors.ru/my-assignments/'>Перейти на сайт</a>"
        )

        if student.telegram_id:
            send_telegram_notification(student, msg)

        file_ids = request.POST.getlist('files')
        if file_ids:
            hw.files.set(file_ids)

        messages.success(request, "Домашнее задание добавлено")

    return redirect('student_card', student_id=student_id)


@login_required
@require_POST
def toggle_presence(request, attendance_id):
    attendance = get_object_or_404(LessonAttendance, id=attendance_id, lesson__tutor=request.user.profile)
    attendance.was_present = not attendance.was_present
    attendance.save()
    return JsonResponse({'status': 'ok', 'was_present': attendance.was_present})


@login_required

def files_library(request):
    user_profile = request.user.profile
    MAX_SIZE = 10 * 1024 * 1024
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        if uploaded_file.size > MAX_SIZE:
            messages.error(request, "Файл слишком большой (макс 10MB).")
            return redirect('files_library')
        FilesLibrary.objects.create(
            tutor=user_profile,
            file=uploaded_file,
            file_name=request.POST.get('file_name') or uploaded_file.name
        )
        messages.success(request, "Файл успешно добавлен в библиотеку!")
        return redirect('files_library')

    files = FilesLibrary.objects.filter(tutor=user_profile).order_by('-upload_date')[:20]
    return smart_render(request, 'core/files_library.html', {'files': files})


@login_required
@require_POST
#@ratelimit(key='ip', rate='5/m', block=True)
def edit_file(request, file_id):
    file_obj = get_object_or_404(FilesLibrary, id=file_id, tutor=request.user.profile)
    if request.method == 'POST':
        new_name = request.POST.get('file_name')
        if new_name:
            file_obj.file_name = new_name

        if request.FILES.get('file'):
            if file_obj.file:
                file_obj.file.delete(save=False)
            file_obj.file = request.FILES['file']

        file_obj.save()
        messages.success(request, "Материал успешно обновлен")
    return redirect('files_library')


@login_required
@require_POST
def delete_file(request, file_id):
    file_obj = get_object_or_404(FilesLibrary, id=file_id, tutor=request.user.profile)
    if request.method == 'POST':
        if file_obj.file:
            file_obj.file.delete()
        file_obj.delete()
        messages.success(request, "Файл удален")
    return redirect('files_library')


@login_required
def download_lesson_materials(request, lesson_id):
    user_profile = request.user.profile

    lesson = get_object_or_404(
        Lessons.objects.select_related('tutor', 'group'),
        id=lesson_id,
    )

    is_tutor = lesson.tutor_id == user_profile.id
    is_individual_student = lesson.student_id == user_profile.id
    is_group_student = (
        lesson.group
        and lesson.group.students.filter(id=user_profile.id).exists()
    )

    if not (is_tutor or is_individual_student or is_group_student):
        messages.error(request, "У вас нет доступа к материалам этого урока.")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    files = lesson.materials.all()
    if not files:
        messages.warning(request, "К этому уроку не прикреплено ни одного файла.")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for f in files:
            if f.file and os.path.exists(f.file.path):
                ext = os.path.splitext(f.file.name)[1]
                name_in_zip = f.file_name if f.file_name.endswith(ext) else f.file_name + ext
                zip_file.write(f.file.path, name_in_zip)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="materials_lesson_{lesson_id}.zip"'
    return response


@login_required
def download_homework_all(request, hw_id):
    user_profile = request.user.profile

    hw = get_object_or_404(
        Homework.objects.select_related('tutor', 'student'),
        id=hw_id,
    )

    is_tutor = hw.tutor_id == user_profile.id
    is_student = hw.student_id == user_profile.id

    if not (is_tutor or is_student):
        messages.error(request, "У вас нет доступа к этим файлам.")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    files = hw.files.all()
    if not files:
        messages.warning(request, "Файлов для скачивания нет")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_f:
        for f in files:
            if f.file and os.path.exists(f.file.path):
                ext = os.path.splitext(f.file.name)[1]
                name_in_zip = f.file_name if f.file_name.endswith(ext) else f.file_name + ext
                zip_f.write(f.file.path, name_in_zip)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="homework_{hw_id}_files.zip"'
    return response



@login_required
def download_homework_response(request, response_id):
    user_profile = request.user.profile

    response_obj = get_object_or_404(
        HomeworkResponse.objects.select_related('homework__tutor', 'homework__student'),
        id=response_id,
    )
    hw = response_obj.homework

    is_tutor = hw.tutor_id == user_profile.id
    is_student = hw.student_id == user_profile.id

    if not (is_tutor or is_student):
        messages.error(request, "У вас нет доступа к этому файлу.")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    if not response_obj.file or not os.path.exists(response_obj.file.path):
        messages.error(request, "Файл не найден.")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    ext = os.path.splitext(response_obj.file.name)[1]
    filename = response_obj.file_name if response_obj.file_name.endswith(ext) else response_obj.file_name + ext

    return FileResponse(
        open(response_obj.file.path, 'rb'),
        as_attachment=True,
        filename=filename,
    )


@login_required
@require_POST
#@ratelimit(key='ip', rate='5/m', block=True)
def edit_homework(request, hw_id):
    hw = get_object_or_404(Homework, id=hw_id, tutor=request.user.profile)
    if request.method == 'POST':
        if request.POST.get('description'):
            hw.description = request.POST.get('description')
        if request.POST.get('subject'):
            hw.subject_id = request.POST.get('subject')
        if request.POST.get('deadline'):
            hw.deadline = request.POST.get('deadline')

        if request.POST.get('status'):
            hw.status = request.POST.get('status')
        if 'tutor_comment' in request.POST:
            hw.tutor_comment = request.POST.get('tutor_comment')

        file_ids = request.POST.getlist('files')
        if file_ids:
            hw.files.set(file_ids)

        hw.save()
        messages.success(request, "Задание обновлено")
    return redirect('student_card', student_id=hw.student.id)


@login_required
@require_POST
def delete_homework(request, hw_id):
    hw = get_object_or_404(Homework, id=hw_id, tutor=request.user.profile)
    student_id = hw.student.id
    if request.method == 'POST':
        hw.delete()
        messages.success(request, "Задание удалено")
    return redirect('student_card', student_id=student_id)


@login_required
#@ratelimit(key='ip', rate='5/m', block=True)
def toggle_homework_status(request, hw_id):
    hw = get_object_or_404(Homework, id=hw_id, tutor=request.user.profile)
    status_cycle = {
        'pending': 'submitted',
        'submitted': 'revision',
        'revision': 'completed',
        'completed': 'pending',
    }
    hw.status = status_cycle.get(hw.status, 'pending')
    hw.save()
    return redirect('student_card', student_id=hw.student.id)


@login_required
def finances(request):
    tutor = request.user.profile

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    attendance_qs = LessonAttendance.objects.filter(
        lesson__tutor=tutor,
        was_present=True
    ).select_related('lesson', 'lesson__subject', 'student').order_by('-lesson__start_time')

    if date_from:
        attendance_qs = attendance_qs.filter(lesson__start_time__date__gte=date_from)
    if date_to:
        attendance_qs = attendance_qs.filter(lesson__start_time__date__lte=date_to)

    if not date_from and not date_to:
        last_30_days = timezone.now() - timedelta(days=30)
        chart_qs = attendance_qs.filter(lesson__start_time__gte=last_30_days)
    else:
        chart_qs = attendance_qs

    total_earned = attendance_qs.filter(is_paid=True).aggregate(Sum('lesson__price'))['lesson__price__sum'] or 0
    total_debt = attendance_qs.filter(is_paid=False).aggregate(Sum('lesson__price'))['lesson__price__sum'] or 0

    stats_raw = chart_qs.values('lesson__start_time__date').annotate(
        total=Sum('lesson__price')
    ).order_by('lesson__start_time__date')

    chart_labels = [s['lesson__start_time__date'].strftime('%d.%m') for s in stats_raw]
    chart_values = [float(s['total']) for s in stats_raw]

    transactions = Transaction.objects.filter(tutor=tutor).order_by('-date')

    context = {
        'total_earned': total_earned,
        'total_debt': total_debt,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'attendances': attendance_qs,
        'transactions': transactions,
        'date_from': date_from,
        'date_to': date_to,
    }
    return smart_render(request, 'core/finances.html', context)


@login_required
@require_POST
#@ratelimit(key='ip', rate='5/m', block=True)
def submit_homework(request, hw_id):
    homework = get_object_or_404(Homework, id=hw_id, student=request.user.profile)
    user_profile = request.user.profile

    if request.method == 'POST':
        # 1. Получаем файлы, загруженные напрямую с ПК (из my_assignments)
        uploaded_files = request.FILES.getlist('response_files')

        # 2. Получаем ID файлов, выбранных из библиотеки (из tutor_card / student_card)
        library_file_ids = request.POST.getlist('response_files')

        added_new = False

        # Обрабатываем загрузку с компьютера
        if uploaded_files:
            for f in uploaded_files:
                # ПРОВЕРКА НА ДУБЛИКАТ: Ищем файл с таким же именем в этом ДЗ
                if not HomeworkResponse.objects.filter(homework=homework, file_name=f.name).exists():
                    HomeworkResponse.objects.create(
                        homework=homework,
                        file=f,
                        file_name=f.name,
                        student=user_profile
                    )
                    added_new = True

        # Обрабатываем выбор из библиотеки
        if library_file_ids:
            for f_id in library_file_ids:
                try:
                    lib_file = FilesLibrary.objects.get(id=f_id, tutor=user_profile)
                    # ПРОВЕРКА НА ДУБЛИКАТ:
                    if not HomeworkResponse.objects.filter(homework=homework, file_name=lib_file.file_name).exists():
                        HomeworkResponse.objects.create(
                            homework=homework,
                            file=lib_file.file,
                            file_name=lib_file.file_name,
                            student=user_profile
                        )
                        added_new = True
                except FilesLibrary.DoesNotExist:
                    continue

        # Если были переданы хоть какие-то файлы
        if added_new or uploaded_files or library_file_ids:
            homework.status = 'submitted'
            homework.save()

            tutor = homework.tutor
            if tutor.telegram_id:
                msg = (
                    f"✅ <b>Задание сдано на проверку!</b>\n\n"
                    f"<b>Ученик:</b> {user_profile.first_name} {user_profile.last_name}\n"
                    f"<b>Предмет:</b> {homework.subject.name}\n"
                    f"<b>Задание:</b> {homework.description[:50]}...\n\n"
                    f"🧐 <a href='https://all4tutors.ru/student-card/{user_profile.id}/'>Перейти к проверке</a>"
                )
                send_telegram_notification(tutor, msg)

            if added_new:
                messages.success(request, "Задание успешно отправлено!")
            else:
                messages.info(request,
                              "Эти файлы уже были прикреплены ранее. Статус задания обновлен на «На проверке».")
        else:
            messages.error(request, "Файлы не были выбраны.")

        # Возвращаем пользователя на ту страницу, с которой он отправлял форму
        return redirect(request.META.get('HTTP_REFERER', 'my_assignments'))


@login_required
def my_assignments(request):
    profile = request.user.profile

    if profile.role != 'student':
        return redirect('index')

    homeworks = Homework.objects.filter(student=profile).order_by('-deadline')

    context = {
        'homeworks': homeworks,
        'profile': profile,
    }
    return smart_render(request, 'core/my_assignments.html', context)


@login_required
def my_subjects(request):
    tutor = getattr(request.user, 'profile', None)
    if not tutor:
        tutor = Users.objects.filter(user=request.user).first()
    if not tutor:
        tutor = Users.objects.create(user=request.user)
    if request.method == 'POST':
        subject_name = request.POST.get('name')
        if subject_name:
            subject, _ = Subjects.objects.get_or_create(
                name=subject_name.strip(),
                tutor=tutor
            )
            TutorSubjects.objects.get_or_create(tutor=tutor, subject=subject)
            messages.success(request, f"Предмет '{subject_name}' добавлен!")
        return smart_render(request, 'core/my_subjects.html')

    subjects = Subjects.objects.filter(tutor=tutor)
    return smart_render(request, 'core/my_subjects.html', {'subjects': subjects})


@login_required
def edit_subject(request, subject_id):
    # Получаем предмет, проверяя принадлежность текущему репетитору
    subject = get_object_or_404(Subjects, id=subject_id, tutor=request.user.profile)

    if request.method == 'POST':
        new_name = request.POST.get('name')
        if new_name:
            subject.name = new_name.strip()
            subject.save()
            messages.success(request, f"Предмет успешно переименован в '{new_name}'")
        else:
            messages.error(request, "Название предмета не может быть пустым")

    return redirect('my_subjects')
@login_required
@require_POST
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subjects, id=subject_id, tutor=request.user.profile)
    try:
        subject.delete()
        messages.success(request, "Предмет успешно удален.")
    except ProtectedError:
        messages.error(request, "Нельзя удалить предмет: по нему уже проведены уроки. Сначала удалите уроки.")

    return redirect('my_subjects')


@login_required
def faq(request):
    return smart_render(request, 'core/faq.html')


def smart_render(request, template_name, context=None):
    if getattr(request, 'is_mobile', False):
        mobile_template = template_name.replace('core/', 'mobile/')
        try:
            get_template(mobile_template)
            return render(request, mobile_template, context)
        except TemplateDoesNotExist:
            pass
    return render(request, template_name, context)


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Твой аккаунт активирован! Теперь заходи в систему.")
        return redirect('login')
    else:
        return render(request, 'core/activation_invalid.html')


@login_required
def group_card(request, group_id):
    tutor = request.user.profile
    group = get_object_or_404(StudyGroups, id=group_id, tutor=tutor)
    now = timezone.now()

    if request.method == 'POST' and 'assign_group_homework' in request.POST:
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        file_ids = request.POST.getlist('files')

        for student in group.students.all():
            hw = Homework.objects.create(
                tutor=tutor,
                student=student,
                subject=group.subject,
                description=description,
                deadline=deadline if deadline else None
            )
            if file_ids:
                hw.files.set(file_ids)

        messages.success(request, "Задание отправлено всей группе")
        return redirect('group_card', group_id=group.id)

    attendances = LessonAttendance.objects.filter(
        lesson__group=group,
        lesson__tutor=tutor
    ).select_related('lesson', 'lesson__subject', 'student').order_by('-lesson__start_time')

    tutor_files = FilesLibrary.objects.filter(tutor=tutor).order_by('-upload_date')

    context = {
        'group': group,
        'attendances': attendances,
        'members': group.students.all(),
        'tutor_files': tutor_files,
    }
    return smart_render(request, 'core/group_card.html', context)


@login_required
def load_more_lessons(request):
    """AJAX: Подгрузка уроков для репетитора и ученика"""
    page = int(request.GET.get('page', 1))
    per_page = 10
    user_profile = request.user.profile
    role = user_profile.role

    # Выбираем базу уроков в зависимости от роли
    if role == 'tutor':
        lessons_qs = Lessons.objects.filter(tutor=user_profile).prefetch_related('attendances__student',  'subject', 'group__students').order_by('start_time')
    else:
        lessons_qs = Lessons.objects.filter(
            Q(student=user_profile) | Q(group__students=user_profile)
        ).distinct().prefetch_related('attendances__student', 'subject').order_by('start_time')

    # Применяем фильтры (те же, что в index)
    lessons_qs = lessons_qs.prefetch_related(
        'attendances__student', 'subject', 'materials', 'group__students'
    ).order_by('-start_time')

    target = request.GET.get('target')
    if target and role == 'tutor':
        if target.startswith('s'):
            lessons_qs = lessons_qs.filter(student_id=target[1:])
        elif target.startswith('g'):
            lessons_qs = lessons_qs.filter(group_id=target[1:])

    if request.GET.get('date_from'):
        lessons_qs = lessons_qs.filter(start_time__date__gte=request.GET['date_from'])
    if request.GET.get('date_to'):
        lessons_qs = lessons_qs.filter(start_time__date__lte=request.GET['date_to'])
    if request.GET.get('subject'):
        lessons_qs = lessons_qs.filter(subject_id=request.GET['subject'])

    # Слайс данных
    start = (page - 1) * per_page
    end = page * per_page
    lessons = list(lessons_qs[start:end])

    # Рендерим строки
    html = render_to_string('core/lessons_rows.html', {
        'lessons': lessons,
        'role': role
    }, request=request)

    has_more = lessons_qs.count() > end
    return JsonResponse({'html': html, 'has_more': has_more})


@login_required
def logout_all_devices(request):
    if request.method == 'POST':
        user_profile = request.user.profile
        new_key = uuid.uuid4()
        user_profile.session_key = new_key
        user_profile.save()

        request.session['user_session_key'] = str(new_key)

        messages.success(request, "Вы вышли со всех остальных устройств.")
        return redirect('edit_profile')


@login_required
def tutor_card(request, tutor_id):
    # Получаем профиль ученика и репетитора
    student_profile = request.user.profile
    tutor = get_object_or_404(Users, id=tutor_id, role='tutor')

    # Используем LessonAttendance вместо несуществующей модели Attendance
    attendances = LessonAttendance.objects.filter(
        student=student_profile,
        lesson__tutor=tutor,
        was_present=True
    ).select_related('lesson', 'lesson__subject').order_by('-lesson__start_time')

    # ДЗ именно от этого репетитора
    homeworks = Homework.objects.filter(
        student=student_profile,
        tutor=tutor
    ).prefetch_related('files', 'responses').order_by('-created_at')

    # Финансы (транзакции ученика именно с этим репетитором)
    transactions = Transaction.objects.filter(
        student=student_profile,
        tutor=tutor
    ).order_by('-date')

    # Получаем баланс ученика у этого конкретного репетитора
    balance_obj, _ = StudentBalance.objects.get_or_create(
        tutor=tutor,
        student=student_profile,
    )

    # Считаем сумму долга за неоплаченные уроки
    total_debt = attendances.filter(is_paid=False,was_present=True).aggregate(
        total=Sum('lesson__price')
    )['total'] or 0

    context = {
        'tutor': tutor,
        'student': student_profile,
        'attendances': attendances,
        'homeworks': homeworks,
        'transactions': transactions,
        'balance': balance_obj.balance,
        'total_debt': total_debt,
    }
    return smart_render(request, 'core/tutor_card.html', context)


# views.py

@login_required
@require_POST
def archive_student(request, student_id):
    tutor = request.user.profile
    student = get_object_or_404(Users, id=student_id, role='student')
    now = timezone.now()

    # 1. Проверка долга: был на уроке (was_present), но не оплатил
    has_debt = LessonAttendance.objects.filter(
        student=student,
        lesson__tutor=tutor,
        was_present=True,
        is_paid=False
    ).exists()

    if has_debt:
        messages.error(request, f"Ошибка: У {student.first_name} есть долг. Закройте его в журнале.")
        return redirect('my_students')

    # 2. Очистка расписания
    # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Удаляем сами объекты будущих ИНДИВИДУАЛЬНЫХ уроков
    Lessons.objects.filter(
        tutor=tutor,
        student=student,
        start_time__gt=now
    ).delete()

    # Чистим записи посещаемости (это уберет ученика из будущих групповых уроков)
    att_qs = LessonAttendance.objects.filter(student=student, lesson__tutor=tutor)
    att_qs.filter(lesson__start_time__gt=now).delete() # Будущие
    att_qs.filter(lesson__start_time__lt=now, was_present=False).delete() # Прошлые прогулы

    # 3. Исключаем из всех групп
    for group in StudyGroups.objects.filter(tutor=tutor, students=student):
        group.students.remove(student)

    # 4. Разрываем связь (используем tutor/student на основе твоих FieldError)
    ConnectionRequest.objects.filter(
        tutor=tutor,
        student=student,
        status='confirmed'
    ).update(status='archived')
    messages.success(request, f"Ученик {student.first_name} переведен в архив.")
    return smart_render(request, 'core/my_students.html')


@login_required
def archived_students(request):
    tutor = request.user.profile

    # Исправленный фильтр: используем lessonattendance и корректные поля ConnectionRequest
    archived_ids = ConnectionRequest.objects.filter(
        tutor=tutor,
        status='archived'
    ).values_list('student_id', flat=True)

    students = Users.objects.filter(id__in=archived_ids).distinct()

    return smart_render(request, 'core/archived_students.html', {'students': students})


@login_required
@require_POST
def restore_student(request, student_id):
    tutor = request.user.profile
    student = get_object_or_404(Users, id=student_id, role='student')

    # Создаем или обновляем связь, ставя статус 'confirmed'
    ConnectionRequest.objects.update_or_create(
        tutor=tutor,
        student=student,
        defaults={'status': 'confirmed'}
    )

    messages.success(request, f"Ученик {student.first_name} успешно возвращен из архива!")
    # После восстановления логично сразу перейти к списку активных учеников
    return smart_render(request, 'core/archived_students.html')


@login_required
def homework_detail(request, hw_id):
    user_profile = request.user.profile

    # Достаем задание со всеми связями, чтобы не делать лишних запросов к БД
    hw = get_object_or_404(
        Homework.objects.select_related('tutor', 'student'),
        id=hw_id
    )

    # Проверка прав: чужие зайти не смогут
    is_tutor = hw.tutor_id == user_profile.id
    is_student = hw.student_id == user_profile.id

    if not (is_tutor or is_student):
        messages.error(request, "У вас нет доступа к этому заданию.")
        return redirect('index')

    # Достаем ответы ученика (если связь называется 'responses', замени на свое имя related_name)
    # Если ты не задавал related_name, то по умолчанию это homeworkresponse_set
    responses = hw.responses.all()  # или hw.homeworkresponse_set.all()

    context = {
        'hw': hw,
        'responses': responses,
        'is_tutor': is_tutor,
    }
    return render(request, 'core/homework_detail.html', context)


@login_required
def api_get_user_files(request):
    user_profile = request.user.profile
    query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    # 1. Достаем файлы только текущего репетитора из правильной модели
    # Сортируем по дате загрузки (самые новые сверху)
    files = FilesLibrary.objects.filter(tutor=user_profile).order_by('-upload_date')

    # 2. Живой поиск по названию
    if query:
        files = files.filter(file_name__icontains=query)

    # 3. Пагинация: отдаем по 20 файлов за раз
    paginator = Paginator(files, 20)
    page_obj = paginator.get_page(page_number)

    # 4. Формируем JSON ответ
    files_data = []
    for f in page_obj:
        # У тебя в модели FilesLibrary есть метод get_extension(),
        # но можно достать расширение и так:
        ext = str(f.file.name).split('.')[-1].lower() if f.file else 'file'

        files_data.append({
            'id': f.id,
            'name': f.file_name,
            'ext': ext
        })

    return JsonResponse({
        'files': files_data,
        'has_next': page_obj.has_next()
    })


@login_required
def load_more_files(request):
    """AJAX: Подгрузка следующих файлов библиотеки"""
    page = int(request.GET.get('page', 1))
    per_page = 20
    user_profile = request.user.profile

    files_qs = FilesLibrary.objects.filter(tutor=user_profile).order_by('-upload_date')

    start = (page - 1) * per_page
    end = page * per_page
    files = list(files_qs[start:end])

    # Рендерим HTML только для новых карточек
    html = render_to_string('core/files_rows.html', {'files': files}, request=request)

    has_more = files_qs.count() > end
    return JsonResponse({'html': html, 'has_more': has_more})


@login_required
def download_library_file(request, file_id):
    # Ищем файл и проверяем, что он принадлежит этому репетитору
    file_obj = get_object_or_404(FilesLibrary, id=file_id, tutor=request.user.profile)

    if not file_obj.file or not os.path.exists(file_obj.file.path):
        messages.error(request, "Файл не найден на сервере.")
        return redirect(request.META.get('HTTP_REFERER', 'files_library'))

    # Формируем правильное имя с расширением
    ext = os.path.splitext(file_obj.file.name)[1]
    filename = file_obj.file_name if file_obj.file_name.endswith(ext) else file_obj.file_name + ext

    # Отдаем файл через Django
    return FileResponse(
        open(file_obj.file.path, 'rb'),
        as_attachment=True,  # True - скачивание, False - открытие в браузере
        filename=filename,
    )


@login_required
def export_lessons_csv(request):
    user_profile = request.user.profile

    # Получаем параметры
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    pay_status = request.GET.get('pay_status')
    lesson_type = request.GET.get('lesson_type')
    subject_id = request.GET.get('subject_id')
    student_id = request.GET.get('student_id')

    # Базовый запрос
    lessons = Lessons.objects.filter(tutor=user_profile).select_related('student', 'group', 'subject')

    # 1. Фильтр по датам
    if date_from:
        lessons = lessons.filter(start_time__date__gte=date_from)
    if date_to:
        lessons = lessons.filter(start_time__date__lte=date_to)

    # 2. Фильтр по оплате
    if pay_status == 'paid':
        lessons = lessons.filter(is_paid=True)
    elif pay_status == 'debt':
        lessons = lessons.filter(is_paid=False)

    # 3. ИСПРАВЛЕННЫЙ Фильтр по формату (индив/группа)
    if lesson_type == 'individual':
        lessons = lessons.filter(student__isnull=False)
    elif lesson_type == 'group':
        lessons = lessons.filter(group__isnull=False)

    # 4. Фильтр по предмету
    if subject_id:
        lessons = lessons.filter(subject_id=subject_id)

    # 5. ИСПРАВЛЕННЫЙ Фильтр по ученику
    if student_id:
        lessons = lessons.filter(student_id=student_id)

    # Сортировка
    lessons = lessons.order_by('-start_time')

    # Формируем Excel
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="filtered_lessons_report.csv"'
    writer = csv.writer(response, delimiter=';')

    writer.writerow(['Дата', 'Время', 'Тип', 'Ученик/Группа', 'Предмет', 'Цена (₽)', 'Статус оплаты'])

    for lesson in lessons:
        # ИСПРАВЛЕННОЕ определение типа и участника
        if lesson.student:
            participant = f"{lesson.student.first_name} {lesson.student.last_name}"
            l_type = "Индивидуальное"
        elif lesson.group:
            participant = f"Группа: {lesson.group.name}"
            l_type = "Групповое"
        else:
            participant = "Не указан"
            l_type = "Неизвестно"

        writer.writerow([
            lesson.start_time.strftime('%d.%m.%Y'),
            lesson.start_time.strftime('%H:%M'),
            l_type,
            participant,
            lesson.subject.name if lesson.subject else '',
            lesson.price,
            'Оплачено' if lesson.is_paid else 'Долг'
        ])

    return response


@login_required
@require_POST
def delete_homework_response(request, response_id):
    # Находим ответ
    response_obj = get_object_or_404(HomeworkResponse, id=response_id)
    hw = response_obj.homework

    # Проверка безопасности: удалить может только автор (ученик)
    if request.user.profile != response_obj.student:
        messages.error(request, "У вас нет прав для удаления этого файла.")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    # Запрещаем удалять, если ДЗ уже принято
    if hw.status == 'completed':
        messages.error(request, "Нельзя удалять файлы из завершенного задания.")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    # Удаляем и возвращаем обратно
    response_obj.delete()
    messages.success(request, "Ответ успешно удален.")

    return redirect(request.META.get('HTTP_REFERER', 'index'))