import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_studygroups_is_archived'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupHomework',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(verbose_name='Описание задания')),
                ('deadline', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('files', models.ManyToManyField(blank=True, related_name='group_homework_files', to='core.fileslibrary')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='homework_assignments', to='core.studygroups')),
            ],
            options={
                'db_table': 'group_homework',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='homework',
            name='group_assignment',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='student_homeworks',
                to='core.grouphomework',
            ),
        ),
    ]
