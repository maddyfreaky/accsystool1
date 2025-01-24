# Generated by Django 5.1 on 2025-01-20 10:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0047_alter_project_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='project',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meeting', to='task_management.project'),
        ),
    ]
