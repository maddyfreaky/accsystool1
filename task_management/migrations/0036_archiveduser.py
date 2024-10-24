# Generated by Django 5.1 on 2024-10-22 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0035_notification'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivedUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('date_joined', models.DateTimeField()),
                ('deleted_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
