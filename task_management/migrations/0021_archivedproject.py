# Generated by Django 5.1 on 2024-09-26 05:08

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0020_todolist_task'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivedProject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('projectname', models.CharField(max_length=200)),
                ('taskname', models.CharField(max_length=200)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], max_length=10)),
                ('from_date', models.DateField(blank=True, null=True)),
                ('to_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField()),
                ('deleted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('working', 'Working'), ('pending_review', 'Pending Review'), ('overdue', 'OverDue'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('not_started', 'Not Started')], default='not_started', max_length=20)),
                ('assigned_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archived_created_projects', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archived_projects', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
