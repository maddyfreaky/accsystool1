# Generated by Django 5.1 on 2024-10-05 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0031_task_is_child_task_parent_task'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(choices=[('Not Started', 'Not Started'), ('Working', 'Working'), ('Pending Review', 'Pending Review'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Not Started', max_length=20),
        ),
    ]