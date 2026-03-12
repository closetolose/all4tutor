# Generated manually for overdue notifications epic

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0010_testresult'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=255)),
                ('link', models.CharField(blank=True, max_length=500, null=True)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=timezone.now)),
                ('type', models.CharField(choices=[('warning', 'Предупреждение'), ('info', 'Информация')], default='warning', max_length=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='homework',
            name='is_overdue_notified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='homework',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Задано'),
                    ('submitted', 'На проверке'),
                    ('revision', 'Доработать'),
                    ('completed', 'Выполнено'),
                    ('overdue', 'Просрочено'),
                ],
                default='pending',
                max_length=15,
            ),
        ),
    ]
