# Generated by Django 5.1 on 2024-09-23 10:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0019_todolistfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='todolist',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='todolists', to='task_management.task'),
        ),
    ]
