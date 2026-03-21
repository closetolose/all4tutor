from datetime import timedelta

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import (
    ConnectionRequest, FilesLibrary, Lessons, Subjects, StudyGroups,
    Profile,
)


class AddSubjectForm(forms.Form):
    subject_name = forms.CharField(
        max_length=100,
        label="Название предмета",
        widget=forms.TextInput(attrs={'placeholder': 'Напр: Квантовая физика'})
    )


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'placeholder': 'Придумайте пароль'})
    )
    password_confirm = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите пароль'})
    )

    ROLE_CHOICES = [
        ('tutor', 'Я репетитор'),
        ('student', 'Я ученик'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Кто вы?")

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Логин'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email (для входа)'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean_password_confirm(self):
        p1 = self.cleaned_data.get('password')  # Берем уже очищенный пароль
        p2 = self.cleaned_data.get('password_confirm')

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают")

        # Всегда возвращаем p2, чтобы значение оставалось в cleaned_data
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
        model = Profile
        fields = [
            'last_name', 'first_name', 'patronymic', 'address', 'contact',
            'telegram_id', 'school_class', 'parent_name', 'parent_phone', 'timezone',
        ]
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'patronymic': 'Отчество',
            'address': 'Адрес/Город',
            'contact': 'Контактные данные (телефон/TG)',
            'telegram_id': 'Telegram ID',
        }
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите фамилию'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите имя'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите отчество (если есть)'}),
            'address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Напр: Москва, ул. Ленина 1'}),
            'contact': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+7 (xxx) xxx-xx-xx'}),
            'telegram_id': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Напр: 123456789',
                'title': 'Ваш цифровой ID в Telegram',
            }),
            'school_class': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например: 9-Б'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Иван Иванович'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+7 ...'}),
            'timezone': forms.Select(attrs={'class': 'form-select', 'id': 'tz-selector'}),
        }


class AddLessonForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label="Начало занятия",
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'tg-native-input'},
            format='%Y-%m-%dT%H:%M'
        )
    )
    duration = forms.IntegerField(
        initial=60,
        label="Длительность (мин)",
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '45 мин'})
    )
    materials = forms.ModelMultipleChoiceField(
        queryset=FilesLibrary.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label="Прикрепить материалы"
    )

    lesson_type = forms.ChoiceField(
        choices=[('individual', 'Индивидуально'), ('group', 'Группа')],
        widget=forms.RadioSelect(attrs={'class': 'lesson-type-switch'}),
        initial='individual',
        label="Тип занятия"
    )

    is_recurring = forms.BooleanField(
        required=False,
        label="Включить повторение",
        widget=forms.CheckboxInput(attrs={'class': 'toggle-checkbox'})
    )

    repeat_count = forms.IntegerField(
        required=False,
        initial=4,
        min_value=1,
        max_value=50,
        label="Количество недель",
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '4 нед.'})
    )

    repeat_until = forms.DateField(
        required=False,
        label="Повторять до даты",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )

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
        fields = [
            'lesson_type',
            'is_recurring', 'repeat_count', 'repeat_until', 'weekdays',
            'student', 'group',
            'subject',
            'start_time', 'duration',
            'format', 'location',
            'notes', 'homework',
            'price', 'materials',
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'format': forms.Select(
                choices=[('online', 'Онлайн'), ('offline', 'Очно')],
                attrs={'class': 'form-select'},
            ),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ссылка на Zoom или Адрес',
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2, 'class': 'form-textarea',
                'placeholder': 'Личные заметки...',
            }),
            'homework': forms.Textarea(attrs={
                'rows': 2, 'class': 'form-textarea',
                'placeholder': 'ДЗ к этому уроку...',
            }),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'id': 'id_price', 'placeholder': '0 ₽'}),
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
        tutor = kwargs.pop('tutor', None)
        super().__init__(*args, **kwargs)

        self.tutor = tutor

        if self.tutor:
            confirmed_ids = ConnectionRequest.objects.filter(
                tutor=tutor, status='confirmed'
            ).values_list('student_id', flat=True)
            self.fields['student'].queryset = Profile.objects.filter(id__in=confirmed_ids)

            self.fields['group'].queryset = StudyGroups.objects.filter(tutor=tutor, is_archived=False)

            self.fields['subject'].queryset = Subjects.objects.filter(tutor=tutor)

            self.fields['student'].required = False
            self.fields['group'].required = False
            self.fields['notes'].required = False
            self.fields['homework'].required = False
            self.fields['location'].required = False
            self.fields['materials'].queryset = FilesLibrary.objects.filter(tutor=tutor)

    def clean(self):
        cleaned_data = super().clean()

        lesson_type = cleaned_data.get('lesson_type')
        student = cleaned_data.get('student')
        group = cleaned_data.get('group')
        start_time = cleaned_data.get('start_time')
        duration = cleaned_data.get('duration')
        tutor = self.tutor

        if lesson_type == 'individual' and not student:
            self.add_error('student', "Выберите ученика для индивидуального занятия")

        if lesson_type == 'group' and not group:
            self.add_error('group', "Выберите группу для группового занятия")

        # Коллизия: при групповом уроке предмет и репетитор должны совпадать с группой
        subject = cleaned_data.get('subject')
        if group and subject and (group.subject_id != subject.id or group.tutor_id != tutor.id):
            self.add_error('group', "Предмет урока должен совпадать с предметом группы.")

        if start_time and duration and tutor:
            end_time = start_time + timedelta(minutes=duration)

            overlapping_lessons = Lessons.objects.filter(
                tutor=tutor,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            if self.instance and self.instance.pk:
                overlapping_lessons = overlapping_lessons.exclude(pk=self.instance.pk)

            if overlapping_lessons.exists():
                collision = overlapping_lessons.first()
                raise ValidationError(
                    f"Это время занято! Урок по предмету '{collision.subject}' "
                    f"идет с {collision.start_time.strftime('%H:%M')} до {collision.end_time.strftime('%H:%M')}"
                )

        return cleaned_data


class StudyGroupForm(forms.ModelForm):
    class Meta:
        model = StudyGroups
        fields = ['name', 'subject', 'students']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название (например, 9Б)'}),
            'students': forms.CheckboxSelectMultiple(),
            'subject': forms.Select(attrs={'class': 'form-select'}),
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
            confirmed_ids = ConnectionRequest.objects.filter(
                tutor=tutor, status='confirmed'
            ).values_list('student_id', flat=True)
            self.fields['students'].queryset = Profile.objects.filter(id__in=confirmed_ids)

            self.fields['subject'].queryset = Subjects.objects.filter(tutor=tutor)
