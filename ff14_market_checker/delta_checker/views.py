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
from tqdm.auto import tqdm
from django.db import transaction
import pytz

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
getting_data = False
api_req_lock = threading.Lock()
last_req_time = datetime.now(timezone.utc)
min_req_wait_microsec = 40000
req_queue_total_size = 0
req_queue_progress = 0
data_queue_progress_lock = threading.Lock()
data_queue_total_size = 0
data_queue_progress = 0



def parse_and_store_data(data_queue, event_start, event_stop, event_done):
    while not event_start.is_set():
        time.sleep(.25)
    
    global data_queue_progress
    target_list_size = 1000
    data_list = []
    
    while not data_queue.empty() or not event_stop.is_set():
        entry = data_queue.get() # tuple of (str, dict)
        r = entry[0]
        result = entry[1]

        listings = None
        if result['listings']:
            listings = result['listings'][0]
        data_list.append(Market_Data(item = Item.objects.get(pk=int(r)),
                        world = World.objects.get(name=result['worldName']),
                        price_per_unit = listings['pricePerUnit'] if listings else 0,
                        quantity = listings['quantity'] if listings else 0,
                        total = listings['total'] if listings else 0,
                        tax = listings['tax'] if listings else 0,
                        regular_sale_velocity = result['regularSaleVelocity'],
                        units_sold = result['unitsSold']))
        
        data_list_len = len(data_list)
        if (data_list_len == target_list_size):
            Market_Data.objects.bulk_create(data_list, target_list_size)
            data_list.clear()
            with data_queue_progress_lock:
                data_queue_progress+=target_list_size
        elif event_stop.is_set():
            Market_Data.objects.bulk_create(data_list, data_list_len)
            data_list.clear()
            with data_queue_progress_lock:
                data_queue_progress+=data_list_len
        
        '''
        data = Market_Data(item = Item.objects.get(pk=int(r)),
                        world = World.objects.get(name=result['worldName']),
                        price_per_unit = listings['pricePerUnit'] if listings else 0,
                        quantity = listings['quantity'] if listings else 0,
                        total = listings['total'] if listings else 0,
                        tax = listings['tax'] if listings else 0,
                        regular_sale_velocity = result['regularSaleVelocity'],
                        units_sold = result['unitsSold'])
        with transaction.atomic():
            data.save()
        
        
        
        with data_queue_progress_lock:
            data_queue_progress+=1
        '''
    if not event_done.is_set():
        event_done.set()

def queue_progress_bar(uri_queue, data_queue, event_done):
    global req_queue_total_size
    global req_queue_progress
    req_queue_progress = 0
    req_total_progress = 0
    req_last_progress = 0
    
    #global data_queue_total_size
    global data_queue_progress

    while not event_done.is_set():
        time.sleep(1)
        req_total_progress = (uri_queue.qsize() - req_queue_total_size) * -1
        req_progress = req_total_progress - req_last_progress
        req_queue_progress += req_progress
        req_last_progress = req_total_progress
        
        '''
        local_data_queue_progress = 0
        with data_queue_progress_lock:
            local_data_queue_progress = data_queue_progress
        data_queue_total_size = data_queue.qsize() + local_data_queue_progress
        '''
        #data_queue_total_size = data_queue.qsize() + data_queue_progress

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
    
    item_str_list.append(items[:-1])
    
    return item_str_list

def get_data():
    global data_retrieved
    global getting_data
    global req_queue_total_size
    global data_queue_total_size
    
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
    event_done = threading.Event()
    
    for w in world_list:
        for i in item_str_list:
            uri = f'https://universalis.app/api/v2/{w.name}/{i}?listings=1&entries=250&hq=false&fields=items.listings.pricePerUnit%2Citems.listings.quantity%2Citems.listings.total%2Citems.listings.tax%2Citems.regularSaleVelocity%2Citems.unitsSold%2Citems.worldName'
            uri_queue.put(uri)
            req_queue_total_size += 1
    
    data_queue_total_size = req_queue_total_size * 100 # 100 items for all but potentially the last req
    
    start_time = datetime.now(pytz.timezone("America/New_York"))
    print(f'start time {start_time}')
    print("starting threads")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=13) as executor:
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(get_api_data, uri_queue, data_queue, event_start, event_stop)
        executor.submit(queue_progress_bar, uri_queue, data_queue, event_done)
        executor.submit(parse_and_store_data, data_queue, event_start, event_stop, event_done)
        executor.submit(parse_and_store_data, data_queue, event_start, event_stop, event_done)
        executor.submit(parse_and_store_data, data_queue, event_start, event_stop, event_done)
        executor.submit(parse_and_store_data, data_queue, event_start, event_stop, event_done)
    
    getting_data = False
    data_retrieved = True
    
    end_time = datetime.now(pytz.timezone("America/New_York"))
    print(f'end time {end_time}')
    print(f'time elapsed {end_time-start_time}')

