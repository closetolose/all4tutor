# Переименование модели Users → Profile

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_delete_botchatmessage'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Users',
            new_name='Profile',
        ),
    ]
