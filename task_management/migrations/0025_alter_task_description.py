# Generated by Django 5.1 on 2024-09-27 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0024_task_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
