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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template import TemplateDoesNotExist
from django.utils.http import url_has_allowed_host_and_scheme
from django.template.loader import get_template
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_POST
from django.http import FileResponse
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError

from .forms import AddLessonForm, AddSubjectForm, ProfileUpdateForm, RegistrationForm, StudyGroupForm
from .models import (
    BotChatMessage, ChatMessage, ConnectionRequest, FileTag, FilesLibrary, Homework, HomeworkResponse,
    LessonAttendance, Lessons, Notification, PaymentReceipt, StudentTariff,
    StudyGroups, Subjects, Transaction, TutorStudentNote, TutorSubjects,
    UnlinkRequest, UserGroupColor, Users, StudentBalance, TestResult,
)
from .utils import notify_user, send_telegram_notification, send_verification_email
# from ratelimit.decorators import ratelimit  # установите django-ratelimit и пересоберите Docker-образ
from django.db.models import ProtectedError
from django.core.paginator import Paginator


def safe_referer_redirect(request, default='index'):
    """Редирект на HTTP_REFERER только если URL разрешён (защита от open redirect)."""
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts=settings.ALLOWED_HOSTS):
        return redirect(referer)
    return redirect(default)


def get_tutor_file_ids(tutor_profile, raw_ids):
    """Возвращает только те ID файлов, которые принадлежат репетитору (защита от привязки чужих файлов)."""
    if not raw_ids:
        return []
    clean = [fid.strip() for fid in raw_ids if fid and str(fid).isdigit()]
    if not clean:
        return []
    return list(FilesLibrary.objects.filter(tutor=tutor_profile, id__in=clean).values_list('id', flat=True))


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
    overdue_count = 0
    total_in_period = 0
    done_in_period = 0
    expected_income = 0
    student_groups = []
    student_tutors = []

    now = timezone.now()

    date_from_val = request.GET.get('date_from')
    date_to_val = request.GET.get('date_to')

    if not date_from_val and not date_to_val:
        final_start_date = (now - timedelta(days=2)).date()
        final_end_date = None
    else:

        final_start_date = date_from_val
        final_end_date = date_to_val

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

        if final_start_date:
            lessons_qs = lessons_qs.filter(start_time__date__gte=final_start_date)
        if final_end_date:
            lessons_qs = lessons_qs.filter(start_time__date__lte=final_end_date)

        if request.GET.get('subject'):
            lessons_qs = lessons_qs.filter(subject_id=request.GET['subject'])


        total_in_period = lessons_qs.count()
        now = timezone.now()
        done_in_period = LessonAttendance.objects.filter(
            lesson__in=lessons_qs,
            was_present=True
        ).values('lesson').distinct().count()
        expected_income = lessons_qs.filter(
            start_time__gt=now
        ).aggregate(
            Sum('price')
        )['price__sum'] or 0

        # Пагинация (первая порция данных)
        total_count = lessons_qs.count()
        lessons = lessons_qs[:per_page]

        # 3. Карта посещаемости (для быстрой отметки в JS) + JSON и счётчики для модалки
        for lesson in lessons:
            att_list = [
                {
                    "id": att.id,
                    "name": f"{att.student.first_name} {att.student.last_name}",
                    "present": att.was_present
                } for att in lesson.attendances.all()
            ]
            attendance_map[str(lesson.id)] = att_list
            setattr(lesson, 'attendances_json', json.dumps(att_list))
            setattr(lesson, 'att_present_count', sum(1 for a in att_list if a['present']))
            setattr(lesson, 'att_total_count', len(att_list))

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
        student_tutors = []
        student_groups = []

        confirmedconnections = ConnectionRequest.objects.filter(
            student=user_profile, status='confirmed'
        ).select_related('tutor')
        for conn in confirmedconnections:
            student_tutors.append(conn.tutor)
        student_groups = StudyGroups.objects.filter(students=user_profile)

        lessons_qs = Lessons.objects.filter(
            Q(student=user_profile) | Q(group__students=user_profile)
        ).distinct().prefetch_related('attendances__student', 'subject').order_by('start_time')

        subj_ids = lessons_qs.values_list('subject_id', flat=True).distinct()

        my_subjects = [{'subject': s} for s in Subjects.objects.filter(id__in=subj_ids)]

        target = request.GET.get('target')
        if target:
            if target.startswith('t'):  # t5 для репетитора
                lessons_qs = lessons_qs.filter(tutor_id=target[1:])
            elif target.startswith('g'):  # g3 для группы
                lessons_qs = lessons_qs.filter(group_id=target[1:])

        if final_start_date:
            lessons_qs = lessons_qs.filter(start_time__date__gte=final_start_date)
        if final_end_date:
            lessons_qs = lessons_qs.filter(start_time__date__lte=final_end_date)
        if request.GET.get('subject'):
            lessons_qs = lessons_qs.filter(subject_id=request.GET['subject'])


        total_count = lessons_qs.count()
        lessons = lessons_qs[:per_page]  # Теперь переменная lessons заполнена!
        for lesson in lessons:
            att_list = [
                {"id": att.id, "name": f"{att.student.first_name} {att.student.last_name}", "present": att.was_present}
                for att in lesson.attendances.all()
            ]
            setattr(lesson, 'attendances_json', json.dumps(att_list))
            setattr(lesson, 'att_present_count', sum(1 for a in att_list if a['present']))
            setattr(lesson, 'att_total_count', len(att_list))

        # 2. Доп. данные ученика
        student_debt = LessonAttendance.objects.filter(
            student=user_profile,
            was_present=True,
            is_paid=False
        ).aggregate(Sum('lesson__price'))['lesson__price__sum'] or 0



        homeworks = Homework.objects.filter(student=user_profile).order_by('deadline')
        active_hw = homeworks.filter(status__in=['pending', 'revision']).select_related('tutor')
        active_hw_count = active_hw.count()
        active_tutors = list(set([f"{hw.tutor.first_name} {hw.tutor.last_name}" for hw in active_hw]))
        overdue_count = homeworks.filter(deadline__lt=timezone.now()).exclude(status='completed').count()

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

    # Цветовая индикация: lesson_colors для расписания (без N+1)
    lesson_colors = {}
    if user_role == 'tutor' and lessons and hasattr(request.user, 'profile'):
        profile = request.user.profile
        group_ids = [l.group_id for l in lessons if getattr(l, 'group_id', None)]
        group_colors = dict(
            UserGroupColor.objects.filter(user=profile, group_id__in=group_ids)
            .exclude(color_hex__isnull=True).exclude(color_hex='')
            .values_list('group_id', 'color_hex')
        ) if group_ids else {}
        student_ids = [l.student_id for l in lessons if getattr(l, 'student_id', None)]
        connection_tutor_colors = dict(
            ConnectionRequest.objects.filter(
                tutor=profile, student_id__in=student_ids, status__in=['confirmed', 'archived']
            ).exclude(tutor_color_hex__isnull=True).exclude(tutor_color_hex='')
            .values_list('student_id', 'tutor_color_hex')
        ) if student_ids else {}
        for lesson in lessons:
            if getattr(lesson, 'group_id', None) and lesson.group_id in group_colors:
                lesson_colors[lesson.id] = group_colors[lesson.group_id]
            elif getattr(lesson, 'student_id', None):
                lesson_colors[lesson.id] = connection_tutor_colors.get(lesson.student_id)
            else:
                lesson_colors[lesson.id] = None
    elif user_role == 'student' and lessons and hasattr(request.user, 'profile'):
        profile = request.user.profile
        tutor_ids = list({l.tutor_id for l in lessons})
        group_ids = list({l.group_id for l in lessons if getattr(l, 'group_id', None)})
        tutor_colors = dict(
            ConnectionRequest.objects.filter(
                student=profile, status='confirmed', tutor_id__in=tutor_ids
            ).exclude(color_hex__isnull=True).exclude(color_hex='').values_list('tutor_id', 'color_hex')
        )
        group_colors = dict(
            UserGroupColor.objects.filter(user=profile, group_id__in=group_ids)
            .exclude(color_hex__isnull=True).exclude(color_hex='')
            .values_list('group_id', 'color_hex')
        ) if group_ids else {}
        for lesson in lessons:
            if getattr(lesson, 'group_id', None) and lesson.group_id in group_colors:
                lesson_colors[lesson.id] = group_colors[lesson.group_id]
            else:
                lesson_colors[lesson.id] = tutor_colors.get(lesson.tutor_id)

    for lesson in lessons:
        setattr(lesson, 'display_color', lesson_colors.get(lesson.id))

    context = {
        'lessons': lessons,
        'lesson_colors': lesson_colors,
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
        'dash_total_in_period': total_in_period,
        'dash_done_in_period': done_in_period,
        'dash_expected_income': float(expected_income),
        'current_date_from': final_start_date,
        'current_date_to': final_end_date,
        'student_tutors': student_tutors,
        'student_groups': student_groups,
        'overdue_count': overdue_count,
        'current_filter_target': request.GET.get('target'),
        'current_filter_subject': request.GET.get('subject'),
    }

    return smart_render(request, 'core/index.html', context)

