# Generated by Django 5.1 on 2024-09-12 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0008_remove_issue_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issue',
            name='completed',
        ),
        migrations.AddField(
            model_name='issue',
            name='status',
            field=models.CharField(choices=[('todo', 'To Do'), ('in-progress', 'In Progress'), ('done', 'Done')], default='todo', max_length=20),
        ),
    ]
