# Generated by Django 4.2.7 on 2025-04-08 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_email_notifications_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verification_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='useractivity',
            name='activity_type',
            field=models.CharField(choices=[('registration', 'Registration'), ('login', 'Login'), ('logout', 'Logout'), ('password_change', 'Password Change'), ('profile_update', 'Profile Update'), ('hiring_request', 'Hiring Request'), ('payment', 'Payment'), ('password_reset', 'Password Reset')], max_length=20),
        ),
    ]
