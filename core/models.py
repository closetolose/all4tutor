# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.conf import settings
from django.utils import timezone
import pytz
from decimal import Decimal
import os
from django.utils import timezone

class Users(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile',db_column="user_id")
    id = models.AutoField(primary_key=True)
    ROLE_CHOICES = [
        ('tutor', 'Репетитор'),
        ('student', 'Ученик'),
        ('parent', 'Родитель'),
    ]
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=7, choices=ROLE_CHOICES)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    telegram_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Telegram")
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC',
        verbose_name="Часовой пояс"
    )
    school_class = models.CharField(max_length=20, verbose_name="Класс", blank=True, null=True)
    parent_name = models.CharField(max_length=255, verbose_name="Имя Отчество родителя", blank=True, null=True)
    parent_phone = models.CharField(max_length=20, verbose_name="Контакты родителя", blank=True, null=True)
    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class FilesLibrary(models.Model):
    tutor = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='materials')
    # Добавляем FileField. null=True поможет избежать ошибок при миграции
    file = models.FileField(upload_to='tutor_materials/%Y/%m/%d/', null=True, blank=True)
    file_name = models.CharField(max_length=255)
    upload_date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'files_library'

    def get_extension(self):
        # Метод для определения типа файла (pdf, docx, video)
        if not self.file: return ""
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()

class GroupMembers(models.Model):
    group = models.ForeignKey('StudyGroups', models.CASCADE)
    student = models.ForeignKey('Users', models.CASCADE)


    class Meta:
        db_table = 'group_members'


class LessonAttendance(models.Model):
    lesson = models.ForeignKey('Lessons', models.CASCADE, related_name='attendances')
    student = models.ForeignKey('Users', models.CASCADE)
    is_paid = models.BooleanField(default=False)
    was_present = models.BooleanField(default=False)

    class Meta:
        db_table = 'lesson_attendance'
        unique_together = ('lesson', 'student')

class StudyGroups(models.Model):
    name = models.CharField(max_length=100)
    tutor = models.ForeignKey('Users', models.CASCADE)
    subject = models.ForeignKey('Subjects', models.CASCADE)
    students = models.ManyToManyField('Users', related_name='study_groups', blank=True)


    class Meta:
        db_table = 'study_groups'

    def __str__(self):
        return f"Группа: {self.name}"


class Lessons(models.Model):
    tutor = models.ForeignKey('Users', models.CASCADE)
    subject = models.ForeignKey('Subjects', models.CASCADE)
    student = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='lessons_student_set', blank=True,null=True)
    group = models.ForeignKey(StudyGroups, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Группа")
    notes = models.TextField(blank=True, null = True,verbose_name="Заметки")
    homework = models.TextField(blank=True,null = True,verbose_name="Домашнее задание")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.IntegerField(default=60, verbose_name="Длительность (мин)")
    format = models.CharField(max_length=12)
    location = models.TextField(blank=True, null=True)
    is_paid = models.IntegerField(blank=True, null=True,default=0)
    series_id = models.UUIDField(default=None,null=True,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    materials = models.ManyToManyField('FilesLibrary', blank=True, related_name='lessons_materials')
    reminder_sent = models.BooleanField(default=False)


    class Meta:
        db_table = 'lessons'


class ParentStudentLinks(models.Model):
    parent = models.ForeignKey('Users', models.CASCADE)
    student = models.ForeignKey('Users', models.CASCADE, related_name='parentstudentlinks_student_set')

    class Meta:
        db_table = 'parent_student_links'


class Results(models.Model):
    task = models.ForeignKey('Tasks', models.CASCADE)
    student = models.ForeignKey('Users', models.CASCADE)
    answer_url = models.CharField(max_length=255, blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'results'


class StudentBalances(models.Model):
    student = models.OneToOneField('Users', models.CASCADE, primary_key=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'student_balances'




class Subjects(models.Model):
    name = models.CharField(unique=True, max_length=100)
    tutor = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='subjects')

    class Meta:
        db_table = 'subjects'

    def __str__(self):
        return self.name


class TaskAssignments(models.Model):
    task = models.ForeignKey('Tasks', models.CASCADE)
    group = models.ForeignKey(StudyGroups, models.CASCADE, blank=True, null=True)
    student = models.ForeignKey('Users', models.CASCADE, blank=True, null=True)
    deadline = models.DateTimeField()

    class Meta:
        db_table = 'task_assignments'


class Tasks(models.Model):
    tutor = models.ForeignKey('Users', models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.ForeignKey(FilesLibrary, models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'tasks'


class Transaction(models.Model):
    TYPES = [('deposit', 'Пополнение'), ('withdrawal', 'Списание')]
    student = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='transactions')
    tutor = models.ForeignKey('Users', on_delete=models.CASCADE)
    attendance = models.ForeignKey('LessonAttendance', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPES)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'student_transactions'
        ordering = ['-date']


class TutorStudentLinks(models.Model):
    tutor = models.ForeignKey('Users', models.CASCADE)
    student = models.ForeignKey('Users', models.CASCADE, related_name='tutorstudentlinks_student_set')
    subject = models.ForeignKey(Subjects, models.CASCADE)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'tutor_student_links'


class TutorSubjects(models.Model):
    tutor = models.ForeignKey('Users', models.CASCADE,db_column='tutor_id')
    subject = models.ForeignKey(Subjects, models.CASCADE,db_column='subject_id')

    class Meta:
        managed = True
        db_table = 'tutor_subjects'
        unique_together = (('tutor', 'subject'),)


class ConnectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждено'),
        ('rejected', 'Отклонено'),
    ]

    tutor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='sent_requests')
    student = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='received_requests')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'connection_requests'

class StudentTariff(models.Model):
    tutor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='tutor_tariffs')
    student = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(StudyGroups, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        # У одного репетитора для одного ученика по одному предмету — одна цена
        unique_together = ('tutor', 'student', 'subject')

class StudentPerformance(models.Model):
    TYPE_CHOICES = [('hw', 'Домашняя работа'), ('test', 'Контрольная работа')]
    student = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='performance')
    lesson = models.ForeignKey('Lessons', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    score = models.IntegerField(help_text="Оценка или процент выполнения")
    comment = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)


class Homework(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Задано'),
        ('submitted', 'На проверке'),
        ('revision', 'Доработать'),
        ('completed', 'Выполнено'),
    ]

    tutor = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='assigned_homework')
    student = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='student_homework')
    subject = models.ForeignKey('Subjects', on_delete=models.CASCADE)

    description = models.TextField(verbose_name="Описание задания")
    files = models.ManyToManyField('FilesLibrary', blank=True, related_name='homework_files')

    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    tutor_comment = models.TextField(verbose_name="Комментарий репетитора", null=True, blank=True)

    class Meta:
        db_table = 'homework'
        ordering = ['-created_at']

class HomeworkResponse(models.Model):
    homework = models.ForeignKey('Homework', on_delete=models.CASCADE, related_name='responses')
    file = models.FileField(upload_to='student_responses/')
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ответ от {self.homework.student} на {self.homework.subject}"


class TutorStudentNote(models.Model):
    tutor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notes_created')
    student = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notes_about_me')
    text = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tutor', 'student')


