# Generated for tutor color (connection) feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_color_indicator'),
    ]

    operations = [
        migrations.AddField(
            model_name='connectionrequest',
            name='tutor_color_hex',
            field=models.CharField(blank=True, max_length=7, null=True),
        ),
    ]