# @ratelimit(key='ip', rate='5/m', block=True)
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
            from django.urls import reverse
            return redirect(reverse('index') + '?saved=1')
    else:
        form = ProfileUpdateForm(instance=profile)

    return smart_render(request, 'core/edit_profile.html', {'form': form})

# @ratelimit(key='ip', rate='5/m', block=True)
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
    student_name = f"{conn_request.student.first_name} {conn_request.student.last_name}".strip() or conn_request.student.user.username
    notify_user(
        conn_request.tutor.user,
        f"Ученик {student_name} принял вашу заявку",
        link=reverse('student_card', args=[conn_request.student.id]),
        notification_type='info',
    )
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
    student_name = f"{conn_request.student.first_name} {conn_request.student.last_name}".strip() or conn_request.student.user.username
    tutor_user = conn_request.tutor.user
    conn_request.delete()
    notify_user(
        tutor_user,
        f"Ученик {student_name} отклонил заявку",
        link=reverse('my_students'),
        notification_type='warning',
    )
    return redirect('confirmations')


@login_required
def my_students(request):
    user_profile = request.user.profile

    if request.method == 'POST' and 'save_tariff' in request.POST:
        StudentTariff.objects.update_or_create(
            tutor=user_profile,
            student_id=request.POST.get('t_student') or None,
            group_id=request.POST.get('t_group') or None,
            subject_id=request.POST.get('t_subject'),
            defaults={'price': request.POST.get('t_price')}
        )
        messages.success(request, 'Тариф сохранён.')
        return redirect('my_students')

    # Твои активные связи
    connections = ConnectionRequest.objects.filter(tutor=user_profile, status='confirmed').select_related('student')
    groups = StudyGroups.objects.filter(tutor=user_profile).select_related('subject').prefetch_related('students')
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
    pending_unlink_tutor_ids = set()
    if request.user.profile.role == 'student':
        pending_unlink_tutor_ids = set(
            UnlinkRequest.objects.filter(
                student=request.user.profile,
                status='pending',
            ).values_list('tutor_id', flat=True)
        )
    return smart_render(request, 'core/my_tutors.html', {
        'connections': confirmed_connections,
        'pending_unlink_tutor_ids': pending_unlink_tutor_ids,
    })


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
            messages.error(request, "Пользователь не найден или уже добавлен.")

    return smart_render(request, 'core/add_student.html')


@login_required
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
                return smart_render(request, 'core/add_lesson.html', {'form': form})

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
                return redirect(reverse('index') + '?saved=1')
    else:
        form = AddLessonForm(instance=lesson, tutor=request.user.profile)

    return smart_render(request, 'core/edit_lesson.html', {'form': form, 'lesson': lesson})


@login_required
@require_POST
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lessons, id=lesson_id, tutor=request.user.profile)

    if request.method == 'POST':
        now = timezone.now()
        is_past = lesson.start_time < now


        critical_attendance = LessonAttendance.objects.filter(
            Q(lesson=lesson) & (Q(was_present=True) | Q(is_paid=True))
        ).exists()

        if is_past and critical_attendance:
            messages.error(
                request,
                "Критическая ошибка: Нельзя удалить прошедший урок с подтвержденной явкой или оплатой."
            )
            return redirect('index')

        # Если урок старый, но на нем только прогулы и нет оплат — он удалится
        lesson.delete()
        messages.success(request, "Урок успешно удален.")

    return redirect('index')

