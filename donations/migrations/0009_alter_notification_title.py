# Generated by Django 5.1.4 on 2025-03-07 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0008_alter_notification_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
