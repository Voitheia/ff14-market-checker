# Generated by Django 5.1.1 on 2024-09-03 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delta_checker', '0002_remove_item_icon_file_item_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='icon_file',
            field=models.CharField(default=0, max_length=256),
            preserve_default=False,
        ),
    ]