@login_required
#@ratelimit(key='ip', rate='5/m', block=True)
def edit_group(request, group_id):
    profile = request.user.profile
    group = get_object_or_404(StudyGroups, id=group_id, tutor=profile)

    if request.method == 'POST':
        form = StudyGroupForm(request.POST, instance=group, tutor=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Группа '{group.name}' обновлена!")
            from django.urls import reverse
            return redirect(reverse('my_students') + '?saved=1')
    else:
        form = StudyGroupForm(instance=group, tutor=profile)

    group_color_obj = UserGroupColor.objects.filter(user=profile, group=group).first()
    group_color_hex = group_color_obj.color_hex if group_color_obj else None

    return smart_render(request, 'core/edit_group.html', {
        'form': form, 'group': group, 'group_color_hex': group_color_hex,
    })


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
def add_group(request):
    if request.method == 'POST':
        form = StudyGroupForm(request.POST, tutor=request.user.profile)
        if form.is_valid():
            new_group = form.save(commit=False)
            new_group.tutor = request.user.profile
            new_group.save()
            form.save_m2m()
            messages.success(request, f"Группа '{new_group.name}' успешно создана!")
            return redirect(reverse('my_students') + '?saved=1')
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
            now = timezone.now()

            # Находим те уроки, которые УЖЕ прошли И имеют посещаемость
            protected_ids = queryset.filter(
                start_time__lt=now,
                attendances__was_present=True
            ).values_list('id', flat=True).distinct() | queryset.filter(
                start_time__lt=now,
                attendances__is_paid=True
            ).values_list('id', flat=True).distinct()

            # 2. Разделяем выборку на те, что можно удалить, и те, что нельзя
            lessons_to_delete = queryset.exclude(id__in=protected_ids)
            protected_count = len(protected_ids)
            deleted_count = lessons_to_delete.count()

            # 3. Выполняем удаление разрешенных уроков
            lessons_to_delete.delete()

            # 4. Формируем уведомление для пользователя
            if protected_count > 0:
                messages.warning(
                    request,
                    f"Удалено занятий: {deleted_count}. Защищено от удаления: {protected_count} (прошедшие уроки с явкой или оплатой)."
                )
            else:
                messages.success(request, f"Успешно удалено занятий: {deleted_count}")


        elif action == 'mass_edit':
            new_date = request.POST.get('mass_date')
            new_time = request.POST.get('mass_time')
            new_student = request.POST.get('mass_student', '').strip()
            new_group = request.POST.get('mass_group', '').strip()
            new_subject = request.POST.get('mass_subject')
            new_duration = request.POST.get('mass_duration')
            new_price = request.POST.get('mass_price')
            new_format = request.POST.get('mass_format')
            new_location = request.POST.get('mass_location')
            new_notes = request.POST.get('notes')
            selected_materials = request.POST.getlist('materials')
            tutor_profile = request.user.profile

            # Проверка доступа: студент — только из своих подключений, группа — своя
            if new_student and not ConnectionRequest.objects.filter(
                tutor=tutor_profile, student_id=new_student, status__in=['confirmed', 'archived']
            ).exists():
                new_student = None
            if new_group and not StudyGroups.objects.filter(id=new_group, tutor=tutor_profile).exists():
                new_group = None

            valid_material_ids = get_tutor_file_ids(tutor_profile, selected_materials) if selected_materials else []

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
                    if new_format:
                        lesson.format = new_format
                    if new_location:
                        lesson.location = new_location
                    if new_notes:
                        lesson.notes = new_notes

                    lesson.save()

                    if 'materials_updated' in request.POST:
                        lesson.materials.set(valid_material_ids)

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

    # связь репетитор–ученик (для формы «Цветовая метка»)
    connection = ConnectionRequest.objects.filter(
        tutor=tutor, student=student, status__in=['confirmed', 'archived']
    ).first()

    # группы этого репетитора, в которых состоит ученик
    student_groups = StudyGroups.objects.filter(tutor=tutor, students=student).order_by('name')

    # Аналитика: раздельно ДЗ (hw) и проверочные/контрольные (test)
    performance_all = student.performance.filter(lesson__tutor=tutor).select_related('lesson', 'lesson__subject').order_by('-date')
    performance_hw = list(performance_all.filter(type='hw')[:15])
    performance_tests = list(performance_all.filter(type='test')[:15])
    avg_score_hw = None
    avg_score_tests = None
    if performance_hw:
        scores = [p.score for p in performance_hw]
        avg_score_hw = round(sum(scores) / len(scores), 1)
    if performance_tests:
        scores = [p.score for p in performance_tests]
        avg_score_tests = round(sum(scores) / len(scores), 1)

    context = {
        'student': student,
        'attendances': attendances,
        'total_debt': total_debt,
        'homeworks': homeworks,
        'tutor_files': tutor_files,
        'subjects': subjects,
        'transactions': student.transactions.filter(tutor=tutor).order_by('-date'),
        'performance_hw': performance_hw,
        'performance_tests': performance_tests,
        'avg_score_hw': avg_score_hw,
        'avg_score_tests': avg_score_tests,
        'tutor_note': note_obj.text,
        'balance': balance_obj.balance,
        'connection': connection,
        'student_groups': student_groups,
    }

    return smart_render(request, 'core/student_card.html', context)


@login_required
@require_POST
def delete_transaction(request, transaction_id):
    """Удаление транзакции с корректировкой баланса (и снятием отметки об оплате, если это списание за урок)."""
    tutor = request.user.profile
    tx = get_object_or_404(Transaction, id=transaction_id, tutor=tutor)
    student = tx.student

    with transaction.atomic():
        balance_obj, _ = StudentBalance.objects.select_for_update().get_or_create(
            tutor=tutor,
            student=student,
        )
        if tx.type == 'deposit':
            balance_obj.balance -= tx.amount
        else:
            balance_obj.balance += tx.amount
            if tx.attendance_id:
                att = LessonAttendance.objects.filter(id=tx.attendance_id).first()
                if att:
                    att.is_paid = False
                    att.save(update_fields=['is_paid'])
        balance_obj.save()
        tx.delete()

    messages.success(request, "Транзакция удалена, баланс обновлён.")
    return redirect('student_card', student_id=student.id)


@login_required
#@ratelimit(key='ip', rate='5/m', block=True)
def add_homework(request, student_id):
    if request.method == 'POST':
        tutor = request.user.profile
        student = get_object_or_404(Users, id=student_id)

        has_access = ConnectionRequest.objects.filter(
            tutor=tutor,
            student=student,
            status__in=['confirmed', 'archived']
        ).exists()
        if not has_access:
            messages.error(request, "Ошибка доступа: это не ваш ученик.")
            return redirect('my_students')

        subject_id = request.POST.get('subject')
        subject_obj = get_object_or_404(Subjects, id=subject_id, tutor=tutor)

        deadline_raw = request.POST.get('deadline')
        description = request.POST.get('description')

        hw = Homework.objects.create(
            tutor=tutor,
            student=student,
            subject=subject_obj,
            description=description,
            deadline=deadline_raw or None
        )

        notify_user(
            student.user,
            f"Новое ДЗ по {subject_obj.name}",
            link=reverse('homework_detail', args=[hw.id]),
            notification_type='info',
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

        file_ids = get_tutor_file_ids(tutor, request.POST.getlist('files'))
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

    # --- ОБРАБОТКА ЗАГРУЗКИ ---
    if request.method == 'POST':
        file_name = (request.POST.get('file_name') or '').strip()
        uploaded = request.FILES.get('file')
        if not file_name:
            messages.error(request, 'Укажите название файла.')
            return redirect('files_library')
        if not uploaded:
            messages.error(request, 'Выберите файл для загрузки.')
            return redirect('files_library')
        if uploaded.size > MAX_SIZE:
            messages.error(request, 'Максимальный размер файла — 10 МБ.')
            return redirect('files_library')
        try:
            file_obj = FilesLibrary.objects.create(
                tutor=user_profile,
                file_name=file_name[:30],
                file=uploaded,
            )
            tag_ids = request.POST.getlist('tags')
            if tag_ids:
                valid_ids = list(FileTag.objects.filter(tutor=user_profile, id__in=tag_ids).values_list('id', flat=True))
                file_obj.tags.set(valid_ids)
            new_tag_name = (request.POST.get('new_tag_name') or '').strip()
            if new_tag_name:
                tag, _ = FileTag.objects.get_or_create(tutor=user_profile, name=new_tag_name[:50])
                file_obj.tags.add(tag)
            messages.success(request, 'Файл успешно загружен.')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('files_library')

    # --- ЛОГИКА ПОИСКА, ФИЛЬТРА ПО ТЕГАМ И СОРТИРОВКИ ---
    query = request.GET.get('q', '')
    tag_ids = request.GET.getlist('tag')
    sort_param = request.GET.get('sort', 'date-desc')
    order_map = {
        'name-asc': ['file_name'],
        'name-desc': ['-file_name'],
        'date-desc': ['-upload_date'],
        'date-asc': ['upload_date'],
    }
    order = order_map.get(sort_param, ['-upload_date'])
    files_qs = FilesLibrary.objects.filter(tutor=user_profile).prefetch_related('tags').order_by(*order)

    if query:
        files_qs = files_qs.filter(file_name__icontains=query)
    if tag_ids:
        files_qs = files_qs.filter(tags__id__in=tag_ids).distinct()

    tutor_tags = FileTag.objects.filter(tutor=user_profile).order_by('name')

    files = files_qs[:20]
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('core/files_rows.html', {'files': files}, request=request)
        return JsonResponse({'html': html, 'has_more': files_qs.count() > 20})

    return smart_render(request, 'core/files_library.html', {
        'files': files,
        'query': query,
        'tutor_tags': tutor_tags,
        'selected_tag_ids': [int(x) for x in tag_ids if x.isdigit()],
        'sort_param': sort_param,
    })


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

        tag_ids = request.POST.getlist('tags')
        valid_tag_ids = list(FileTag.objects.filter(tutor=request.user.profile, id__in=tag_ids).values_list('id', flat=True))
        file_obj.tags.set(valid_tag_ids)

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
@require_POST
def rename_tag(request, tag_id):
    tag = get_object_or_404(FileTag, id=tag_id, tutor=request.user.profile)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = {}
    new_name = (data.get('name') or '').strip()[:50]
    if not new_name:
        return JsonResponse({'error': 'Имя не может быть пустым'}, status=400)
    if FileTag.objects.filter(tutor=request.user.profile, name=new_name).exclude(id=tag.id).exists():
        return JsonResponse({'error': 'Тег с таким именем уже существует'}, status=400)
    tag.name = new_name
    tag.save()
    return JsonResponse({'success': True, 'id': tag.id, 'name': tag.name})


@login_required
@require_POST
def delete_tag(request, tag_id):
    tag = get_object_or_404(FileTag, id=tag_id, tutor=request.user.profile)
    tag.delete()
    return JsonResponse({'success': True})


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
        return safe_referer_redirect(request, 'index')

    files = lesson.materials.all()
    if not files:
        messages.warning(request, "К этому уроку не прикреплено ни одного файла.")
        return safe_referer_redirect(request, 'index')

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
        return safe_referer_redirect(request, 'index')

    files = hw.files.all()
    if not files:
        messages.warning(request, "Файлов для скачивания нет")
        return safe_referer_redirect(request, 'index')

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
        return safe_referer_redirect(request, 'index')

    if not response_obj.file or not os.path.exists(response_obj.file.path):
        messages.error(request, "Файл не найден.")
        return safe_referer_redirect(request, 'index')

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

        file_ids = get_tutor_file_ids(request.user.profile, request.POST.getlist('files'))
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
def results_page(request):
    """Аналитика / Результаты: репетитор — фильтры по ученику/предмету; ученик — только свои результаты. Безопасность: QuerySet всегда по request.user."""
    user_profile = request.user.profile

    # ——— Ученик: только свои результаты, без доступа к чужим ———
    if user_profile.role == 'student':
        qs = TestResult.objects.filter(student=user_profile).select_related('tutor', 'subject').order_by('-date')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        subject_id_param = request.GET.get('subject_id')
        subject_id_filter = int(subject_id_param) if subject_id_param and subject_id_param.isdigit() else None
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if subject_id_filter:
            qs = qs.filter(subject_id=subject_id_filter)
        # Используем корректный related_name из модели TestResult.subject
        subjects_list = Subjects.objects.filter(test_results__student=user_profile).distinct().order_by('name')
        from collections import defaultdict
        by_date = defaultdict(list)
        for r in qs:
            pct = r.percent
            if pct is not None:
                by_date[r.date].append(pct)
        dates_sorted = sorted(by_date.keys())
        chart_labels = [d.strftime('%d.%m') for d in dates_sorted]
        chart_values = [round(sum(by_date[d]) / len(by_date[d]), 1) for d in dates_sorted]
        context = {
            'results': qs,
            'subjects_list': subjects_list,
            'students_list': [],
            'date_from': date_from,
            'date_to': date_to,
            'subject_id': subject_id_param,
            'subject_id_filter': subject_id_filter,
            'chart_labels': json.dumps(chart_labels),
            'chart_values': json.dumps(chart_values),
            'is_student_view': True,
        }
        return smart_render(request, 'core/results.html', context)

    # ——— Репетитор ———
    tutor = user_profile

    # POST — добавление результата
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        max_score = request.POST.get('max_score')
        score = request.POST.get('score')
        date_str = request.POST.get('result_date')
        comment = (request.POST.get('comment') or '').strip() or None
        try:
            max_score = Decimal(max_score or '0')
            score = Decimal(score or '0')
        except Exception:
            messages.error(request, 'Сумма и балл должны быть числами.')
            return redirect('results_page')
        if max_score <= 0:
            messages.error(request, 'Максимальный балл должен быть больше 0.')
            return redirect('results_page')
        if score < 0 or score > max_score:
            messages.error(request, 'Полученный балл должен быть от 0 до максимального балла.')
            return redirect('results_page')
        if not date_str:
            messages.error(request, 'Укажите дату.')
            return redirect('results_page')
        try:
            result_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Некорректная дата.')
            return redirect('results_page')
        if result_date > timezone.now().date():
            messages.error(request, 'Дата не может быть в будущем.')
            return redirect('results_page')
        student = get_object_or_404(Users, id=student_id, role='student')
        subject = get_object_or_404(Subjects, id=subject_id)
        if not TutorSubjects.objects.filter(tutor=tutor, subject=subject).exists():
            messages.error(request, 'Этот предмет не принадлежит вам.')
            return redirect('results_page')
        if not ConnectionRequest.objects.filter(tutor=tutor, student=student, status__in=['confirmed', 'archived']).exists():
            messages.error(request, 'Ученик не привязан к вам.')
            return redirect('results_page')
        TestResult.objects.create(tutor=tutor, student=student, subject=subject, max_score=max_score, score=score, date=result_date, comment=comment)
        messages.success(request, 'Результат добавлен.')
        return redirect('results_page')

    # GET — список и фильтры (всегда по tutor=request.user, student_id только из своих учеников)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    subject_id_param = request.GET.get('subject_id')
    subject_id_filter = int(subject_id_param) if subject_id_param and subject_id_param.isdigit() else None
    student_id_param = request.GET.get('student_id')
    confirmed_ids = list(ConnectionRequest.objects.filter(tutor=tutor, status__in=['confirmed', 'archived']).values_list('student_id', flat=True))
    student_id_filter = None
    if student_id_param and student_id_param.isdigit():
        sid = int(student_id_param)
        if sid in confirmed_ids:
            student_id_filter = sid

    qs = TestResult.objects.filter(tutor=tutor).select_related('student', 'subject').order_by('-date')
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    if subject_id_filter:
        qs = qs.filter(subject_id=subject_id_filter)
    if student_id_filter is not None:
        qs = qs.filter(student_id=student_id_filter)

    subjects_list = Subjects.objects.filter(tutorsubjects__tutor=tutor).order_by('name')
    students_list = Users.objects.filter(id__in=confirmed_ids, role='student').order_by('last_name', 'first_name')

    from collections import defaultdict
    by_date = defaultdict(list)
    for r in qs:
        pct = r.percent
        if pct is not None:
            by_date[r.date].append(pct)
    dates_sorted = sorted(by_date.keys())
    chart_labels = [d.strftime('%d.%m') for d in dates_sorted]
    chart_values = [round(sum(by_date[d]) / len(by_date[d]), 1) for d in dates_sorted]

    context = {
        'results': qs,
        'subjects_list': subjects_list,
        'students_list': students_list,
        'date_from': date_from,
        'date_to': date_to,
        'subject_id': subject_id_param,
        'subject_id_filter': subject_id_filter,
        'student_id_filter': student_id_filter,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'is_student_view': False,
    }
    return smart_render(request, 'core/results.html', context)


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

            student_name = f"{user_profile.first_name} {user_profile.last_name}".strip() or user_profile.user.username
            notify_user(
                tutor.user,
                f"{student_name} сдал(а) ДЗ по {homework.subject.name} на проверку",
                link=reverse('homework_detail', args=[homework.id]),
                notification_type='info',
            )

            if added_new:
                messages.success(request, "Задание успешно отправлено!")
            else:
                messages.info(request,
                              "Эти файлы уже были прикреплены ранее. Статус задания обновлен на «На проверке».")
        else:
            messages.error(request, "Файлы не были выбраны.")

        # Возвращаем пользователя на ту страницу, с которой он отправлял форму
        return safe_referer_redirect(request, 'my_assignments')


@login_required
def my_assignments(request):
    profile = request.user.profile

    if profile.role != 'student':
        return redirect('index')

    now = timezone.now()
    homeworks = list(Homework.objects.filter(student=profile).select_related('tutor', 'subject').order_by('-deadline'))
    tutor_ids = list({hw.tutor_id for hw in homeworks})
    tutor_colors = dict(
        ConnectionRequest.objects.filter(
            student=profile, status='confirmed', tutor_id__in=tutor_ids
        ).exclude(color_hex__isnull=True).exclude(color_hex='').values_list('tutor_id', 'color_hex')
    ) if tutor_ids else {}
    overdue_count = 0
    for hw in homeworks:
        setattr(hw, 'display_color', tutor_colors.get(hw.tutor_id))
        is_overdue = hw.deadline and hw.deadline < now and hw.status != 'completed'
        setattr(hw, 'is_overdue', is_overdue)
        if is_overdue:
            overdue_count += 1

    context = {
        'homeworks': homeworks,
        'profile': profile,
        'tutor_colors': tutor_colors,
        'overdue_count': overdue_count,
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
    profile = request.user.profile
    group = get_object_or_404(StudyGroups, id=group_id)
    is_tutor_owner = group.tutor == profile
    is_student_member = not is_tutor_owner and group.students.filter(id=profile.id).exists()
    if not (is_tutor_owner or is_student_member):
        return redirect('index')

    if request.method == 'POST' and 'assign_group_homework' in request.POST and is_tutor_owner:
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        file_ids = get_tutor_file_ids(profile, request.POST.getlist('files'))

        for student in group.students.all():
            hw = Homework.objects.create(
                tutor=profile,
                student=student,
                subject=group.subject,
                description=description,
                deadline=deadline if deadline else None
            )
            if file_ids:
                hw.files.set(file_ids)
            notify_user(
                student.user,
                f"Новое ДЗ по {group.subject.name}",
                link=reverse('homework_detail', args=[hw.id]),
                notification_type='info',
            )

        messages.success(request, "Задание отправлено всей группе")
        return redirect('group_card', group_id=group.id)

    attendances = LessonAttendance.objects.filter(
        lesson__group=group,
        lesson__tutor=group.tutor
    ).select_related('lesson', 'lesson__subject', 'student').order_by('-lesson__start_time')

    tutor_files = FilesLibrary.objects.filter(tutor=group.tutor).order_by('-upload_date') if is_tutor_owner else []

    # Текущий цвет группы для этого пользователя (репетитор или ученик)
    group_color_obj = UserGroupColor.objects.filter(user=profile, group=group).first()
    group_color_hex = group_color_obj.color_hex if group_color_obj else None

    context = {
        'group': group,
        'attendances': attendances,
        'members': group.students.all(),
        'tutor_files': tutor_files,
        'is_tutor_owner': is_tutor_owner,
        'group_color_hex': group_color_hex,
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

    # Применяем фильтры (те же, что в index). Порядок — как в index (по возрастанию даты)
    lessons_qs = lessons_qs.prefetch_related(
        'attendances__student', 'subject', 'materials', 'group__students'
    ).order_by('start_time')

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
    for lesson in lessons:
        att_list = [
            {"id": att.id, "name": f"{att.student.first_name} {att.student.last_name}", "present": att.was_present}
            for att in lesson.attendances.all()
        ]
        setattr(lesson, 'attendances_json', json.dumps(att_list))
        setattr(lesson, 'att_present_count', sum(1 for a in att_list if a['present']))
        setattr(lesson, 'att_total_count', len(att_list))

    # Цветовая индикация для среза уроков (без N+1)
    lesson_colors = {}
    if role == 'tutor' and lessons:
        group_ids = [l.group_id for l in lessons if getattr(l, 'group_id', None)]
        group_colors = dict(
            UserGroupColor.objects.filter(user=user_profile, group_id__in=group_ids)
            .exclude(color_hex__isnull=True).exclude(color_hex='')
            .values_list('group_id', 'color_hex')
        ) if group_ids else {}
        student_ids = [l.student_id for l in lessons if getattr(l, 'student_id', None)]
        connection_tutor_colors = dict(
            ConnectionRequest.objects.filter(
                tutor=user_profile, student_id__in=student_ids, status__in=['confirmed', 'archived']
            ).exclude(tutor_color_hex__isnull=True).exclude(tutor_color_hex='')
            .values_list('student_id', 'tutor_color_hex')
        ) if student_ids else {}
        for lesson in lessons:
            if getattr(lesson, 'group_id', None) and lesson.group_id in group_colors:
                lesson_colors[lesson.id] = group_colors[lesson.group_id]
            elif getattr(lesson, 'student_id', None):
                lesson_colors[lesson.id] = connection_tutor_colors.get(lesson.student_id)
            else:
                lesson_colors[lesson.id] = None
    elif role == 'student' and lessons:
        tutor_ids = list({l.tutor_id for l in lessons})
        group_ids = list({l.group_id for l in lessons if getattr(l, 'group_id', None)})
        tutor_colors = dict(
            ConnectionRequest.objects.filter(
                student=user_profile, status='confirmed', tutor_id__in=tutor_ids
            ).exclude(color_hex__isnull=True).exclude(color_hex='').values_list('tutor_id', 'color_hex')
        )
        group_colors = dict(
            UserGroupColor.objects.filter(user=user_profile, group_id__in=group_ids)
            .exclude(color_hex__isnull=True).exclude(color_hex='')
            .values_list('group_id', 'color_hex')
        ) if group_ids else {}
        for lesson in lessons:
            if getattr(lesson, 'group_id', None) and lesson.group_id in group_colors:
                lesson_colors[lesson.id] = group_colors[lesson.group_id]
            else:
                lesson_colors[lesson.id] = tutor_colors.get(lesson.tutor_id)

    for lesson in lessons:
        setattr(lesson, 'display_color', lesson_colors.get(lesson.id))

    # Рендерим строки: для мобильного — карточки, для десктопа — строки таблицы
    rows_template = (
        'mobile/lessons_rows.html' if getattr(request, 'is_mobile', False)
        else 'core/lessons_rows.html'
    )
    html = render_to_string(rows_template, {
        'lessons': lessons,
        'lesson_colors': lesson_colors,
        'role': role,
        'now': timezone.now(),
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

    # Связь ученик–репетитор для формы цвета (только для ученика)
    connection = None
    has_pending_unlink = False
    if student_profile.role == 'student':
        connection = ConnectionRequest.objects.filter(
            student=student_profile, tutor=tutor, status='confirmed'
        ).first()
        if connection:
            has_pending_unlink = UnlinkRequest.objects.filter(
                student=student_profile, tutor=tutor, status='pending'
            ).exists()

    context = {
        'tutor': tutor,
        'student': student_profile,
        'connection': connection,
        'has_pending_unlink': has_pending_unlink,
        'attendances': attendances,
        'homeworks': homeworks,
        'transactions': transactions,
        'balance': balance_obj.balance,
        'total_debt': total_debt,
    }
    return smart_render(request, 'core/tutor_card.html', context)


@login_required
@require_POST
def update_tutor_color(request, connection_id):
    """Обновление цвета репетитора (только для ученика, владеющего связью)."""
    connection = get_object_or_404(ConnectionRequest, id=connection_id)
    if connection.student != request.user.profile:
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
    color_hex = (request.POST.get('color_hex') or '').strip() or None
    if color_hex and len(color_hex) > 7:
        color_hex = color_hex[:7]
    connection.color_hex = color_hex
    connection.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'color_hex': color_hex})
    return safe_referer_redirect(request, 'my_tutors')


@login_required
@require_POST
def update_connection_tutor_color(request, connection_id):
    """Обновление цвета связи для репетитора (только репетитор — владелец связи)."""
    connection = get_object_or_404(ConnectionRequest, id=connection_id)
    if connection.tutor != request.user.profile:
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
    color_hex = (request.POST.get('color_hex') or '').strip() or None
    if color_hex and len(color_hex) > 7:
        color_hex = color_hex[:7]
    connection.tutor_color_hex = color_hex
    connection.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'color_hex': color_hex})
    return redirect('student_card', student_id=connection.student_id)


@login_required
@require_POST
def update_group_color(request, group_id):
    """Обновление цвета группы (репетитор — владелец, ученик — участник)."""
    group = get_object_or_404(StudyGroups, id=group_id)
    profile = request.user.profile
    if profile.role == 'tutor':
        if group.tutor != profile:
            return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
    else:
        if not group.students.filter(id=profile.id).exists():
            return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
    color_hex = (request.POST.get('color_hex') or '').strip() or None
    if color_hex and len(color_hex) > 7:
        color_hex = color_hex[:7]
    obj, _ = UserGroupColor.objects.get_or_create(user=profile, group=group, defaults={'color_hex': color_hex})
    obj.color_hex = color_hex
    obj.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'color_hex': color_hex})
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts=settings.ALLOWED_HOSTS):
        return redirect(referer)
    return redirect('group_card', group_id=group_id)


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

    archived_connection = ConnectionRequest.objects.filter(
        tutor=tutor,
        student=student,
        status='archived'
    ).first()
    if not archived_connection:
        messages.error(request, "Ошибка доступа: этого ученика нельзя восстановить.")
        return redirect('archived_students')

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


