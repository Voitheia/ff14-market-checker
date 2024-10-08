# Generated by Django 5.1.1 on 2024-09-03 18:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DC',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('region', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('icon_file', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='World',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('dc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='delta_checker.dc')),
            ],
        ),
        migrations.CreateModel(
            name='Market_Data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_per_unit', models.IntegerField(null=True)),
                ('quantity', models.IntegerField(null=True)),
                ('total', models.IntegerField(null=True)),
                ('tax', models.IntegerField(null=True)),
                ('regular_sale_velocity', models.DecimalField(decimal_places=2, max_digits=15, null=True)),
                ('current_average_price', models.DecimalField(decimal_places=2, max_digits=15, null=True)),
                ('average_price', models.DecimalField(decimal_places=2, max_digits=15, null=True)),
                ('min_price', models.IntegerField(null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='delta_checker.item')),
                ('world', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='delta_checker.world')),
            ],
        ),
    ]
