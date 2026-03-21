# Block 3: TestResult.tutor удалён, HomeworkResponse.student удалён

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_block2_remove_tables'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testresult',
            name='tutor',
        ),
        migrations.RemoveField(
            model_name='homeworkresponse',
            name='student',
        ),
    ]
