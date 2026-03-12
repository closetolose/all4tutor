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
    path('tags/<int:tag_id>/rename/', views.rename_tag, name='rename_tag'),
    path('tags/<int:tag_id>/delete/', views.delete_tag, name='delete_tag'),
    path('student/<int:student_id>/add-homework/', views.add_homework, name='add_homework'),
    path('lesson/<int:lesson_id>/download-materials/', views.download_lesson_materials, name='download_materials'),
    path('homework/edit/<int:hw_id>/', views.edit_homework, name='edit_homework'),
    path('homework/delete/<int:hw_id>/', views.delete_homework, name='delete_homework'),
    path('homework/toggle-status/<int:hw_id>/', views.toggle_homework_status, name='toggle_hw_status'),
    path('finances/', views.finances, name='finances'),
    path('results/', views.results_page, name='results_page'),
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
    path('toggle-attendance-pay/<int:attendance_id>/', views.toggle_attendance_pay, name='toggle_attendance_pay'),
    path('transaction/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('load-more-lessons/', views.load_more_lessons, name='load_more_lessons'),
    path('logout-all/', views.logout_all_devices, name='logout_all_devices'),
    path('tutor-card/<int:tutor_id>/', views.tutor_card, name='tutor_card'),
    path('connection/<int:connection_id>/update-tutor-color/', views.update_tutor_color, name='update_tutor_color'),
    path('connection/<int:connection_id>/update-connection-tutor-color/', views.update_connection_tutor_color, name='update_connection_tutor_color'),
    path('group/<int:group_id>/update-group-color/', views.update_group_color, name='update_group_color'),
    path('subjects/edit/<int:subject_id>/', views.edit_subject, name='edit_subject'),
    path('students/archive-list/', views.archived_students, name='archived_students'),
    path('students/archive-action/<int:student_id>/', views.archive_student, name='archive_student'),
    path('students/restore/<int:student_id>/', views.restore_student, name='restore_student'),
    path('homework/<int:hw_id>/', views.homework_detail, name='homework_detail'),
    path('api/user-files/', views.api_get_user_files, name='api_get_user_files'),
    path('api/notifications/<int:notification_id>/read/', views.api_notification_mark_read, name='api_notification_mark_read'),
    path('load-more-files/', views.load_more_files, name='load_more_files'),
    path('payment-receipts/', views.payment_receipts, name='payment_receipts'),
    path('payment-receipts/submit/', views.submit_receipt, name='submit_receipt'),
    path('payment-receipts/<int:receipt_id>/approve/', views.approve_receipt, name='approve_receipt'),
    path('payment-receipts/<int:receipt_id>/reject/', views.reject_receipt, name='reject_receipt'),
    path('download/file/<int:file_id>/', views.download_library_file, name='download_library_file'),
    path('export/lessons/', views.export_lessons_csv, name='export_lessons_csv'),
    path('homework/response/delete/<int:response_id>/', views.delete_homework_response, name='delete_homework_response'),
    path('connection/<int:connection_id>/request-unlink/', views.request_unlink, name='request_unlink'),

    path('dashboard/admin/', views.dashboard_admin_index, name='dashboard_admin_index'),
    path('dashboard/admin/users/', views.dashboard_admin_users, name='dashboard_admin_users'),
    path('dashboard/admin/users/<int:user_id>/toggle-active/', views.dashboard_admin_toggle_active, name='dashboard_admin_toggle_active'),
    path('dashboard/admin/users/<int:user_id>/delete/', views.dashboard_admin_delete_user, name='dashboard_admin_delete_user'),
    path('dashboard/admin/unlink-requests/', views.dashboard_admin_unlink_requests, name='dashboard_admin_unlink_requests'),
    path('dashboard/admin/unlink-requests/<int:pk>/approve/', views.dashboard_admin_unlink_approve, name='dashboard_admin_unlink_approve'),
    path('dashboard/admin/unlink-requests/<int:pk>/reject/', views.dashboard_admin_unlink_reject, name='dashboard_admin_unlink_reject'),

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
    path('update-timezone/', views.update_timezone, name='update_timezone'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
