# Generated by Django 5.1.1 on 2024-09-08 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delta_checker', '0017_item_average_items_per_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='potential_profit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