# --- Chat (репетитор ↔ ученик) ---


@login_required
def bot_chat(request):
    """Чат с AI-ботом (GigaChat)."""
    if request.method == 'POST':
        text = (request.POST.get('text') or '').strip()
        if text:
            # Сохраняем сообщение пользователя
            BotChatMessage.objects.create(
                user=request.user,
                role='user',
                content=text[:8000],
            )
            # Собираем историю для контекста (последние 20 пар)
            # QuerySet не поддерживает [-21:], поэтому сначала list, потом срез
            all_history = list(
                BotChatMessage.objects.filter(user=request.user)
                .order_by('created_at')
                .values_list('role', 'content')
            )
            history = all_history[-21:]
            api_messages = [{"role": r, "content": c} for r, c in history]
            # Запрос к GigaChat
            from core.services.gigachat import get_giga_response
            reply = get_giga_response(api_messages)
            # Сохраняем ответ бота
            BotChatMessage.objects.create(
                user=request.user,
                role='assistant',
                content=reply[:16000],
            )
            return redirect('bot_chat')

    bot_messages = BotChatMessage.objects.filter(user=request.user).order_by('created_at')
    context = {
        'bot_messages': bot_messages,
    }
    return smart_render(request, 'core/bot_chat.html', context)


@login_required
def chat_list(request):
    """Список диалогов: для репетитора — с учениками, для ученика — с репетиторами."""
    profile = request.user.profile
    if profile.role == 'tutor':
        connections = list(ConnectionRequest.objects.filter(
            tutor=profile, status__in=['confirmed', 'archived']
        ).select_related('student').order_by('-created_at'))
    else:
        connections = list(ConnectionRequest.objects.filter(
            student=profile, status__in=['confirmed', 'archived']
        ).select_related('tutor').order_by('-created_at'))

    conn_ids = [c.id for c in connections]
    last_msgs = {}
    for msg in ChatMessage.objects.filter(connection_id__in=conn_ids).order_by('connection_id', '-created_at'):
        if msg.connection_id not in last_msgs:
            last_msgs[msg.connection_id] = msg

    # Непрочитанные: сообщения от counterpart, которые я ещё не прочитал
    unread_counts = {}
    for row in ChatMessage.objects.filter(
        connection_id__in=conn_ids, is_read=False
    ).exclude(sender=profile).values('connection_id').annotate(cnt=Count('id')):
        unread_counts[row['connection_id']] = row['cnt']

    # Прикрепляем last_message и unread_count к каждому connection
    for conn in connections:
        conn.last_message = last_msgs.get(conn.id)
        conn.unread_count = unread_counts.get(conn.id, 0)

    context = {
        'connections': connections,
        'is_tutor': profile.role == 'tutor',
    }
    return smart_render(request, 'core/chat_list.html', context)


