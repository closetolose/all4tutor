# UnlinkRequest → ConnectionRequest: перенос полей заявки на открепление в ConnectionRequest

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_unlink_to_connection(apps, schema_editor):
    """Перенос pending заявок из UnlinkRequest в ConnectionRequest."""
    UnlinkRequest = apps.get_model('core', 'UnlinkRequest')
    ConnectionRequest = apps.get_model('core', 'ConnectionRequest')
    for ur in UnlinkRequest.objects.filter(status='pending'):
        conn = ConnectionRequest.objects.filter(
            student=ur.student, tutor=ur.tutor, status='confirmed'
        ).first()
        if conn:
            conn.unlink_requested = True
            conn.unlink_reason = ur.reason or ''
            conn.unlink_requested_at = ur.created_at
            conn.save(update_fields=['unlink_requested', 'unlink_reason', 'unlink_requested_at'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_block4_add_indexes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='connectionrequest',
            name='unlink_requested',
            field=models.BooleanField(default=False, verbose_name='Заявка на открепление'),
        ),
        migrations.AddField(
            model_name='connectionrequest',
            name='unlink_reason',
            field=models.TextField(blank=True, null=True, verbose_name='Причина открепления'),
        ),
        migrations.AddField(
            model_name='connectionrequest',
            name='unlink_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='connectionrequest',
            name='unlink_reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='connectionrequest',
            name='unlink_reviewed_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='unlink_reviews',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(migrate_unlink_to_connection, noop),
        migrations.DeleteModel(name='UnlinkRequest'),
    ]
