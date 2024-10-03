# Generated by Django 5.1 on 2024-10-03 09:47

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0026_alter_task_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='comment_timestamp',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2024, 10, 3, 9, 47, 3, 724568, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='task',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
    ]
