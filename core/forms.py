from django import forms
from django.contrib.auth.models import User
from .models import Users, Lessons, ConnectionRequest, TutorSubjects, Subjects, StudyGroups, FilesLibrary
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from datetime import timedelta

class AddSubjectForm(forms.Form):
    subject_name = forms.CharField(
        max_length=100,
        label="Название предмета",
        widget=forms.TextInput(attrs={'placeholder': 'Напр: Квантовая физика'})
    )





class RegistrationForm(forms.ModelForm):
    # Поля паролей (не сохраняются в модель напрямую, хешируются во view)
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'placeholder': 'Придумайте пароль'})
    )
    password_confirm = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите пароль'})
    )

    # Роль (выбор ученик/репетитор)
    ROLE_CHOICES = [
        ('tutor', 'Я репетитор'),
        ('student', 'Я ученик'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Кто вы?")

    class Meta:
        model = User
        # В системную таблицу пишем только логин и email
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Логин'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email (для входа)'}),
        }

    def clean_password_confirm(self):
        p1 = self.cleaned_data.get('password')
        p2 = self.cleaned_data.get('password_confirm')
        if p1:
            if p1 and p2 and p1 != p2:
                raise forms.ValidationError("Пароли не совпадают")
            try:
                validate_password(p1)
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
            return p2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 4:
            raise ValidationError("Логин должен содержать не менее 4 символов.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с такой почтой уже зарегистрирован.")
        return email

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Users
        # Твои поля профиля (включая address и contact)
        fields = ['last_name', 'first_name', 'patronymic', 'address', 'contact',"telegram_id","school_class","parent_name","parent_phone","timezone"]
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'patronymic': 'Отчество',
            'address': 'Адрес/Город',
            'contact': 'Контактные данные (телефон/TG)',
            'telegram_id': 'Telegram ID',
        }
        widgets = {
            'last_name': forms.TextInput(attrs={'placeholder': 'Введите фамилию'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Введите имя'}),
            'patronymic': forms.TextInput(attrs={'placeholder': 'Введите отчество (если есть)'}),
            'address': forms.TextInput(attrs={'placeholder': 'Напр: Москва, ул. Ленина 1'}),
            'contact': forms.TextInput(attrs={'placeholder': '+7 (xxx) xxx-xx-xx'}),
            'telegram_id': forms.TextInput(attrs={'placeholder': 'Напр: 123456789','title': 'Ваш цифровой ID в Telegram'}),
            'school_class': forms.TextInput(attrs={'class': 'm-input', 'placeholder': 'Например: 9-Б'}),
            'parent_name': forms.TextInput(attrs={'class': 'm-input', 'placeholder': 'Иван Иванович'}),
            'parent_phone': forms.TextInput(attrs={'class': 'm-input', 'placeholder': '+7 ...'}),
            'timezone': forms.Select(attrs={'class': 'form-control', 'id': 'tz-selector'})
        }




# ... (Твои другие формы: RegistrationForm, StudyGroupForm и т.д. оставь как есть) ...

class AddLessonForm(forms.ModelForm):
    # --- 1. Основные настройки ---

    start_time = forms.DateTimeField(
        label="Начало занятия",
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],  # Форматы, которые понимает сервер
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'tg-native-input'},
            format='%Y-%m-%dT%H:%M'  # Формат, который понимает браузер
        )
    )
    duration = forms.IntegerField(
        initial=60,
        label="Длительность (мин)",
        widget=forms.NumberInput(attrs={'class': 'custom-input'})
    )
    materials = forms.ModelMultipleChoiceField(
        queryset=FilesLibrary.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),  # Или SelectMultiple для экономии места
        label="Прикрепить материалы"
    )

    # Переключатель типа (Индивидуально / Группа)
    lesson_type = forms.ChoiceField(
        choices=[('individual', 'Индивидуально'), ('group', 'Группа')],
        widget=forms.RadioSelect(attrs={'class': 'lesson-type-switch'}),
        initial='individual',
        label="Тип занятия"
    )

    # --- 2. Настройки повторения (Планировщик) ---
    is_recurring = forms.BooleanField(
        required=False,
        label="Включить повторение",
        widget=forms.CheckboxInput(attrs={'class': 'toggle-checkbox'})
    )

    # Вариант А: Повторять N недель
    repeat_count = forms.IntegerField(
        required=False,
        initial=4,
        min_value=1,
        max_value=50,
        label="Количество недель",
        widget=forms.NumberInput(attrs={'class': 'custom-input'})
    )

    # Вариант Б: Повторять ДО конкретной даты
    repeat_until = forms.DateField(
        required=False,
        label="Повторять до даты",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'custom-input'})
    )

    # Выбор дней недели (0=Пн, 6=Вс)
    WEEKDAYS = [
        ('0', 'Пн'), ('1', 'Вт'), ('2', 'Ср'), ('3', 'Чт'),
        ('4', 'Пт'), ('5', 'Сб'), ('6', 'Вс')
    ]
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAYS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'weekday-checkbox'}),
        required=False,
        label="Дни недели"
    )

    class Meta:
        model = Lessons
        # Перечисляем ВСЕ поля в порядке отображения
        fields = [
            'lesson_type',
            'is_recurring', 'repeat_count', 'repeat_until', 'weekdays',  # Блок планировщика
            'student', 'group',
            'subject',
            'start_time', 'duration',
            'format', 'location',
            'notes', 'homework',
            "price", 'materials'
        ]
        widgets = {

            'student': forms.Select(attrs={'class': 'custom-input'}),
            'group': forms.Select(attrs={'class': 'custom-input'}),
            'subject': forms.Select(attrs={'class': 'custom-input'}),
            'format': forms.Select(choices=[('online', 'Онлайн'), ('offline', 'Очно')],
                                   attrs={'class': 'custom-input'}),
            'location': forms.TextInput(attrs={'class': 'custom-input', 'placeholder': 'Ссылка на Zoom или Адрес'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'custom-input', 'placeholder': 'Личные заметки...'}),
            'homework': forms.Textarea(
                attrs={'rows': 2, 'class': 'custom-input', 'placeholder': 'ДЗ к этому уроку...'}),
            'price': forms.NumberInput(attrs={'class': 'custom-input', 'id': 'id_price'}),
        }
        labels = {
            'student': 'Ученик',
            'group': 'Группа',
            'subject': 'Предмет',
            'start_time': 'Начало занятия',
            'format': 'Формат',
            'location': 'Место / Ссылка',
        }



    def __init__(self, *args, **kwargs):
        # Извлекаем текущего репетитора, чтобы отфильтровать списки
        tutor = kwargs.pop('tutor', None)
        super().__init__(*args, **kwargs)

        self.tutor = tutor

        if self.tutor:
            # 1. Показываем только тех учеников, которые подтвердили связь с этим репетитором
            confirmed_ids = ConnectionRequest.objects.filter(
                tutor=tutor, status='confirmed'
            ).values_list('student_id', flat=True)
            self.fields['student'].queryset = Users.objects.filter(id__in=confirmed_ids)

            # 2. Показываем только группы этого репетитора
            self.fields['group'].queryset = StudyGroups.objects.filter(tutor=tutor)

            # 3. Показываем только предметы, которые ведет этот репетитор
            subject_ids = TutorSubjects.objects.filter(tutor=tutor).values_list('subject_id', flat=True)
            self.fields['subject'].queryset = Subjects.objects.filter(id__in=subject_ids)

            # Делаем поля необязательными на уровне формы (валидацию мы делаем вручную во view)
            # Это нужно, чтобы форма не ругалась "Заполните ученика", если выбрана "Группа"
            self.fields['student'].required = False
            self.fields['group'].required = False
            self.fields['notes'].required = False
            self.fields['homework'].required = False
            self.fields['location'].required = False
            self.fields['materials'].queryset = FilesLibrary.objects.filter(tutor=tutor)

    def clean(self):
        # 1. Вызываем базовую очистку один раз
        cleaned_data = super().clean()

        # Извлекаем все нужные поля
        lesson_type = cleaned_data.get('lesson_type')
        student = cleaned_data.get('student')
        group = cleaned_data.get('group')
        start_time = cleaned_data.get('start_time')
        duration = cleaned_data.get('duration')
        tutor = self.tutor

        # --- БЛОК 1: Валидация участников ---
        if lesson_type == 'individual' and not student:
            self.add_error('student', "Выберите ученика для индивидуального занятия")

        if lesson_type == 'group' and not group:
            self.add_error('group', "Выберите группу для группового занятия")

        # --- БЛОК 2: Валидация пересечений (коллизий) ---
        if start_time and duration and tutor:
            from datetime import timedelta  # Не забудь импорт в начале файла
            end_time = start_time + timedelta(minutes=duration)

            overlapping_lessons = Lessons.objects.filter(
                tutor=tutor,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            # Исключаем текущий урок при редактировании
            if self.instance and self.instance.pk:
                overlapping_lessons = overlapping_lessons.exclude(pk=self.instance.pk)

            if overlapping_lessons.exists():
                collision = overlapping_lessons.first()
                raise ValidationError(
                    f"Это время занято! Урок по предмету '{collision.subject}' "
                    f"идет с {collision.start_time.strftime('%H:%M')} до {collision.end_time.strftime('%H:%M')}"
                )

        # Возвращаем очищенные данные в конце
        return cleaned_data

class StudyGroupForm(forms.ModelForm):
    class Meta:
        model = StudyGroups
        # 1. ДОБАВЛЯЕМ 'subject' В СПИСОК ПОЛЕЙ
        fields = ['name', 'subject', 'students']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'custom-input', 'placeholder': 'Название (например, 9Б)'}),
            'students': forms.CheckboxSelectMultiple(),
            # 2. Добавляем стиль для выпадающего списка
            'subject': forms.Select(attrs={'class': 'custom-input'}),
        }
        labels = {
            'name': 'Название',
            'subject': 'Предмет',
            'students': 'Ученики',
        }

    def __init__(self, *args, **kwargs):
        tutor = kwargs.pop('tutor', None)
        super().__init__(*args, **kwargs)
        if tutor:
            # Фильтруем учеников
            confirmed_ids = ConnectionRequest.objects.filter(
                tutor=tutor, status='confirmed'
            ).values_list('student_id', flat=True)
            self.fields['students'].queryset = Users.objects.filter(id__in=confirmed_ids)

            # 3. ФИЛЬТРУЕМ ПРЕДМЕТЫ (Показываем только предметы этого репетитора)
            subject_ids = TutorSubjects.objects.filter(tutor=tutor).values_list('subject_id', flat=True)
            self.fields['subject'].queryset = Subjects.objects.filter(id__in=subject_ids)