@login_required
def chat_thread(request, connection_id):
    """Чат с конкретным пользователем (по connection_id)."""
    profile = request.user.profile
    connection = get_object_or_404(
        ConnectionRequest.objects.select_related('tutor', 'student'),
        id=connection_id,
        status__in=['confirmed', 'archived']
    )
    # Проверка: текущий пользователь — участник диалога
    if profile.role == 'tutor':
        if connection.tutor_id != profile.id:
            messages.error(request, "Нет доступа к этому диалогу.")
            return redirect('chat_list')
        counterpart = connection.student
    else:
        if connection.student_id != profile.id:
            messages.error(request, "Нет доступа к этому диалогу.")
            return redirect('chat_list')
        counterpart = connection.tutor

    if request.method == 'POST':
        text = (request.POST.get('text') or '').strip()
        uploaded_file = request.FILES.get('file')
        if text or uploaded_file:
            try:
                msg = ChatMessage(
                    connection=connection,
                    sender=profile,
                    text=text[:5000] if text else '',
                )
                if uploaded_file:
                    from core.validators import validate_chat_file
                    validate_chat_file(uploaded_file)
                    msg.file = uploaded_file
                    msg.file_name = uploaded_file.name[:255]
                msg.save()
            except ValidationError as e:
                messages.error(request, str(e))
            else:
                return redirect('chat_thread', connection_id=connection.id)
        else:
            messages.error(request, "Введите текст или прикрепите файл.")

    # Пометить входящие сообщения как прочитанные при открытии чата
    ChatMessage.objects.filter(
        connection=connection,
        sender=counterpart,
        is_read=False,
    ).update(is_read=True)

    chat_messages = ChatMessage.objects.filter(connection=connection).select_related('sender').order_by('created_at')

    context = {
        'connection': connection,
        'counterpart': counterpart,
        'chat_messages': chat_messages,
        'is_tutor': profile.role == 'tutor',
    }
    return smart_render(request, 'core/chat_thread.html', context)


