import io
import json
import os
import zipfile
from django.utils.encoding import force_str
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Lessons, Users, Subjects, TutorSubjects, ConnectionRequest, StudentTariff, LessonAttendance, \
    Transaction, FilesLibrary, Homework, HomeworkResponse
from .forms import AddSubjectForm, RegistrationForm, ProfileUpdateForm, AddLessonForm
from django.contrib.auth.models import User as AuthUser
from .models import Users as Profile
from django.contrib.auth import login as django_login
from django.shortcuts import get_object_or_404
from django.contrib import messages

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from datetime import timedelta, datetime
from .models import StudyGroups
from .forms import StudyGroupForm
import uuid
from django.utils import timezone
from django.db.models import Q
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone
from django.http import HttpResponse
from .utils import send_telegram_notification, send_verification_email
from django.utils.dateparse import parse_datetime
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.db import transaction
from django.http import FileResponse
@login_required
def index(request):

    user_role = 'guest'
    lessons_list = []
    user_profile = None
    tutor_students = []
    tutor_groups = []
    my_subjects = []
    tariffs_list = []
    student_debt = 0
    profile = request.user.profile
    homeworks = []
    attendance_map = []

    try:
        user_profile = request.user.profile
        user_role = user_profile.role
    except Exception:
        if request.user.is_superuser:
            user_role = 'admin'

    if user_role == 'tutor' and user_profile:
        tariffs_list = list(StudentTariff.objects.filter(tutor=user_profile).values(
            'student_id', 'group_id', 'subject_id', 'price'
        ))
        for t in tariffs_list: t['price'] = float(t['price'])
        # Базовый запрос: все занятия репетитора
        lessons_list = Lessons.objects.filter(tutor=user_profile).prefetch_related('attendances__student').order_by('start_time')
        attendance_map = {}
        for lesson in lessons_list:
            attendance_map[str(lesson.id)] = [
                {
                    "id": att.id,
                    "name": f"{att.student.first_name} {att.student.last_name}",
                    "present": att.was_present
                } for att in lesson.attendances.all()
            ]

        # 1. Фильтр по ученику или группе (через префиксы s_ и g_)
        target = request.GET.get('target')
        if target:
            if target.startswith('s_'):
                lessons_list = lessons_list.filter(student_id=target[2:])
            elif target.startswith('g_'):
                lessons_list = lessons_list.filter(group_id=target[2:])

        # 2. Фильтр по диапазону ДАТ
        start_date = request.GET.get('date_from')
        end_date = request.GET.get('date_to')
        if start_date:
            lessons_list = lessons_list.filter(start_time__date__gte=start_date)
        if end_date:
            lessons_list = lessons_list.filter(start_time__date__lte=end_date)

        # 3. Фильтр по диапазону ВРЕМЕНИ
        s_time = request.GET.get('time_from')
        e_time = request.GET.get('time_to')
        if s_time:
            lessons_list = lessons_list.filter(start_time__time__gte=s_time)
        if e_time:
            lessons_list = lessons_list.filter(start_time__time__lte=e_time)

        # 4. Фильтр по предмету
        subject_id = request.GET.get('subject')
        if subject_id:
            lessons_list = lessons_list.filter(subject_id=subject_id)

        # 5. Фильтр по статусу оплаты
        status = request.GET.get('status')
        if status == 'paid':
            lessons_list = lessons_list.filter(is_paid=True)
        elif status == 'unpaid':
            lessons_list = lessons_list.filter(is_paid=False)

        # Данные для выпадающих списков
        accepted_ids = ConnectionRequest.objects.filter(
            tutor=user_profile,
            status='confirmed'  # или 'accepted', проверь в базе
        ).values_list('student_id', flat=True)

        tutor_students = Users.objects.filter(id__in=accepted_ids)
        tutor_groups = StudyGroups.objects.filter(tutor=user_profile)

        # 3. Список предметов репетитора (наполняем переменную)
        my_subjects = TutorSubjects.objects.filter(tutor=user_profile).select_related('subject')
        connections = ConnectionRequest.objects.filter(tutor=user_profile, status='confirmed')
        groups = StudyGroups.objects.filter(tutor=user_profile)



        if 'save_tariff' in request.POST and request.method == "POST":
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

    elif user_role == 'student':
        # ЛОГИКА ДЛЯ УЧЕНИКА: ищем личные уроки И уроки его групп
        lessons_list = Lessons.objects.filter(
            Q(student=user_profile) | Q(group__students=user_profile)
        ).distinct().order_by('start_time')
        student_debt = LessonAttendance.objects.filter(
            student=user_profile,
            was_present=True,
            is_paid=False
        ).aggregate(Sum('lesson__price'))['lesson__price__sum'] or 0
        student_debt = max(0, student_debt - profile.balance)
        homeworks = Homework.objects.filter(student=profile).order_by('-deadline')

    # 4. Обработка POST-запросов для предметов
    if request.method == 'POST':
        if 'add_subject' in request.POST and user_role == 'tutor':
            subject_name = request.POST.get('subject_name')
            if subject_name:
                subject_obj, _ = Subjects.objects.get_or_create(name=subject_name)
                TutorSubjects.objects.get_or_create(tutor=user_profile, subject=subject_obj)
            return redirect('index')

        if 'delete_subject' in request.POST and user_role == 'tutor':
            subj_id = request.POST.get('subject_id')
            TutorSubjects.objects.filter(tutor=user_profile, subject_id=subj_id).delete()
            return redirect('index')
    files = FilesLibrary.objects.filter(tutor=user_profile).order_by('-upload_date')
    context = {
        'lessons': lessons_list,
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
        'homeworks' : homeworks,
        'attendance_map_json': attendance_map,

    }

    return smart_render(request, 'core/index.html', context)




