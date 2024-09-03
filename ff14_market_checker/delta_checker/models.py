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

class Market_Data(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    world = models.ForeignKey(World, on_delete=models.CASCADE)
    price_per_unit = models.IntegerField(null=True)
    quantity = models.IntegerField(null=True)
    total = models.IntegerField(null=True)
    tax = models.IntegerField(null=True)
    regular_sale_velocity = models.DecimalField(null=True, decimal_places=2, max_digits=15)
    current_average_price = models.DecimalField(null=True, decimal_places=2, max_digits=15)
    average_price = models.DecimalField(null=True, decimal_places=2, max_digits=15)
    min_price = models.IntegerField(null=True)
    
    def __str__(self):
        return f'{self.item.name}({self.world.name})'
