from django.utils import timezone

from .models import ChatMessage, ConnectionRequest, Homework, Lessons, Notification, StudyGroups, Users
from django.urls import resolve, reverse, NoReverseMatch
from django.db.models import Q


def notifications_processor(request):
    """Данные для колокольчика уведомлений (без N+1)."""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).count()

    recent = list(
        Notification.objects.filter(user=request.user)
        .order_by('-created_at')[:10]
    )

    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent,
    }


def unread_chat_processor(request):
    """Количество непрочитанных сообщений в чате (для бейджа в сайдбаре)."""
    if not request.user.is_authenticated:
        return {'unread_chat_count': 0}
    try:
        profile = request.user.profile
    except Exception:
        return {'unread_chat_count': 0}
    # Сообщения, где текущий пользователь — получатель (не отправитель) и is_read=False
    if profile.role == 'tutor':
        count = ChatMessage.objects.filter(
            connection__tutor=profile,
            is_read=False,
        ).exclude(sender=profile).count()
    else:
        count = ChatMessage.objects.filter(
            connection__student=profile,
            is_read=False,
        ).exclude(sender=profile).count()
    return {'unread_chat_count': count}


def next_lesson_processor(request):
    if not request.user.is_authenticated:
        return {'next_lesson': None}

    try:
        user_profile = request.user.profile
        now = timezone.now()

        if user_profile.role == 'tutor':
            next_lesson = Lessons.objects.filter(
                tutor=user_profile,
                start_time__gt=now
            ).order_by('start_time').first()
        else:
            next_lesson = Lessons.objects.filter(
                Q(student=user_profile) | Q(group__students=user_profile),
                start_time__gt=now
            ).distinct().order_by('start_time').first()

        return {'next_lesson': next_lesson}
    except Exception:
        return {'next_lesson': None}


# Цепочка breadcrumb: url_name -> (название страницы, родитель url_name или None)
BREADCRUMB_CHAIN = {
    'index': ('Главная', None),
    'my_students': ('Мои ученики', 'index'),
    'student_card': (None, 'my_students'),  # название подставим из БД
    'add_student': ('Добавить ученика', 'my_students'),
    'add_lesson': ('Новое занятие', 'index'),
    'edit_lesson': ('Редактирование занятия', 'index'),
    'add_group': ('Создать группу', 'my_students'),
    'edit_group': (None, 'my_students'),  # название подставим из БД
    'group_card': (None, 'my_students'),
    'files_library': ('Мои файлы', 'index'),
    'edit_file': ('Редактирование файла', 'files_library'),
    'finances': ('Финансы', 'index'),
    'my_assignments': ('Мои задания', 'index'),
    'homework_detail': (None, 'my_assignments'),
    'edit_homework': ('Редактирование ДЗ', 'my_assignments'),
    'my_subjects': ('Мои предметы', 'index'),
    'edit_subject': ('Редактирование предмета', 'my_subjects'),
    'delete_subject': ('Мои предметы', 'my_subjects'),
    'edit_profile': ('Профиль', 'index'),
    'confirmations': ('Подтверждения', 'index'),
    'my_tutors': ('Мои репетиторы', 'index'),
    'tutor_card': (None, 'my_tutors'),
    'faq': ('FAQ', 'index'),
    'archived_students': ('Архив учеников', 'my_students'),
    'accept_request': ('Подтверждения', 'confirmations'),
    'reject_request': ('Подтверждения', 'confirmations'),
    'chat_list': ('Сообщения', 'index'),
    'chat_thread': (None, 'chat_list'),
    'bot_chat': ('AI-помощник', 'chat_list'),
}


def breadcrumbs(request):
    if not request.user.is_authenticated:
        return {'auto_breadcrumbs': []}

    try:
        match = resolve(request.path)
    except Exception:
        return {'auto_breadcrumbs': [{'name': 'Главная', 'url': reverse('index')}]}

    url_name = match.url_name
    kwargs = match.kwargs

    if url_name not in BREADCRUMB_CHAIN:
        return {'auto_breadcrumbs': [{'name': 'Главная', 'url': reverse('index')}]}

    # Собираем цепочку от текущей страницы к корню
    chain = []
    current = url_name
    while current:
        if current not in BREADCRUMB_CHAIN:
            break
        label, parent = BREADCRUMB_CHAIN[current]
        try:
            url = reverse(current, kwargs=kwargs if current == url_name else {})
        except NoReverseMatch:
            url = request.path
        chain.append((label, url, current))
        if parent is None:
            if current != 'index':
                chain.append(('Главная', reverse('index'), 'index'))
            break
        current = parent

    # Название текущей страницы из БД, если нужно
    if chain and chain[0][0] is None:
        first_label, first_url, first_name = chain[0]
        if first_name == 'student_card' and kwargs.get('student_id'):
            try:
                student = Users.objects.get(id=kwargs['student_id'])
                first_label = f"{student.first_name} {student.last_name}"
            except Users.DoesNotExist:
                first_label = "Ученик"
        elif first_name == 'tutor_card' and kwargs.get('tutor_id'):
            try:
                tutor = Users.objects.get(id=kwargs['tutor_id'], role='tutor')
                first_label = f"{tutor.first_name} {tutor.last_name}"
            except Users.DoesNotExist:
                first_label = "Репетитор"
        elif first_name == 'group_card' and kwargs.get('group_id'):
            try:
                group = StudyGroups.objects.get(id=kwargs['group_id'])
                first_label = group.name
            except StudyGroups.DoesNotExist:
                first_label = "Группа"
        elif first_name == 'edit_group' and kwargs.get('group_id'):
            try:
                group = StudyGroups.objects.get(id=kwargs['group_id'])
                first_label = f"Редактирование: {group.name}"
            except StudyGroups.DoesNotExist:
                first_label = "Редактирование группы"
        elif first_name == 'homework_detail' and kwargs.get('hw_id'):
            try:
                hw = Homework.objects.get(id=kwargs['hw_id'])
                first_label = f"ДЗ: {hw.subject.name}"
            except Exception:
                first_label = "Задание"
        elif first_name == 'chat_thread' and kwargs.get('connection_id'):
            try:
                conn = ConnectionRequest.objects.select_related('tutor', 'student').get(id=kwargs['connection_id'])
                profile_id = getattr(request.user.profile, 'id', None)
                counterpart = conn.student if conn.tutor_id == profile_id else conn.tutor
                first_label = f"Чат с {counterpart.first_name} {counterpart.last_name}"
            except Exception:
                first_label = "Чат"
        else:
            first_label = first_name.replace('_', ' ').capitalize()
        chain[0] = (first_label, first_url, first_name)

    # Строим список крошек: от Главной к текущей (chain от текущей к корню)
    crumbs = []
    for i in range(len(chain) - 1, -1, -1):
        label, url, _ = chain[i]
        if label:
            crumbs.append({'name': label, 'url': url})

    # Последний элемент — текущая страница, ссылку не даём (уже в шаблоне last не ссылка)
    return {'auto_breadcrumbs': crumbs}
