from django.db import models

# Create your models here.
class DC(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=256)
    region = models.CharField(max_length=256)
    
    def __str__(self):
        return f'{self.name}({self.id})'

class World(models.Model):
    id = models.IntegerField(primary_key=True)
    dc = models.ForeignKey(DC, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    
    def __str__(self):
        return f'{self.dc.name}/{self.name}({self.id})'

class Item(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=256)
    icon_file = models.CharField(max_length=256)
    
    def __str__(self):
        return f'{self.name}({self.id})'

class Item_Stats(models.Model):
    item = models.IntegerField(primary_key=True)
    average_sale_velocity = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    average_daily_transactions = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    average_items_per_transaction = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    market_data_list = models.TextField(default="")
    region_delta = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    dc_delta = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    region_low_world = models.CharField(default="", max_length=256)
    dc_low_world = models.CharField(default="", max_length=256)
    potential_profit = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    weight = models.DecimalField(default=0, decimal_places=2, max_digits=20)

class Market_Data(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    world = models.ForeignKey(World, on_delete=models.CASCADE)
    price_per_unit = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    tax = models.IntegerField(default=0)
    regular_sale_velocity = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    average_daily_transactions = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    units_sold = models.IntegerField(default=0)
    history_entries = models.IntegerField(default=0)
    
    def __str__(self):
        return f'{self.item.name}({self.world.name})'
