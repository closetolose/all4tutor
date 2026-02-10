"""
URL configuration for tutor_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from core import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),

    # Авторизация
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('confirmations/', views.confirmations, name='confirmations'),
    path('confirmations/accept/<int:request_id>/', views.accept_request, name='accept_request'),
    path('confirmations/reject/<int:request_id>/', views.reject_request, name='reject_request'),

    # НОВЫЕ ПУТИ ДЛЯ СПИСКОВ
    path('my-students/', views.my_students, name='my_students'),
    path('my-tutors/', views.my_tutors, name='my_tutors'),
    path('add-lesson/', views.add_lesson, name='add_lesson'),
    path('add-student/', views.add_student, name='add_student'),
    path('lesson/edit/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),
    path('lesson/delete/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),

    path('group/edit/<int:group_id>/', views.edit_group, name='edit_group'),
    path('group/delete/<int:group_id>/', views.delete_group, name='delete_group'),

    path('student/remove/<int:connection_id>/', views.remove_student, name='remove_student'),
    path('add-group/', views.add_group, name='add_group'),
    path('lessons/bulk/', views.bulk_action_lessons, name='bulk_action'),
    path('toggle-pay/<int:attendance_id>/', views.toggle_attendance_pay, name='toggle_pay'),
    path('student/<int:student_id>/', views.student_card, name='student_card'),
    path('toggle-presence/<int:attendance_id>/', views.toggle_presence, name='toggle_presence'),
    path('my-files/', views.files_library, name='files_library'),
    path('files/edit/<int:file_id>/', views.edit_file, name='edit_file'),
    path('files/delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path('student/<int:student_id>/add-homework/', views.add_homework, name='add_homework'),
    path('lesson/<int:lesson_id>/download-materials/', views.download_lesson_materials, name='download_materials'),
    path('homework/edit/<int:hw_id>/', views.edit_homework, name='edit_homework'),
    path('homework/delete/<int:hw_id>/', views.delete_homework, name='delete_homework'),
    path('homework/toggle-status/<int:hw_id>/', views.toggle_homework_status, name='toggle_hw_status'),
    path('finances/', views.finances, name='finances'),
    path('homework/submit/<int:hw_id>/', views.submit_homework, name='submit_homework'),
    path('my-assignments/', views.my_assignments, name='my_assignments'),
    path('subjects/', views.my_subjects, name='my_subjects'),
    path('subjects/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('bulk-action/', views.bulk_action_lessons, name='bulk_action'),
    path('group-card/<int:group_id>/', views.group_card, name='group_card'),

    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='core/registration/password_reset_form.html',
             html_email_template_name='core/emails/password_reset_email.html',
             subject_template_name='core/emails/password_reset_subject.txt'
         ),
         name='password_reset'),


    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='core/registration/password_reset_done.html'),
         name='password_reset_done'),


    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='core/registration/password_reset_confirm.html'),
         name='password_reset_confirm'),


    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='core/registration/password_reset_complete.html'),
         name='password_reset_complete'),

    path('faq/', TemplateView.as_view(template_name='core/faq.html'), name='faq'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)