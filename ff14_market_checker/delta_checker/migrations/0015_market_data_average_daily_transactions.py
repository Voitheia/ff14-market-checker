# Generated by Django 5.1.1 on 2024-09-06 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delta_checker', '0014_item_average_daily_transactions'),
    ]

    operations = [
        migrations.AddField(
            model_name='market_data',
            name='average_daily_transactions',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