@login_required
def download_chat_file(request, message_id):
    """Скачать/просмотреть файл из чата (только участники диалога)."""
    msg = get_object_or_404(
        ChatMessage.objects.select_related('connection'),
        id=message_id,
        file__isnull=False,
    )
    conn = msg.connection
    profile = request.user.profile
    if conn.tutor_id != profile.id and conn.student_id != profile.id:
        messages.error(request, "Нет доступа к этому файлу.")
        return redirect('chat_list')
    if not msg.file or not os.path.exists(msg.file.path):
        messages.error(request, "Файл не найден.")
        return redirect('chat_thread', connection_id=conn.id)
    filename = msg.file_name or os.path.basename(msg.file.name)
    ext = filename.lower().split('.')[-1] if filename else ''
    content_types = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp',
    }
    content_type = content_types.get(ext, 'application/octet-stream')
    as_attachment = ext not in content_types
    response = FileResponse(
        open(msg.file.path, 'rb'),
        as_attachment=as_attachment,
        filename=filename,
        content_type=content_type,
    )
    return response


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
    query = request.GET.get('q', '')
    tag_ids = request.GET.getlist('tag')
    sort_param = request.GET.get('sort', 'date-desc')
    order_map = {
        'name-asc': ['file_name'],
        'name-desc': ['-file_name'],
        'date-desc': ['-upload_date'],
        'date-asc': ['upload_date'],
    }
    order = order_map.get(sort_param, ['-upload_date'])
    files_qs = FilesLibrary.objects.filter(tutor=user_profile).prefetch_related('tags').order_by(*order)
    if query:
        files_qs = files_qs.filter(file_name__icontains=query)
    if tag_ids:
        files_qs = files_qs.filter(tags__id__in=tag_ids).distinct()

    start = (page - 1) * per_page
    end = page * per_page
    files = list(files_qs[start:end])

    rows_template = 'mobile/files_rows.html' if getattr(request, 'is_mobile', False) else 'core/files_rows.html'
    html = render_to_string(rows_template, {'files': files}, request=request)
    has_more = files_qs.count() > end
    return JsonResponse({'html': html, 'has_more': has_more})


