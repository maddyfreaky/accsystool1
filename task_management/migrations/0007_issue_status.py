# Generated by Django 5.1 on 2024-09-12 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0006_remove_issue_status_issue_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='status',
            field=models.CharField(default='todo', max_length=20),
        ),
    ]
