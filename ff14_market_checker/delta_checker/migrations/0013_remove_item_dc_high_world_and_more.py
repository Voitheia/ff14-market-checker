# Generated by Django 5.1.1 on 2024-09-06 14:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('delta_checker', '0012_item_dc_high_world_item_dc_low_world_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='dc_high_world',
        ),
        migrations.RemoveField(
            model_name='item',
            name='region_high_world',
        ),
    ]
