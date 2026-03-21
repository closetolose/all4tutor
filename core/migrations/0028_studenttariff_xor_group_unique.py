from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_rename_users_to_profile'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='studenttariff',
            constraint=models.CheckConstraint(
                check=(
                    Q(student__isnull=False, group__isnull=True) |
                    Q(student__isnull=True, group__isnull=False)
                ),
                name='student_tariff_student_xor_group',
            ),
        ),
        migrations.AddConstraint(
            model_name='studenttariff',
            constraint=models.UniqueConstraint(
                fields=('tutor', 'student', 'subject'),
                name='student_tariff_unique_student',
            ),
        ),
        migrations.AddConstraint(
            model_name='studenttariff',
            constraint=models.UniqueConstraint(
                fields=('tutor', 'group', 'subject'),
                name='student_tariff_unique_group',
            ),
        ),
    ]

