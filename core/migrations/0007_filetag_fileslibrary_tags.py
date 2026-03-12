# Generated for file tags feature

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_connectionrequest_tutor_color_hex'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_tags', to='core.users')),
            ],
            options={
                'db_table': 'file_tags',
                'unique_together': {('tutor', 'name')},
            },
        ),
        migrations.AddField(
            model_name='fileslibrary',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='files', to='core.filetag'),
        ),
    ]
