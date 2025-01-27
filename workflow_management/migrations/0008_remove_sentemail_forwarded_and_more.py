# Generated by Django 5.1 on 2025-01-02 08:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_management', '0007_sentemail_forwarded'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sentemail',
            name='forwarded',
        ),
        migrations.RemoveField(
            model_name='sentemail',
            name='recipient_user',
        ),
        migrations.CreateModel(
            name='ForwardedReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reply_message_id', models.CharField(max_length=255, unique=True)),
                ('forwarded_at', models.DateTimeField(auto_now_add=True)),
                ('sent_email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forwarded_replies', to='workflow_management.sentemail')),
            ],
        ),
    ]
