from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from core import views

urlpatterns = [
    path('secretplace/', admin.site.urls),
    path('', views.index, name='index'),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('confirmations/', views.confirmations, name='confirmations'),
    path('confirmations/accept/<int:request_id>/', views.accept_request, name='accept_request'),
    path('confirmations/reject/<int:request_id>/', views.reject_request, name='reject_request'),

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
    path('group-card/<int:group_id>/', views.group_card, name='group_card'),
    path('homework/download-all/<int:hw_id>/', views.download_homework_all, name='download_homework_all'),
    path('lesson/<int:lesson_id>/materials/', views.download_lesson_materials, name='download_lesson_materials'),
    path('homework/<int:hw_id>/files/', views.download_homework_all, name='download_homework_all'),
    path('homework/response/<int:response_id>/download/', views.download_homework_response, name='download_homework_response'),
    path('toggle-presence/<int:attendance_id>/', views.toggle_presence, name='toggle_presence'),
    path('toggle-attendance-pay/<int:attendance_id>/', views.toggle_attendance_pay, name='toggle_attendance_pay'),
    path('load-more-lessons/', views.load_more_lessons, name='load_more_lessons'),
    path('logout-all/', views.logout_all_devices, name='logout_all_devices'),
    path('tutor-card/<int:tutor_id>/', views.tutor_card, name='tutor_card'),
    path('subjects/edit/<int:subject_id>/', views.edit_subject, name='edit_subject'),
    path('students/archive-list/', views.archived_students, name='archived_students'),
    path('students/archive-action/<int:student_id>/', views.archive_student, name='archive_student'),
    path('students/restore/<int:student_id>/', views.restore_student, name='restore_student'),



    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='core/registration/password_reset_form.html',
             html_email_template_name='core/emails/password_reset_email.html',
             subject_template_name='core/emails/password_reset_subject.txt',
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='core/registration/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='core/registration/password_reset_confirm.html',
         ),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='core/registration/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    path('faq/', views.faq, name='faq'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
