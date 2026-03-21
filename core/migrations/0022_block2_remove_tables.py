# Block 2: TutorStudentNote→ConnectionRequest, удаление GroupMembers, StudentPerformance, StudentBalance

from django.db import migrations, models


def migrate_tutor_notes(apps, schema_editor):
    """Перенос заметок из TutorStudentNote в ConnectionRequest."""
    TutorStudentNote = apps.get_model('core', 'TutorStudentNote')
    ConnectionRequest = apps.get_model('core', 'ConnectionRequest')
    for note in TutorStudentNote.objects.all():
        conn = ConnectionRequest.objects.filter(
            tutor=note.tutor, student=note.student,
            status__in=['confirmed', 'archived']
        ).first()
        if conn and note.text:
            conn.tutor_note = note.text
            conn.save()


def reverse_migrate_tutor_notes(apps, schema_editor):
    """Обратный перенос заметок (для отката)."""
    TutorStudentNote = apps.get_model('core', 'TutorStudentNote')
    ConnectionRequest = apps.get_model('core', 'ConnectionRequest')
    for conn in ConnectionRequest.objects.exclude(tutor_note__isnull=True).exclude(tutor_note=''):
        TutorStudentNote.objects.update_or_create(
            tutor=conn.tutor, student=conn.student,
            defaults={'text': conn.tutor_note}
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_block1_financial_and_is_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='connectionrequest',
            name='tutor_note',
            field=models.TextField(blank=True, null=True, verbose_name='Заметка репетитора об ученике'),
        ),
        migrations.RunPython(migrate_tutor_notes, reverse_migrate_tutor_notes),
        migrations.DeleteModel(name='TutorStudentNote'),
        migrations.SeparateDatabaseAndState(
            state_operations=[migrations.DeleteModel(name='GroupMembers')],
            database_operations=[
                migrations.RunSQL(
                    sql="DROP TABLE IF EXISTS group_members",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[migrations.DeleteModel(name='StudentPerformance')],
            database_operations=[
                migrations.RunSQL(
                    sql="DROP TABLE IF EXISTS core_studentperformance",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[migrations.DeleteModel(name='StudentBalance')],
            database_operations=[
                migrations.RunSQL(
                    sql="DROP TABLE IF EXISTS core_studentbalance",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
