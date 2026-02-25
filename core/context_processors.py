from django.utils import timezone

from .models import Lessons, Users
from django.urls import resolve, reverse,NoReverseMatch
from django.db.models import Q

def next_lesson_processor(request):
    if not request.user.is_authenticated:
        return {'next_lesson': None}

    try:
        user_profile = request.user.profile
        now = timezone.now()

        if user_profile.role == 'tutor':
            # Логика для репетитора
            next_lesson = Lessons.objects.filter(
                tutor=user_profile,
                start_time__gt=now
            ).order_by('start_time').first()
        else:
            # Логика для ученика (индивидуально или группа)
            next_lesson = Lessons.objects.filter(
                Q(student=user_profile) | Q(group__students=user_profile),
                start_time__gt=now
            ).distinct().order_by('start_time').first()

        return {'next_lesson': next_lesson}
    except Exception:
        return {'next_lesson': None}


def breadcrumbs(request):
    # Если пользователь не залогинен, крошки не нужны
    if not request.user.is_authenticated:
        return {'auto_breadcrumbs': []}

    # Получаем сегменты пути, игнорируя пустые строки: /student/5/ -> ['student', '5']
    path_segments = [s for s in request.path.split('/') if s]
    crumbs = []

    # 1. Всегда начинаем с Главной
    crumbs.append({'name': 'Главная', 'url': reverse('index')})

    # 2. Словарь "красивых" имен и ПРАВИЛЬНЫХ ссылок.
    # Если URL содержит 'student' или 'student-card', ссылка будет вести на 'my_students'
    TITLES = {
        'my-students': {'name': 'Мои ученики', 'url_name': 'my_students'},
        'student': {'name': 'Мои ученики', 'url_name': 'my_students'},
        'student-card': {'name': 'Мои ученики', 'url_name': 'my_students'},
        'finances': {'name': 'Финансы', 'url_name': 'finances'},
        'my-assignments': {'name': 'Мои задания', 'url_name': 'my_assignments'},
        'my-files': {'name': 'Мои файлы', 'url_name': 'files_library'},
        'my-subjects': {'name': 'Мои предметы', 'url_name': 'my_subjects'},
        'edit-profile': {'name': 'Профиль', 'url_name': 'edit_profile'},
        'subjects': {'name': 'Мои предметы', 'url_name': 'my_subjects'},
        'faq': {'name': 'FAQ', 'url_name': 'faq'},
        'confirmations': {'name': 'Подтверждения', 'url_name': 'confirmations'},
        'my-tutors': {'name': 'Мои репетиторы', 'url_name': 'my_tutors'},
        'tutor-card': {'name': 'Мои репетиторы', 'url_name': 'my_tutors'},
        'homework': {'name': 'Мои задания', 'url_name': 'my_assignments'},

    }

    accumulated_url = ''
    for i, segment in enumerate(path_segments):
        accumulated_url += f'/{segment}/'

        # Случай А: Это ID (цифра) после сегмента, связанного с карточкой ученика
        if segment.isdigit() and i > 0:
            prev_segment = path_segments[i - 1]

            # Обработка ученика (уже была у тебя)
            if prev_segment in ['student', 'student-card']:
                try:
                    student = Users.objects.get(id=segment)
                    name = f"{student.first_name} {student.last_name}"
                except Users.DoesNotExist:
                    name = "Ученик"

            # НОВОЕ: Обработка репетитора
            elif prev_segment == 'tutor-card':
                try:
                    # Ищем репетитора в модели Users
                    tutor = Users.objects.get(id=segment, role='tutor')
                    name = f"{tutor.first_name} {tutor.last_name}"
                except Users.DoesNotExist:
                    name = "Репетитор"
            elif prev_segment == 'homework':
                try:
                    # Импортируй модель Homework внутри функции или в начале файла
                    from .models import Homework
                    hw = Homework.objects.get(id=segment)
                    # Отображаем предмет, по которому задано ДЗ
                    name = f"ДЗ: {hw.subject.name}"
                except Exception:
                    name = "Задание"

            else:
                name = segment  # Если это другой ID (например, страница пагинации)

            crumbs.append({'name': name, 'url': accumulated_url})

        # Случай Б: Сегмент описан в нашем словаре TITLES
        elif segment in TITLES:
            mapping = TITLES[segment]
            try:
                # Пытаемся получить URL через reverse по имени из словаря
                target_url = reverse(mapping['url_name'])
            except NoReverseMatch:
                target_url = accumulated_url

            # Проверяем, нет ли уже такого названия в цепочке (защита от дублей)
            if not any(c['name'] == mapping['name'] for c in crumbs):
                crumbs.append({'name': mapping['name'], 'url': target_url})

        # Случай В: Обычные текстовые сегменты (запасной вариант)
        else:
            name = segment.replace('-', ' ').replace('_', ' ').capitalize()
            crumbs.append({'name': name, 'url': accumulated_url})

    return {'auto_breadcrumbs': crumbs}


