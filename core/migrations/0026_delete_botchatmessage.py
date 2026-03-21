# Удаление BotChatMessage (GigaChat) из проекта

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_unlink_to_connectionrequest'),
    ]

    operations = [
        migrations.DeleteModel(name='BotChatMessage'),
    ]
