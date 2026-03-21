# Generated manually: CheckConstraints and defaults for data integrity

from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_unlinkrequest_reason'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='lessons',
            constraint=models.CheckConstraint(
                check=Q(price__gte=0),
                name='lessons_price_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='lessons',
            constraint=models.CheckConstraint(
                check=Q(duration__gt=0),
                name='lessons_duration_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='transaction',
            constraint=models.CheckConstraint(
                check=Q(amount__gt=0),
                name='transaction_amount_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='paymentreceipt',
            constraint=models.CheckConstraint(
                check=Q(amount__gt=0),
                name='payment_receipt_amount_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='studenttariff',
            constraint=models.CheckConstraint(
                check=Q(price__gte=0),
                name='student_tariff_price_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='testresult',
            constraint=models.CheckConstraint(
                check=Q(max_score__gt=0),
                name='test_result_max_score_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='testresult',
            constraint=models.CheckConstraint(
                check=Q(score__gte=0),
                name='test_result_score_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='testresult',
            constraint=models.CheckConstraint(
                check=Q(score__lte=F('max_score')),
                name='test_result_score_lte_max',
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='description',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