@login_required
def download_library_file(request, file_id):
    # Ищем файл и проверяем, что он принадлежит этому репетитору
    file_obj = get_object_or_404(FilesLibrary, id=file_id, tutor=request.user.profile)

    if not file_obj.file or not os.path.exists(file_obj.file.path):
        messages.error(request, "Файл не найден на сервере.")
        return safe_referer_redirect(request, 'files_library')

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
def payment_receipts(request):
    """Страница оплат: ученик — форма отправки чека и список своих чеков; репетитор — заявки на подтверждение."""
    user_profile = request.user.profile
    if user_profile.role == 'student':
        confirmed_tutor_ids = ConnectionRequest.objects.filter(
            student=user_profile, status='confirmed'
        ).values_list('tutor_id', flat=True)
        my_tutors = Users.objects.filter(id__in=confirmed_tutor_ids)
        my_receipts = PaymentReceipt.objects.filter(student=user_profile).select_related('tutor').order_by('-created_at')
        return smart_render(request, 'core/payment_receipts_student.html', {
            'my_tutors': my_tutors,
            'my_receipts': my_receipts,
        })
    else:
        pending_receipts = PaymentReceipt.objects.filter(
            tutor=user_profile, status='pending'
        ).select_related('student').order_by('-created_at')
        return smart_render(request, 'core/payment_receipts_tutor.html', {
            'pending_receipts': pending_receipts,
        })


@login_required
@require_POST
def submit_receipt(request):
    """Ученик отправляет чек на верификацию."""
    user_profile = request.user.profile
    if user_profile.role != 'student':
        messages.error(request, 'Только ученик может отправить чек.')
        return redirect('payment_receipts')
    tutor_id = request.POST.get('tutor_id')
    tutor = get_object_or_404(Users, id=tutor_id, role='tutor')
    if not ConnectionRequest.objects.filter(student=user_profile, tutor=tutor, status='confirmed').exists():
        messages.error(request, 'Нет подтверждённой связи с этим репетитором.')
        return redirect('payment_receipts')
    try:
        amount = Decimal((request.POST.get('amount') or '').replace(',', '.'))
        if amount <= 0:
            raise ValueError('Сумма должна быть больше нуля')
    except (ValueError, TypeError):
        messages.error(request, 'Укажите корректную сумму.')
        return redirect('payment_receipts')
    receipt_date_str = request.POST.get('receipt_date')
    if not receipt_date_str:
        messages.error(request, 'Укажите дату платежа.')
        return redirect('payment_receipts')
    try:
        receipt_date = datetime.strptime(receipt_date_str, '%Y-%m-%d').date()
        if receipt_date > timezone.now().date():
            messages.error(request, 'Дата не может быть в будущем.')
            return redirect('payment_receipts')
    except ValueError:
        messages.error(request, 'Некорректная дата.')
        return redirect('payment_receipts')
    uploaded = request.FILES.get('file')
    if not uploaded:
        messages.error(request, 'Прикрепите скан чека.')
        return redirect('payment_receipts')
    try:
        from core.validators import validate_receipt_file
        validate_receipt_file(uploaded)
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('payment_receipts')
    if amount > Decimal('999999.99'):
        messages.error(request, 'Сумма не должна превышать 999 999,99 ₽.')
        return redirect('payment_receipts')
    try:
        receipt = PaymentReceipt.objects.create(
            student=user_profile,
            tutor=tutor,
            amount=amount,
            receipt_date=receipt_date,
            file=uploaded,
            comment=(request.POST.get('comment') or '').strip() or None,
            status='pending',
        )
        student_name = f"{user_profile.first_name} {user_profile.last_name}".strip() or user_profile.user.username
        notify_user(
            tutor.user,
            f"{student_name} отправил чек на {amount} ₽ на проверку",
            link=reverse('payment_receipts'),
            notification_type='info',
        )
        messages.success(request, 'Чек отправлен на проверку репетитору.')
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect('payment_receipts')


@login_required
@require_POST
def approve_receipt(request, receipt_id):
    """Репетитор подтверждает чек: обновляет статус, баланс и создаёт транзакцию (атомарно)."""
    receipt = get_object_or_404(PaymentReceipt, id=receipt_id, tutor=request.user.profile, status='pending')
    try:
        with transaction.atomic():
            receipt.status = 'approved'
            receipt.reviewed_at = timezone.now()
            receipt.save()
            balance_obj, _ = StudentBalance.objects.select_for_update().get_or_create(
                tutor=receipt.tutor,
                student=receipt.student,
            )
            balance_obj.balance += receipt.amount
            balance_obj.save()
            Transaction.objects.create(
                student=receipt.student,
                tutor=receipt.tutor,
                amount=receipt.amount,
                type='deposit',
                description='Пополнение по чеку от %s' % receipt.receipt_date.strftime('%d.%m.%Y'),
                date=timezone.now(),
            )
        notify_user(
            receipt.student.user,
            f"Чек подтверждён. Баланс пополнен на {receipt.amount} ₽",
            link=reverse('payment_receipts'),
            notification_type='info',
        )
        student_name = '%s %s' % (receipt.student.first_name, receipt.student.last_name)
        messages.success(request, 'Чек подтверждён. Баланс ученика %s пополнен на %s ₽.' % (student_name, receipt.amount))
    except Exception:
        messages.error(request, 'Ошибка при подтверждении.')
    return redirect('payment_receipts')


