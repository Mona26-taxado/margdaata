# Generated by Django 5.1.4 on 2025-03-06 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0002_alter_customer_dob'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='username',
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
