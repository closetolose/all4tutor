# Add reason field to UnlinkRequest

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_botchatmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='unlinkrequest',
            name='reason',
            field=models.TextField(blank=True, verbose_name='Причина открепления'),
        ),
    ]