def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # 1. Создаем пользователя (ДЕАКТИВИРОВАННЫМ)
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False
            user.save()

            # 2. Создаем Профиль
            # УБРАЛИ ПОВТОР user=user из image_67be83.png
            Users.objects.create(
                user=user,
                role=form.cleaned_data['role']
            )

            # 3. Отправка письма (ТЕПЕРЬ ВНУТРИ if form.is_valid)
            try:
                send_verification_email(request, user)
                # Если всё ок — перекидываем на страницу ожидания
                return render(request, 'core/registration_pending.html', {'email': user.email})
            except Exception as e:
                # Если почта не ушла, удаляем юзера, чтобы он мог регаться снова
                print(f"Ошибка почты: {e}")
                user.delete()
                messages.error(request, "Ошибка при отправке письма. Попробуйте позже.")
                return redirect('register')
        else:
            # ТУТ САМОЕ ВАЖНОЕ: если форма не валидна, мы увидим почему
            print("ОШИБКИ ФОРМЫ:", form.errors)
    else:
        form = RegistrationForm()

    return render(request, 'core/register.html', {'form': form})


# --- РЕДАКТИРОВАНИЕ ПРОФИЛЯ ---
@login_required
def edit_profile(request):
    # Пытаемся получить профиль текущего пользователя
    try:
        profile = request.user.profile
    except Users.DoesNotExist:
        # Если вдруг профиля нет (сбой), создаем на лету
        profile = Users.objects.create(user=request.user, role='student')

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # После сохранения отправляем на главную
            return redirect('index')
    else:
        form = ProfileUpdateForm(instance=profile)

    return smart_render(request, 'core/edit_profile.html', {'form': form})


# --- ВХОД (LOGIN) ---
def user_login(request):
    if request.method == 'POST':
        # Используем стандартную форму аутентификации или свою
        # Для простоты можно использовать AuthenticationForm из django.contrib.auth.forms
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


# --- ВЫХОД (LOGOUT) ---
def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def confirmations(request):
    # ИСПРАВЛЕНИЕ: используем student__user, чтобы Django понял,
    # что мы ищем профиль, привязанный к текущему авторизованному юзеру.
    incoming_requests = ConnectionRequest.objects.filter(
        student__user=request.user,  # Было student__id=request.user.id (это ошибка)
        status='pending'
    )
    return smart_render(request, 'core/confirmations.html', {'requests': incoming_requests})

@login_required
def accept_request(request, request_id):
    # Здесь тоже нужно исправить проверку безопасности
    conn_request = get_object_or_404(
        ConnectionRequest,
        id=request_id,
        student__user=request.user # Исправили student__id на student__user
    )
    conn_request.status = 'confirmed'
    conn_request.save()
    return redirect('confirmations')

