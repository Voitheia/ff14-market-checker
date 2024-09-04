from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import DC, World, Item, Market_Data
import requests
import time
import concurrent.futures
import queue
import threading
import json
from datetime import datetime, timedelta, timezone
from tqdm import tqdm

'''
def make_market_data_request(w, i):
    uri = f'https://universalis.app/api/v2/{w}/{i}?listings=1&entries=250&hq=false&fields=items.listings.pricePerUnit%2Citems.listings.quantity%2Citems.listings.total%2Citems.listings.tax%2Citems.regularSaleVelocity%2Citems.unitsSold%2Citems.worldName'
    response = requests.get(uri)
    if not response.status_code == 200:
        time.sleep(.05)
        make_market_data_request(w, i)
        return
    
    result = response.json()["items"]
    for r in data:
        item = Item.objects.get(pk=int(r))
        world = World.objects.get(name=w)
        listings = None
        if result[r]['listings']:
            listings = result[r]['listings'][0]
        price_per_unit = listings['pricePerUnit'] if listings else 0
        quantity = listings['quantity'] if listings else 0
        total = listings['total'] if listings else 0
        tax = listings['tax'] if listings else 0
        regular_sale_velocity = result[r]['regularSaleVelocity']
        units_sold = result[r]['unitsSold']
        data = Market_Data(item=item,
                            world=world,
                            price_per_unit=price_per_unit,
                            quantity=quantity,
                            total=total,
                            tax=tax,
                            regular_sale_velocity=regular_sale_velocity,
                            units_sold=units_sold)
    for r in result:
        listings = None
        if result[r]['listings']:
            listings = result[r]['listings'][0]
        data = Market_Data(item =                   Item.objects.get(pk=int(r)),
                           world =                  result[r]['worldName'],
                           price_per_unit =         listings['pricePerUnit'] if listings else 0,
                           quantity =               listings['quantity'] if listings else 0,
                           total =                  listings['total'] if listings else 0,
                           tax =                    listings['tax'] if listings else 0,
                           regular_sale_velocity =  result[r]['regularSaleVelocity'],
                           units_sold =             result[r]['unitsSold'])
        data.save()
        print(data)
    time.sleep(.05)
'''

data_retrieved = False
api_req_lock = threading.Lock()
last_req_time = datetime.now(timezone.utc)
min_req_wait_microsec = 40000
queue_total_size = 0

def parse_and_store_data(data_queue, event_start, event_stop):
    while not event_start.is_set():
        time.sleep(.25)
    
    while not data_queue.empty() or not event_stop.is_set():
        entry = data_queue.get() # tuple of (str, dict)
        r = entry[0]
        result = entry[1]

        listings = None
        if result['listings']:
            listings = result['listings'][0]
        data = Market_Data(item = Item.objects.get(pk=int(r)),
                        world = World.objects.get(name=result['worldName']),
                        price_per_unit = listings['pricePerUnit'] if listings else 0,
                        quantity = listings['quantity'] if listings else 0,
                        total = listings['total'] if listings else 0,
                        tax = listings['tax'] if listings else 0,
                        regular_sale_velocity = result['regularSaleVelocity'],
                        units_sold = result['unitsSold'])
        data.save()

def queue_progress(uri_queue, event_stop):
    global queue_total_size
    total_progress = 0
    last_progress = 0
    progressbar = tqdm(total=queue_total_size)
    while not event_stop.is_set():
        time.sleep(.5)
        total_progress = (uri_queue.qsize() - queue_total_size) * -1
        progress = total_progress - last_progress
        progressbar.update(progress)
        last_progress = total_progress
    progressbar.close()

def make_api_req(uri):
    global last_req_time
    with api_req_lock:
        utc_now = datetime.now(timezone.utc)
        delta = utc_now - last_req_time
        if delta.microseconds < min_req_wait_microsec:
            wait_time = (min_req_wait_microsec - delta.microseconds) / 1000000
            time.sleep(wait_time)
        last_req_time = datetime.now(timezone.utc)
    return requests.get(uri)

def get_api_data(uri_queue, data_queue, event_start, event_stop):
    while not uri_queue.empty():
        uri = uri_queue.get()
        ok = False
        response = None
        while(not ok):
            response = make_api_req(uri)
            ok = response.ok
        result = response.json()["items"]
        for r in result:
            result_tuple = (r, result[r])
            data_queue.put(result_tuple)
        if not event_start.is_set():
            event_start.set()
    if not event_stop.is_set():
        event_stop.set()

def create_item_str_list():
    item_str_list = []
    items = ""
    counter = 0
    item_list = Item.objects.all()
    for i in item_list:
        if counter == 99:
            items += str(i.id)
            item_str_list.append(items)
            items = ""
            counter = 0
            continue
        
        items += str(i.id) + ','
        counter += 1
    
    return item_str_list

def get_data():
    global data_retrieved
    global queue_total_size
    
    # clear market data
    Market_Data.objects.all().delete()
    
    # get list of worlds
    world_list = World.objects.all()

    # get list of items, break into strings of 100 items
    item_str_list = create_item_str_list()
    
    uri_queue = queue.Queue()
    data_queue = queue.Queue()
    event_start = threading.Event()
    event_stop = threading.Event()
    
    for w in world_list:
        for i in item_str_list:
            uri = f'https://universalis.app/api/v2/{w.name}/{i}?listings=1&entries=250&hq=false&fields=items.listings.pricePerUnit%2Citems.listings.quantity%2Citems.listings.total%2Citems.listings.tax%2Citems.regularSaleVelocity%2Citems.unitsSold%2Citems.worldName'
            uri_queue.put(uri)
            queue_total_size += 1
    
    print("starting threads")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(queue_progress, uri_queue, event_stop)
        executor.submit(parse_and_store_data, data_queue, event_start, event_stop)
    
    data_retrieved = True

# Create your views here.
def index(request):
    global data_retrieved
    if not data_retrieved:
        get_data()
    
    '''
    take the items in the item list and query universalis for market data for each of them
    and store that market data in the database
    
    then, get the top 100 velocity items and display them in the webpage with their highest
    and lowest prices
    '''
    item_list = []
    
    
    market_data = Market_Data.objects.all().order_by('regular_sale_velocity')
    #loop through the list of market data, and produce a unique (no duplicate items) sorted list of the 100 highest sale velocity items
    
    
    context = {
        "item_list": item_list,
    }
    return render(request, 'delta_checker/index.html', context)