@login_required
@require_POST
def reject_receipt(request, receipt_id):
    """Репетитор отклоняет чек."""
    receipt = get_object_or_404(PaymentReceipt, id=receipt_id, tutor=request.user.profile, status='pending')
    receipt.status = 'rejected'
    receipt.reviewed_at = timezone.now()
    receipt.save()
    notify_user(
        receipt.student.user,
        "Чек отклонён",
        link=reverse('payment_receipts'),
        notification_type='warning',
    )
    messages.success(request, 'Чек отклонён.')
    return redirect('payment_receipts')


@login_required
@require_POST
def request_unlink(request, connection_id):
    """Ученик создаёт заявку на открепление от репетитора (обрабатывается администратором)."""
    user_profile = request.user.profile
    if user_profile.role != 'student':
        messages.error(request, 'Только ученик может подать заявку на открепление.')
        return redirect('my_tutors')
    connection = get_object_or_404(
        ConnectionRequest,
        id=connection_id,
        student=user_profile,
        status='confirmed',
    )
    if UnlinkRequest.objects.filter(student=user_profile, tutor=connection.tutor, status='pending').exists():
        messages.info(request, 'Заявка на открепление уже отправлена и ожидает рассмотрения администратором.')
        return redirect('my_tutors')
    reason = (request.POST.get('reason') or '').strip()[:2000]
    UnlinkRequest.objects.create(student=user_profile, tutor=connection.tutor, status='pending', reason=reason)
    messages.success(request, 'Заявка на открепление отправлена. Решение примет администратор платформы.')
    return redirect('my_tutors')


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
        return safe_referer_redirect(request, 'index')

    # Запрещаем удалять, если ДЗ уже принято
    if hw.status == 'completed':
        messages.error(request, "Нельзя удалять файлы из завершенного задания.")
        return safe_referer_redirect(request, 'index')

    # Удаляем и возвращаем обратно
    response_obj.delete()
    messages.success(request, "Ответ успешно удален.")

    return safe_referer_redirect(request, 'index')

@login_required
@require_POST
def api_notification_mark_read(request, notification_id):
    """Пометить уведомление прочитанным. Возвращает JSON."""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user,
    )
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return JsonResponse({'ok': True})


@require_POST
def update_timezone(request):
    tz = request.POST.get('timezone', '').strip()
    try:
        import pytz
        valid = pytz.all_timezones_set
    except ImportError:
        try:
            import zoneinfo
            valid = zoneinfo.available_timezones()
        except ImportError:
            valid = set()
    if tz and (not valid or tz in valid):
        try:
            profile = request.user.profile
            profile.timezone = tz
            profile.save()
            return JsonResponse({'status': 'ok'})
        except Exception:
            pass
    return JsonResponse({'status': 'ignored'})


# --- Custom Admin Dashboard (superuser only) ---

def _admin_required(view_func):
    """Decorator: login + is_superuser. Use for all dashboard admin views. Redirect to index if not superuser."""
    decorated = login_required(view_func)
    return user_passes_test(lambda u: u.is_superuser, login_url='/')(decorated)


@_admin_required
def dashboard_admin_index(request):
    """Главная панели администратора — редирект на список пользователей."""
    return redirect('dashboard_admin_users')


@_admin_required
def dashboard_admin_users(request):
    """Список пользователей с пагинацией, поиском и фильтром по роли."""
    User = get_user_model()
    qs = User.objects.filter(profile__isnull=False).select_related('profile').order_by('-date_joined')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(email__icontains=search) | Q(profile__first_name__icontains=search) |
            Q(profile__last_name__icontains=search) | Q(username__icontains=search)
        )
    role = request.GET.get('role', '').strip().lower()
    if role in ('tutor', 'student'):
        qs = qs.filter(profile__role=role)

    paginator = Paginator(qs, 25)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.page(int(page_num))
    except (ValueError, TypeError):
        page = paginator.page(1)
    return render(request, 'core/dashboard_admin/users.html', {
        'page_obj': page,
        'search': search,
        'role_filter': role,
    })


@_admin_required
def dashboard_admin_unlink_requests(request):
    """Список заявок на открепление с пагинацией."""
    qs = UnlinkRequest.objects.select_related('student', 'tutor', 'reviewed_by').order_by('-created_at')
    paginator = Paginator(qs, 25)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.page(int(page_num))
    except (ValueError, TypeError):
        page = paginator.page(1)
    return render(request, 'core/dashboard_admin/unlink_requests.html', {'page_obj': page})


@_admin_required
@require_POST
def dashboard_admin_toggle_active(request, user_id):
    """POST: переключение User.is_active. Ответ JSON."""
    User = get_user_model()
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Нельзя заблокировать суперпользователя.'}, status=400)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return JsonResponse({'success': True, 'is_active': user.is_active, 'message': 'Статус обновлён.'})


@_admin_required
@require_POST
def dashboard_admin_delete_user(request, user_id):
    """POST: удаление пользователя. Тело: {"confirm": "УДАЛИТЬ"}. В transaction.atomic()."""
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный JSON.'}, status=400)
    if body.get('confirm') != 'УДАЛИТЬ':
        return JsonResponse({'success': False, 'error': 'Подтверждение не совпадает.'}, status=400)

    User = get_user_model()
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Нельзя удалить суперпользователя.'}, status=400)
    try:
        with transaction.atomic():
            profile = getattr(user, 'profile', None)
            if profile:
                profile.delete()
            user.delete()
        return JsonResponse({'success': True, 'message': 'Пользователь удалён.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@_admin_required
@require_POST
def dashboard_admin_unlink_approve(request, pk):
    """Одобрить заявку: UnlinkRequest → approved, ConnectionRequest (confirmed → archived)."""
    unlink = get_object_or_404(UnlinkRequest, pk=pk)
    if unlink.status != 'pending':
        return JsonResponse({'success': False, 'error': 'Заявка уже рассмотрена.'}, status=400)
    try:
        with transaction.atomic():
            unlink.status = 'approved'
            unlink.reviewed_at = timezone.now()
            unlink.reviewed_by = request.user
            unlink.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
            conn = ConnectionRequest.objects.filter(
                student=unlink.student, tutor=unlink.tutor, status='confirmed'
            ).first()
            if conn:
                conn.status = 'archived'
                conn.save(update_fields=['status'])
        return JsonResponse({'success': True, 'message': 'Заявка одобрена.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@_admin_required
@require_POST
def dashboard_admin_unlink_reject(request, pk):
    """Отклонить заявку на открепление."""
    unlink = get_object_or_404(UnlinkRequest, pk=pk)
    if unlink.status != 'pending':
        return JsonResponse({'success': False, 'error': 'Заявка уже рассмотрена.'}, status=400)
    unlink.status = 'rejected'
    unlink.reviewed_at = timezone.now()
    unlink.reviewed_by = request.user
    unlink.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
    return JsonResponse({'success': True, 'message': 'Заявка отклонена.'})
