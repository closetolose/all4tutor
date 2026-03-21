# Block 1: CASCADE→SET_NULL для финансов, удаление Lessons.is_paid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_delete_tutorsubjects'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='student',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='transactions',
                to='core.users',
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='tutor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='core.users',
            ),
        ),
        migrations.AlterField(
            model_name='paymentreceipt',
            name='student',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payment_receipts',
                to='core.users',
            ),
        ),
        migrations.AlterField(
            model_name='paymentreceipt',
            name='tutor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='incoming_receipts',
                to='core.users',
            ),
        ),
        migrations.RemoveField(
            model_name='lessons',
            name='is_paid',
        ),
    ]
