from django.db import migrations, models


def forwards(apps, schema_editor):
    # This migration adds doctor decision tracking to SmartSchedule.
    SmartSchedule = apps.get_model('scheduling', 'SmartSchedule')
    # Fields are added declaratively below; no data migration required.


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='smartschedule',
            name='doctor_decision',
            field=models.CharField(
                blank=True,
                choices=[
                    ('double_next', 'مضاعفة الجرعة القادمة'),
                    ('skip', 'تخطي الجرعة'),
                    ('take_later', 'أخذها لاحقاً'),
                    ('reschedule', 'إعادة جدولتها'),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='smartschedule',
            name='doctor_decision_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
