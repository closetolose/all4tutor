from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_studenttariff_xor_group_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='studygroups',
            name='is_archived',
            field=models.BooleanField(default=False, verbose_name='В архиве'),
        ),
    ]
