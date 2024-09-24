# Generated by Django 5.1 on 2024-09-12 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0003_delete_task_remove_issue_completed_issue_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issue',
            name='status',
        ),
        migrations.AddField(
            model_name='issue',
            name='completed',
            field=models.BooleanField(default=False),
        ),
    ]
