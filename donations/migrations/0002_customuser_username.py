# Generated by Django 5.1.4 on 2025-03-10 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='username',
            field=models.CharField(default='admin', max_length=50, unique=True),
        ),
    ]
