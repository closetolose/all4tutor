# Generated for TestResult (analytics module)

from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_unlinkrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_score', models.DecimalField(decimal_places=2, help_text='Максимальный балл', max_digits=8)),
                ('score', models.DecimalField(decimal_places=2, help_text='Полученный балл', max_digits=8)),
                ('date', models.DateField(default=timezone.now)),
                ('comment', models.TextField(blank=True, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_results_as_student', to='core.users')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_results', to='core.subjects')),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_results_as_tutor', to='core.users')),
            ],
            options={
                'db_table': 'test_results',
                'ordering': ['-date'],
            },
        ),
    ]