calculating_stats = False
item_stats_calculated = False
total_items = 0
num_items_calculated = 0

def calculate_item_stats():
    global calculating_stats
    global item_stats_calculated
    global total_items
    global num_items_calculated
    
    item_list = Item.objects.all()
    total_items = len(item_list)
    for i in item_list:
        
        market_data = Market_Data.objects.filter(item=i)
        sale_velocity = 0
        market_data_str = ""
        region_lowest = None
        region_highest = None
        dc_lowest = None
        dc_highest = None
        
        for m in market_data:
            sale_velocity += m.regular_sale_velocity
            market_data_str += str(m.id) + ','
            
            # check if in region
            if m.world.dc.region == "North-America":
                if region_lowest == None or m.price_per_unit < region_lowest.price_per_unit:
                    region_lowest = m
                if region_highest == None or m.price_per_unit > region_highest.price_per_unit:
                    region_highest = m
            
            # check if in dc
            if m.world.dc.id == 4:
                if dc_lowest == None or m.price_per_unit < dc_lowest.price_per_unit:
                    dc_lowest = m
                if dc_highest == None or m.price_per_unit > dc_highest.price_per_unit:
                    dc_highest = m
        
        Item.objects.filter(id=i.id).update(
            average_sale_velocity = sale_velocity/len(market_data),
            market_data_list = market_data_str[:-1],
            region_delta = region_highest.price_per_unit - region_lowest.price_per_unit,
            dc_delta = dc_highest.price_per_unit - dc_lowest.price_per_unit,
            region_low_world = region_lowest.world,
            region_high_world = region_highest.world,
            dc_low_world = dc_lowest.world,
            dc_high_world = dc_highest.world
        )
        
        num_items_calculated += 1

    item_stats_calculated = True
    calculating_stats = False

#
# views
#
def index(request):
    item_list = Item.objects.all().order_by('-average_sale_velocity')[:100]
    
    context = {
        "item_list": item_list,
    }
    return render(request, 'delta_checker/index.html', context)

def calc_item_stats(request=None):
    global calculating_stats
    global item_stats_calculated
    global total_items
    global num_items_calculated
    
    if not item_stats_calculated:
        if not calculating_stats:
            calculating_stats = True
            t = threading.Thread(target=calculate_item_stats)
            t.setDaemon(True)
            t.start()
        
        stats_percent_complete = ""
        if total_items == 0:
            stats_percent_complete = "0"
        else:
            stats_percent_complete = str(round((num_items_calculated * 100)/total_items))
         
        hx_trigger = "every 1s" if calculating_stats else "once"
        
        context = {
            "calculating_stats": calculating_stats,
            "num_items_calculated": num_items_calculated,
            "total_items": total_items,
            "stats_percent_complete": stats_percent_complete,
            "hx_trigger": hx_trigger,
        }
        
        if request is None:
            return context
        
        return render(request, 'delta_checker/calc_item_stats.html', context)
    else:
        return index(request)

def build_market_data(request=None):
    global data_retrieved
    global getting_data

    if not data_retrieved:
        if not getting_data:
            getting_data = True
            t = threading.Thread(target=get_data)
            t.setDaemon(True)
            t.start()
        
        global req_queue_total_size
        global req_queue_progress
        global data_queue_total_size
        global data_queue_progress
        
        req_percent_complete = ""
        if req_queue_total_size == 0:
            req_percent_complete = "0"
        else:
            req_percent_complete = str(round((req_queue_progress * 100)/req_queue_total_size))
            
        data_percent_complete = ""
        if data_queue_total_size == 0:
            data_percent_complete = "0"
        else:
            data_percent_complete = str(round((data_queue_progress * 100)/data_queue_total_size))
        
        hx_trigger = "every 1s" if getting_data else "once"
        
        context = {
            "getting_data": getting_data,
            "req_percent_complete": req_percent_complete,
            "req_queue_progress": req_queue_progress,
            "req_queue_total_size": req_queue_total_size,
            "data_percent_complete": data_percent_complete,
            "data_queue_progress": data_queue_progress,
            "data_queue_total_size": data_queue_total_size,
            "hx_trigger": hx_trigger,
        }
        
        if request is None:
            return context
        
        return render(request, 'delta_checker/build_market_data.html', context)
    
    else:
        return index(request)