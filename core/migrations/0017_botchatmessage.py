# Bot chat with GigaChat AI

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_chatmessage_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BotChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', 'Пользователь'), ('assistant', 'Ассистент')], max_length=10)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(default=timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bot_chat_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'bot_chat_messages',
                'ordering': ['created_at'],
            },
        ),
    ]