@login_required
def reject_request(request, request_id):
    # И здесь
    conn_request = get_object_or_404(
        ConnectionRequest,
        id=request_id,
        student__user=request.user # Исправили student__id на student__user
    )
    conn_request.delete()
    return redirect('confirmations')


@login_required
def my_students(request):
    user_profile = request.user.profile

    # Сохранение тарифа
    if request.method == 'POST' and 'save_tariff' in request.POST:
        StudentTariff.objects.update_or_create(
            tutor=user_profile,
            student_id=request.POST.get('t_student') or None,
            group_id=request.POST.get('t_group') or None,
            subject_id=request.POST.get('t_subject'),
            defaults={'price': request.POST.get('t_price')}  # Используем price!
        )
        return redirect('my_students')

    connections = ConnectionRequest.objects.filter(tutor=user_profile, status='confirmed')
    groups = StudyGroups.objects.filter(tutor=user_profile)
    # Передаем предметы репетитора
    my_subjects = TutorSubjects.objects.filter(tutor=user_profile).select_related('subject')

    return smart_render(request, 'core/my_students.html', {
        'connections': connections, 'groups': groups, 'my_subjects': my_subjects
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
        # Получаем логин из формы
        target_username = request.POST.get('username')

        try:
            # 1. Ищем по ЛОГИНУ (username), а не по email
            student_auth = AuthUser.objects.get(username=target_username)

            # 2. Проверяем роль
            if hasattr(student_auth, 'profile') and student_auth.profile.role == 'student':

                # 3. Проверка на дубликаты
                existing = ConnectionRequest.objects.filter(
                    tutor=request.user.profile,
                    student=student_auth.profile
                ).exists()

                if not existing:
                    # 4. Создаем заявку
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


@login_required
def add_lesson(request):
    print(f"DEBUG RAW POST: {request.POST.get('start_time')}")
    if request.user.profile.role != 'tutor':
        return redirect('index')

    if request.method == 'POST':
        form = AddLessonForm(request.POST, tutor=request.user.profile)
        if form.is_valid():
            base_start_time = form.cleaned_data.get('start_time')
            print(f"DEBUG CLEANED DATA: {base_start_time}")
            duration = form.cleaned_data.get('duration')
            is_recurring = form.cleaned_data.get('is_recurring')
            new_series_id = uuid.uuid4() if is_recurring else None



            # ЛОГИКА ИЛИ-ИЛИ
            repeat_count = form.cleaned_data.get('repeat_count')
            repeat_until = form.cleaned_data.get('repeat_until')
            selected_weekdays = form.cleaned_data.get('weekdays') or []

            end_date_limit = base_start_time.date()
            if is_recurring:
                if repeat_until:
                    end_date_limit = repeat_until
                elif repeat_count:
                    end_date_limit = base_start_time.date() + timedelta(weeks=repeat_count)
                else:
                    end_date_limit = base_start_time.date() + timedelta(weeks=4)

            created_count = 0
            current_date = base_start_time.date()

            while current_date <= end_date_limit:
                is_first_day = (current_date == base_start_time.date())
                is_selected_day = str(current_date.weekday()) in selected_weekdays

                if not is_recurring or is_first_day or is_selected_day:
                    lesson = form.save(commit=False)
                    lesson.pk = None
                    lesson.tutor = request.user.profile
                    lesson.series_id = new_series_id

                    naive_start = timezone.make_naive(base_start_time)  # делаем "наивным"
                    new_naive = naive_start.replace(
                        year=current_date.year,
                        month=current_date.month,
                        day=current_date.day,
                        second=0,
                        microsecond=0
                    )
                    new_start = timezone.make_aware(new_naive)
                    print(f"DEBUG FINAL START: {new_start} (Seconds: {new_start.second})")
                    lesson.start_time = new_start
                    lesson.end_time = new_start + timedelta(minutes=duration)


                    if form.cleaned_data.get('lesson_type') == 'individual':
                        lesson.group = None
                    else:
                        lesson.student = None

                    lesson.save()
                    form.save_m2m()
                    created_count += 1
                    students_to_link = []
                    if lesson.group:
                        students_to_link = lesson.group.students.all()
                    elif lesson.student:
                        students_to_link = [lesson.student]

                    for student in students_to_link:
                        # Создаем запись для каждого ученика
                        LessonAttendance.objects.get_or_create(lesson=lesson, student=student)

                if not is_recurring: break
                current_date += timedelta(days=1)
                if created_count >= 100: break

            messages.success(request, f"Создано занятий: {created_count}")
            return redirect('index')
        else:
            # Выводим ошибки формы, если что-то не так
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Ошибка в поле {field}: {error}")
    else:
        form = AddLessonForm(tutor=request.user.profile)
    if getattr(request, 'is_mobile', False):
        return smart_render(request, 'core/add_lesson.html', {'form': form})
    return redirect('index')


# --- УПРАВЛЕНИЕ УРОКАМИ ---
@login_required
def edit_lesson(request, lesson_id):
    # Получаем урок, но только если он принадлежит текущему репетитору
    lesson = get_object_or_404(Lessons, id=lesson_id, tutor=request.user.profile)

    if request.method == 'POST':
        form = AddLessonForm(request.POST, instance=lesson, tutor=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Занятие обновлено!")
            return redirect('index')
    else:
        # Загружаем форму с уже заполненными данными (instance=lesson)
        form = AddLessonForm(instance=lesson, tutor=request.user.profile)
    if getattr(request, 'is_mobile', False):
        return smart_render(request, 'core/edit_lesson.html', {'form': form, 'lesson': lesson})
    return redirect('index')


@login_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lessons, id=lesson_id, tutor=request.user.profile)
    mode = request.POST.get('delete_mode', 'single')

    if request.method == 'GET' and getattr(request, 'is_mobile', False):
        return smart_render(request, 'core/lesson_confirm_delete.html', {'lesson': lesson})

    if lesson.series_id and mode != 'single':
        query = Lessons.objects.filter(series_id=lesson.series_id)
        if mode == 'following':
            query = query.filter(start_time__gte=lesson.start_time)
        query.delete()
        messages.success(request, "Серия занятий удалена")
    else:
        lesson.delete()
        messages.success(request, "Занятие удалено")

    return redirect('index')



# --- УПРАВЛЕНИЕ ГРУППАМИ ---
@login_required
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
def delete_group(request, group_id):
    group = get_object_or_404(StudyGroups, id=group_id, tutor=request.user.profile)
    if request.method == 'POST':
        group.delete()
        messages.success(request, "Группа удалена.")
    return redirect('my_students')


# --- УПРАВЛЕНИЕ СТУДЕНТАМИ (Разрыв связи) ---
@login_required
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
            form.save_m2m()  # Сохраняем учеников
            messages.success(request, f"Группа '{new_group.name}' успешно создана!")
            return redirect('my_students')
    else:
        form = StudyGroupForm(tutor=request.user.profile)

    return smart_render(request, 'core/create_group.html', {'form': form})


@login_required
def bulk_action_lessons(request):
    if request.method == 'POST' and request.user.profile.role == 'tutor':
        ids_str = request.POST.get('lesson_ids', '')
        action = request.POST.get('action_type')

        if not ids_str:
            return redirect('index')

        id_list = [i for i in ids_str.split(',') if i.strip()]
        queryset = Lessons.objects.filter(id__in=id_list, tutor=request.user.profile)

        if action == 'delete':
            count = queryset.count()
            queryset.delete()
            messages.success(request, f"Удалено занятий: {count}")

        elif action == 'mass_edit':
            # Собираем данные один раз
            new_date = request.POST.get('mass_date')
            new_time = request.POST.get('mass_time')
            new_student = request.POST.get('mass_student')
            new_group = request.POST.get('mass_group')
            new_subject = request.POST.get('mass_subject')
            new_duration = request.POST.get('mass_duration')
            new_price = request.POST.get('mass_price')
            selected_materials = request.POST.getlist('materials')

            with transaction.atomic():
                for lesson in queryset:
                    # Обновление времени
                    if new_date or new_time:
                        d = new_date if new_date else lesson.start_time.strftime('%Y-%m-%d')
                        t = new_time if new_time else lesson.start_time.strftime('%H:%M')
                        naive_dt = datetime.strptime(f"{d} {t}", '%Y-%m-%d %H:%M')
                        lesson.start_time = timezone.make_aware(naive_dt).replace(second=0, microsecond=0)

                        dur = int(new_duration) if new_duration else lesson.duration
                        lesson.end_time = lesson.start_time + timedelta(minutes=dur)

                    # Смена ученика/группы
                    if new_student:
                        lesson.student_id = new_student
                        lesson.group = None
                    elif new_group:
                        lesson.group_id = new_group
                        lesson.student = None

                    if new_subject: lesson.subject_id = new_subject
                    if new_duration: lesson.duration = int(new_duration)
                    if new_price: lesson.price = Decimal(new_price)

                    lesson.save()

                    # Материалы
                    if 'materials' in request.POST:
                        lesson.materials.set(selected_materials)

                    # Пересоздаем посещаемость, если сменился состав
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
def toggle_attendance_pay(request, attendance_id):
    # Ограничиваем выборку только уроками этого репетитора
    attendance = get_object_or_404(
        LessonAttendance,
        id=attendance_id,
        lesson__tutor=request.user.profile
    )
    student = attendance.student
    price = attendance.lesson.price

    # Если мы хотим отметить как ОПЛАЧЕНО (текущий статус False)
    if not attendance.is_paid:
        if student.balance >= price:
            # Денег достаточно: списываем и создаем транзакцию
            student.balance -= price
            attendance.is_paid = True
            Transaction.objects.create(
                student=student,
                tutor=request.user.profile,
                attendance=attendance,
                amount=price,
                type='withdrawal',
                description=f"Оплата: {attendance.lesson.subject.name} ({attendance.lesson.start_time.strftime('%d.%m')})"
            )
        else:
            # Денег мало: прерываем выполнение и возвращаем ошибку
            return JsonResponse({
                'status': 'error',
                'message': 'Недостаточно средств на балансе ученика'
            }, status=400)

    # Если мы отменяем оплату (текущий статус True)
    else:
        student.balance += price
        attendance.is_paid = False
        # Удаляем транзакцию списания
        Transaction.objects.filter(attendance=attendance, type='withdrawal').delete()

    student.save()
    attendance.save()

    # Считаем актуальный долг (занятия были, но не оплачены)
    now = timezone.now()
    new_total_debt = LessonAttendance.objects.filter(
        student=student,
        lesson__tutor=request.user.profile,
        was_present=True,
        lesson__start_time__lt=now,
        is_paid=False
    ).aggregate(total=Sum('lesson__price'))['total'] or 0
    new_total_debt = max(0,new_total_debt - student.balance)

    return JsonResponse({
        'status': 'ok',
        'is_paid': attendance.is_paid,
        'new_balance': float(student.balance),
        'new_total_debt': float(new_total_debt)
    })


@login_required
def student_card(request, student_id):
    tutor = request.user.profile
    student = get_object_or_404(Users, id=student_id)
    now = timezone.now()

    # 1. Обработка пополнения баланса (твой существующий код)
    if request.method == 'POST' and 'update_balance' in request.POST:
        amount = Decimal(request.POST.get('amount', 0))
        desc = request.POST.get('description', 'Пополнение баланса')
        custom_date = request.POST.get('date')
        Transaction.objects.create(
            student=student, tutor=tutor, amount=amount, type='deposit', description=desc,
            date=datetime.strptime(custom_date, '%Y-%m-%dT%H:%M') if custom_date else timezone.now()
        )
        student.balance += amount
        student.save()
        messages.success(request, f"Баланс пополнен")
        return redirect('student_card', student_id=student.id)

    # 2. Данные для журнала оплат (твой существующий код)
    attendances = LessonAttendance.objects.filter(
        student=student, lesson__tutor=tutor, was_present=True, lesson__start_time__lt=now
    ).select_related('lesson', 'lesson__subject').order_by('-lesson__start_time')

    total_debt = attendances.filter(is_paid=False).aggregate(total=Sum('lesson__price'))['total'] or 0

    # 3. НОВОЕ: Данные для блока ДЗ и материалов
    homeworks = Homework.objects.filter(student=student, tutor=tutor).prefetch_related('files').order_by('-created_at')
    # Файлы репетитора для выбора в модалке задания ДЗ
    tutor_files = FilesLibrary.objects.filter(tutor=tutor).order_by('-upload_date')
    # Предметы, по которым репетитор может задать ДЗ
    subjects = Subjects.objects.filter(tutorsubjects__tutor=tutor)

    context = {
        'student': student,
        'attendances': attendances,
        'total_debt': total_debt,
        'homeworks': homeworks,  # Список ДЗ
        'tutor_files': tutor_files,  # Список файлов для модалки
        'subjects': subjects,  # Список предметов для модалки
        'transactions': student.transactions.filter(tutor=tutor).order_by('-date'),
        'performance': student.performance.all().order_by('-date')[:10]
    }
    return smart_render(request, 'core/student_card.html', context)


@login_required
def add_homework(request, student_id):
    if request.method == 'POST':
        tutor = request.user.profile
        student = get_object_or_404(Users, id=student_id)

        # 1. Получаем объект предмета (чтобы работал .name)
        subject_id = request.POST.get('subject')
        subject_obj = get_object_or_404(Subjects, id=subject_id)

        deadline_raw = request.POST.get('deadline')
        description = request.POST.get('description')

        # 2. Создаем запись в базе
        hw = Homework.objects.create(
            tutor=tutor,
            student=student,
            subject=subject_obj,
            description=description,
            deadline=deadline_raw or None
        )

        # 3. ПРЕВРАЩАЕМ СТРОКУ В ДАТУ ДЛЯ TELEGRAM
        # Это решает ошибку 'str' object has no attribute 'strftime'
        deadline_obj = parse_datetime(deadline_raw) if deadline_raw else None
        deadline_display = deadline_obj.strftime('%d.%m %H:%M') if deadline_obj else 'Не задан'

        # 4. Формируем и отправляем уведомление
        msg = (
            f"📚 <b>Новое задание!</b>\n"
            f"Предмет: {subject_obj.name}\n"
            f"Преподаватель: {tutor.first_name}\n"
            f"Срок: {deadline_display}\n\n"
            f"Посмотреть: <a href='https://all4tutors.ru/my-assignments/'>Перейти на сайт</a>"
        )

        # ПРОВЕРКА: отправляем, только если у ученика есть telegram_id
        if student.telegram_id:
            from .utils import send_telegram_notification
            send_telegram_notification(student, msg)

        # 5. Прикрепляем файлы
        file_ids = request.POST.getlist('files')
        if file_ids:
            hw.files.set(file_ids)

        messages.success(request, "Домашнее задание добавлено")

    return redirect('student_card', student_id=student_id)

@login_required
def toggle_presence(request, attendance_id):
    attendance = get_object_or_404(LessonAttendance, id=attendance_id, lesson__tutor=request.user.profile)
    attendance.was_present = not attendance.was_present
    attendance.save()
    return JsonResponse({'status': 'ok', 'was_present': attendance.was_present})


@login_required
def files_library(request):
    user_profile = request.user.profile


    # Обработка загрузки файла
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        FilesLibrary.objects.create(
            tutor=user_profile,
            file=uploaded_file,
            file_name=request.POST.get('file_name') or uploaded_file.name
        )
        messages.success(request, "Файл успешно добавлен в библиотеку!")
        return redirect('files_library')

    # Получаем все файлы репетитора
    files = FilesLibrary.objects.filter(tutor=user_profile).order_by('-upload_date')
    return smart_render(request, 'core/files_library.html', {'files': files})


@login_required
def edit_file(request, file_id):
    file_obj = get_object_or_404(FilesLibrary, id=file_id, tutor=request.user.profile)
    if request.method == 'POST':
        new_name = request.POST.get('file_name')
        if new_name:
            file_obj.file_name = new_name

        # НОВОЕ: Замена физического файла
        if request.FILES.get('file'):
            if file_obj.file:
                file_obj.file.delete(save=False)  # удаляем старый
            file_obj.file = request.FILES['file']

        file_obj.save()
        messages.success(request, "Материал успешно обновлен")
    return redirect('files_library')

@login_required
def delete_file(request, file_id):
    file_obj = get_object_or_404(FilesLibrary, id=file_id, tutor=request.user.profile)
    # Удаляем файл из папки media, чтобы не занимать место
    if file_obj.file:
        file_obj.file.delete()
    file_obj.delete()
    messages.success(request, "Файл удален")
    return redirect('files_library')


@login_required
def download_lesson_materials(request, lesson_id):
    # Получаем урок и все прикрепленные к нему файлы (materials)
    lesson = get_object_or_404(Lessons, id=lesson_id)
    files = lesson.materials.all()

    if not files:
        messages.warning(request, "К этому уроку не прикреплено ни одного файла.")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    # Создаем байтовый поток (буфер) в памяти
    buffer = io.BytesIO()

    # Открываем архив для записи в этот буфер
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for f in files:
            if f.file and os.path.exists(f.file.path):
                # Получаем расширение оригинального файла
                ext = os.path.splitext(f.file.name)[1]
                # Формируем имя файла в архиве (название из базы + расширение)
                name_in_zip = f.file_name if f.file_name.endswith(ext) else f.file_name + ext
                # Записываем физический файл в архив
                zip_file.write(f.file.path, name_in_zip)

    # Возвращаем курсор в начало буфера
    buffer.seek(0)

    # Формируем ответ с типом zip-архива
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="materials_lesson_{lesson_id}.zip"'

    return response


@login_required
def download_homework_all(request, hw_id):
    # Используем tutor=request.user.profile для безопасности
    hw = get_object_or_404(Homework, id=hw_id, tutor=request.user.profile)
    files = hw.files.all()

    if not files:
        messages.warning(request, "Файлов для скачивания нет")
        return redirect(request.META.get('HTTP_REFERER', 'index'))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_f:
        for f in files:
            if f.file and os.path.exists(f.file.path):
                # Сохраняем расширение файла
                ext = os.path.splitext(f.file.name)[1]
                name_in_zip = f.file_name if f.file_name.endswith(ext) else f.file_name + ext
                zip_f.write(f.file.path, name_in_zip)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="homework_{hw_id}_files.zip"'
    return response


@login_required
def edit_homework(request, hw_id):
    hw = get_object_or_404(Homework, id=hw_id, tutor=request.user.profile)
    if request.method == 'POST':
        # Поля для редактирования (твои старые)
        if request.POST.get('description'):
            hw.description = request.POST.get('description')
        if request.POST.get('subject'):
            hw.subject_id = request.POST.get('subject')
        if request.POST.get('deadline'):
            hw.deadline = request.POST.get('deadline')

        # НОВЫЕ ПОЛЯ для проверки
        if request.POST.get('status'):
            hw.status = request.POST.get('status')
        if 'tutor_comment' in request.POST:
            hw.tutor_comment = request.POST.get('tutor_comment')

        # Обновляем файлы (твои старые)
        file_ids = request.POST.getlist('files')
        if file_ids:
            hw.files.set(file_ids)

        hw.save()
        messages.success(request, "Задание обновлено")
    return redirect('student_card', student_id=hw.student.id)


@login_required
def delete_homework(request, hw_id):
    hw = get_object_or_404(Homework, id=hw_id, tutor=request.user.profile)
    student_id = hw.student.id
    hw.delete()
    messages.success(request, "Задание удалено")
    return redirect('student_card', student_id=student_id)


@login_required
def toggle_homework_status(request, hw_id):
    hw = get_object_or_404(Homework, id=hw_id, tutor=request.user.profile)
    # Циклическое переключение статусов: Задано -> На проверке -> Выполнено -> Задано
    status_cycle = {
        'pending': 'submitted',
        'submitted': 'completed',
        'completed': 'pending'
    }
    hw.status = status_cycle.get(hw.status, 'pending')
    hw.save()
    return redirect('student_card', student_id=hw.student.id)


@login_required
def finances(request):
    tutor = request.user.profile

    # Получаем даты из фильтра
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Базовая выборка посещаемости (проведенные уроки)
    attendance_qs = LessonAttendance.objects.filter(
        lesson__tutor=tutor,
        was_present=True
    )

    # Применяем фильтры по датам, если они есть
    if date_from:
        attendance_qs = attendance_qs.filter(lesson__start_time__date__gte=date_from)
    if date_to:
        attendance_qs = attendance_qs.filter(lesson__start_time__date__lte=date_to)

    # Если фильтров нет, для графика берем последние 30 дней
    if not date_from and not date_to:
        last_30_days = timezone.now() - timedelta(days=30)
        chart_qs = attendance_qs.filter(lesson__start_time__gte=last_30_days)
    else:
        chart_qs = attendance_qs

    # Расчеты показателей за выбранный период
    total_earned = attendance_qs.aggregate(Sum('lesson__price'))['lesson__price__sum'] or 0
    total_debt = attendance_qs.filter(is_paid=False).aggregate(Sum('lesson__price'))['lesson__price__sum'] or 0

    # Данные для графика
    stats_raw = chart_qs.values('lesson__start_time__date').annotate(
        total=Sum('lesson__price')
    ).order_by('lesson__start_time__date')

    chart_labels = [s['lesson__start_time__date'].strftime('%d.%m') for s in stats_raw]
    chart_values = [float(s['total']) for s in stats_raw]

    # История операций (транзакции) всегда внизу
    transactions = Transaction.objects.filter(tutor=tutor).order_by('-date')

    context = {
        'total_earned': total_earned,
        'total_debt': total_debt,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'transactions': transactions,
        'date_from': date_from,
        'date_to': date_to,
    }
    return smart_render(request, 'core/finances.html', context)


@login_required
def submit_homework(request, hw_id):
    # Используем get_object_or_404, чтобы сервер не падал, если ID неверный
    homework = get_object_or_404(Homework, id=hw_id, student=request.user.profile)

    if request.method == 'POST':
        files = request.FILES.getlist('response_files')
        if files:
            for f in files:
                HomeworkResponse.objects.create(
                    homework=homework,
                    file=f,
                    file_name=f.name
                )
            homework.status = 'submitted'
            homework.save()
            tutor = homework.tutor
            if tutor.telegram_id:
                msg = (
                    f"✅ <b>Задание сдано на проверку!</b>\n\n"
                    f"<b>Ученик:</b> {request.user.profile.first_name} {request.user.profile.last_name}\n"
                    f"<b>Предмет:</b> {homework.subject.name}\n"
                    f"<b>Задание:</b> {homework.description[:50]}...\n\n"
                    f"🧐 <a href='https://all4tutors.ru/student-card/{request.user.profile.id}/'>Перейти к проверке</a>"
                )
                send_telegram_notification(tutor, msg)
            messages.success(request, "Задание успешно отправлено!")
        else:
            messages.error(request, "Файлы не были выбраны.")
        return redirect('my_assignments')

    # ОБЯЗАТЕЛЬНЫЙ ОТВЕТ для GET-запроса (решает проблему ValueError)
    return redirect('my_assignments')


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
        from .models import Users
        tutor = Users.objects.filter(user=request.user).first()
    if not tutor:
        from .models import Users
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
        return redirect('my_subjects')

    subjects = Subjects.objects.filter(tutor=tutor)
    return smart_render(request, 'core/my_subjects.html', {'subjects': subjects})


# Функция для удаления предмета
@login_required
def delete_subject(request, subject_id):
    subject = Subjects.objects.get(id=subject_id, tutor=request.user.profile)
    subject.delete()
    return redirect('my_subjects')


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
        # 1. Расшифровываем ID пользователя из ссылки
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # 2. Проверяем токен на валидность
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True  # ВКЛЮЧАЕМ АККАУНТ
        user.save()
        messages.success(request, "Твой аккаунт активирован! Теперь заходи в систему.")
        return redirect('login') # Или на страницу логина
    else:
        # Если ссылка битая или токен старый
        return render(request, 'core/activation_invalid.html')




@login_required
def group_card(request, group_id):
    tutor = request.user.profile
    group = get_object_or_404(StudyGroups, id=group_id, tutor=tutor)
    now = timezone.now()

    # ЛОГИКА ГРУППОВОГО ДЗ (POST запрос)
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

        messages.success(request, f"Задание отправлено всей группе")
        return redirect('group_card', group_id=group.id)

    # ДАННЫЕ ДЛЯ КАРТОЧКИ
    attendances = LessonAttendance.objects.filter(
        lesson__group=group,
        lesson__tutor=tutor
    ).select_related('lesson', 'lesson__subject', 'student').order_by('-lesson__start_time')


    tutor_files = FilesLibrary.objects.filter(tutor=tutor).order_by('-upload_date')

    context = {
        'group': group,
        'attendances': attendances,
        'members': group.students.all(),  # Список учеников
        'tutor_files': tutor_files,  # Список файлов
    }
    return smart_render(request, 'core/group_card.html', context)

@login_required
def faq(request):
    return smart_render(request, 'core/faq.html')