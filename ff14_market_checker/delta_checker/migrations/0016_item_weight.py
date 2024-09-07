# Generated by Django 5.1.1 on 2024-09-06 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delta_checker', '0015_market_data_average_daily_transactions'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='weight',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
    ]
