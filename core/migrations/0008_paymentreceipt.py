# Generated for payment receipts feature

import core.validators
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_filetag_fileslibrary_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('receipt_date', models.DateField()),
                ('file', models.FileField(upload_to='payment_receipts/%Y/%m/', validators=[core.validators.validate_receipt_file])),
                ('status', models.CharField(choices=[('pending', 'Ожидает'), ('approved', 'Подтверждён'), ('rejected', 'Отклонён')], default='pending', max_length=10)),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=timezone.now)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_receipts', to='core.users')),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_receipts', to='core.users')),
            ],
            options={
                'db_table': 'payment_receipts',
                'ordering': ['-created_at'],
            },
        ),
    ]
