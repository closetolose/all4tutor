# Add file field to ChatMessage for images and documents

import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_merge_0014_alter_chatmessage_id_0014_chatmessage_is_read'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='file',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='chat_files/%Y/%m/',
                validators=[core.validators.validate_chat_file],
            ),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='file_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
