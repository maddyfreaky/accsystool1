# Generated by Django 5.1 on 2024-09-13 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0011_issue_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issue',
            name='status',
        ),
        migrations.AddField(
            model_name='todolist',
            name='status',
            field=models.CharField(choices=[('todo', 'To Do'), ('progress', 'In Progress'), ('done', 'Done')], default='todo', max_length=20),
        ),
    ]
