# Generated by Django 5.1 on 2024-11-06 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_management', '0003_leaverequest_level1_approvers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaverequest',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
