# Generated by Django 5.1.1 on 2024-09-03 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delta_checker', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='icon_file',
        ),
        migrations.AddField(
            model_name='item',
            name='icon',
            field=models.ImageField(null=True, upload_to='icons'),
        ),
    ]
