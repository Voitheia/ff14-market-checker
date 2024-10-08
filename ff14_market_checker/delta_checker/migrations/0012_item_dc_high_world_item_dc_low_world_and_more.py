# Generated by Django 5.1.1 on 2024-09-05 19:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delta_checker', '0011_item_dc_delta_item_region_delta'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='dc_high_world',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='world_dh', to='delta_checker.world'),
        ),
        migrations.AddField(
            model_name='item',
            name='dc_low_world',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='world_dl', to='delta_checker.world'),
        ),
        migrations.AddField(
            model_name='item',
            name='region_high_world',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='world_rh', to='delta_checker.world'),
        ),
        migrations.AddField(
            model_name='item',
            name='region_low_world',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='world_rl', to='delta_checker.world'),
        ),
    ]
