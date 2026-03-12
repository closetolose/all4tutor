# Generated manually for color indicator feature

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_connectionrequest_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='connectionrequest',
            name='color_hex',
            field=models.CharField(blank=True, max_length=7, null=True),
        ),
        migrations.CreateModel(
            name='UserGroupColor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color_hex', models.CharField(blank=True, max_length=7, null=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_colors', to='core.studygroups')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_colors', to='core.users')),
            ],
            options={
                'db_table': 'user_group_colors',
                'unique_together': {('user', 'group')},
            },
        ),
    ]
