# Block 4: Добавление индексов для производительности

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_block3_testresult_homeworkresponse'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='lessons',
            index=models.Index(fields=['tutor', 'start_time'], name='lessons_tutor_start'),
        ),
        migrations.AddIndex(
            model_name='lessons',
            index=models.Index(fields=['student', 'start_time'], name='lessons_student_start'),
        ),
        migrations.AddIndex(
            model_name='connectionrequest',
            index=models.Index(fields=['tutor', 'status'], name='conn_req_tutor_status'),
        ),
        migrations.AddIndex(
            model_name='connectionrequest',
            index=models.Index(fields=['student', 'status'], name='conn_req_student_status'),
        ),
        migrations.AddIndex(
            model_name='homework',
            index=models.Index(fields=['student', 'status'], name='homework_student_status'),
        ),
        migrations.AddIndex(
            model_name='homework',
            index=models.Index(fields=['tutor', 'deadline'], name='homework_tutor_deadline'),
        ),
        migrations.AddIndex(
            model_name='chatmessage',
            index=models.Index(fields=['connection', 'is_read'], name='chat_conn_is_read'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='notif_user_is_read'),
        ),
    ]
