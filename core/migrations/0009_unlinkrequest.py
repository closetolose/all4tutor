# Generated for unlink request (student requests to unlink from tutor)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_paymentreceipt'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UnlinkRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Ожидает рассмотрения'), ('approved', 'Одобрено'), ('rejected', 'Отклонено')], default='pending', max_length=10)),
                ('created_at', models.DateTimeField(default=timezone.now)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unlink_requests_reviewed', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlink_requests_sent', to='core.users')),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlink_requests_received', to='core.users')),
            ],
            options={
                'db_table': 'unlink_requests',
                'ordering': ['-created_at'],
            },
        ),
    ]
