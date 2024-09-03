from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import DC, World, Item, Market_Data

# Create your views here.
def index(request):
    
    
    
    
    item_list = Item.objects.all()
    context = {
        "item_list": item_list,
    }
    return render(request, 'delta_checker/index.html', context)