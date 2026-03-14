# Add is_read field to ChatMessage

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_chatmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]
