import decimal
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import DC, World, Item, Market_Data, Item_Stats
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
import math
#from silk.profiling.profiler import silk_profile
from django.db.models import Max
from django.shortcuts import redirect

headers = {'User-Agent': 'delta_checker'}

num_history_entries = 100

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

#@silk_profile(name='parse_and_store_data')
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
        
        num_history_entries = 0
        # get num transactions per day avg
        avg_daily_transactions = 0
        if result['recentHistory']:
            num_history_entries = len(result['recentHistory'])
            
            # attempt to avoid low volume items by only giving an
            # avg_daily_transaction to items that have 50+ history entries
            #if num_history_entries >= 50:
            last_hist = result['recentHistory'][-1]
            last_hist_time = last_hist['timestamp']
            
            # make datetime.now(timezone.utc) compatible with the history timestamp
            now = datetime.fromtimestamp(round(datetime.now(timezone.utc).replace(microsecond=0).timestamp()))
            past = datetime.fromtimestamp(last_hist_time)
            timespan = now - past
            try:
                avg_daily_transactions = (num_history_entries * 86400)/timespan.total_seconds()
            except:
                avg_daily_transactions = 0

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
                        average_daily_transactions = round(avg_daily_transactions, 2),
                        units_sold = result['unitsSold'],
                        history_entries = num_history_entries))
        
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
        
    if not event_done.is_set():
        event_done.set()

#@silk_profile(name='queue_progress_bar')
def queue_progress_bar(uri_queue, data_queue, event_done):
    global req_queue_total_size
    global req_queue_progress
    req_queue_progress = 0
    req_total_progress = 0
    req_last_progress = 0
    
    global data_queue_progress

    while not event_done.is_set():
        time.sleep(1)
        req_total_progress = (uri_queue.qsize() - req_queue_total_size) * -1
        req_progress = req_total_progress - req_last_progress
        req_queue_progress += req_progress
        req_last_progress = req_total_progress

#@silk_profile(name='make_api_req')
def make_api_req(uri):
    global last_req_time
    global headers
    with api_req_lock:
        utc_now = datetime.now(timezone.utc)
        delta = utc_now - last_req_time
        if delta.microseconds < min_req_wait_microsec:
            wait_time = (min_req_wait_microsec - delta.microseconds) / 1000000
            time.sleep(wait_time)
        last_req_time = datetime.now(timezone.utc)
    return requests.get(uri, headers=headers)

#@silk_profile(name='get_api_data')
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

#@silk_profile(name='create_item_str_list')
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

#@silk_profile(name='get_data')
def get_data():
    global data_retrieved
    global getting_data
    global req_queue_total_size
    global data_queue_total_size
    global num_history_entries
    
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
            uri = f'https://universalis.app/api/v2/{w.name}/{i}?listings=1&entries={num_history_entries}&hq=false&fields=items.listings.pricePerUnit%2Citems.listings.quantity%2Citems.listings.total%2Citems.listings.tax%2Citems.regularSaleVelocity%2Citems.unitsSold%2Citems.worldName%2Citems.recentHistory'
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
num_weight_calculated = 0
calc_stats_lock = threading.Lock()
max_pprofit = 0
max_adt = 0

#@silk_profile(name='update_items_calcd')
def update_items_calcd(item_queue, weight_queue, event_stats_done, event_weight_done):
    global num_items_calculated
    global num_weight_calculated
    global total_items
    global max_pprofit
    global max_adt
    
    while not item_queue.empty():
        num_items_calculated = (item_queue.qsize() - total_items) * -1
        time.sleep(1)
    
    num_items_calculated = total_items
    
    item_stats = Item_Stats.objects.all()
    item_stats_pprofit = list(item_stats.values_list('potential_profit', flat=True))
    item_stats_adt = list(item_stats.values_list('average_daily_transactions', flat=True))
    item_stats_pprofit.sort(reverse=True)
    item_stats_adt.sort(reverse=True)
    max_pprofit = item_stats_pprofit[0]
    max_adt = item_stats_adt[0]
    
    event_stats_done.set()
    
    # this is being skipped for some reason
    #test = weight_queue.empty() # this is resolving true??? maybe can't use it
    #test2 = weight_queue.qsize()
    #while not weight_queue.empty():
    while not event_weight_done.is_set():
        num_weight_calculated = (weight_queue.qsize() - total_items) * -1
        time.sleep(1)
        
    num_weight_calculated = total_items
    
def calculate_weight_worker(weight_queue, event_stats_done):
    global max_pprofit
    global max_adt
    
    while not event_stats_done.is_set():
        time.sleep(1)
    
    # calculate max values for potential profit and average_daily_transactions
    #max_pprofit = Item_Stats.objects.aggregate(Max('potential_profit')).get('potential_profit__max')
    #max_adt = Item_Stats.objects.aggregate(Max('average_daily_transactions')).get('average_daily_transactions__max')
    #item_stats_pprofit = list(Item_Stats.objects.all().values('potential_profit'))
    #item_stats_adp = list(Item_Stats.objects.all().values('average_daily_transactions'))
    #item_stats_pprofit.sort(reverse=True)
    #item_stats_adp.sort(reverse=True)
    #max_pprofit = item_stats_pprofit[0]
    #max_adt = item_stats_adp[0]
    
    item_list = []

    while not weight_queue.empty(): # weight_queue.empty() might be resolving true
        i = weight_queue.get()
        pprofit_percent = round(decimal.Decimal(i.potential_profit) / max_pprofit, 4) * 100
        adt_percent = round(decimal.Decimal(i.average_daily_transactions) / max_adt, 4) * 100
        
        # these shouldn't be possible, and are probably the cause of bad or unwanted data
        # so effectively remove them from the list
        if pprofit_percent > 100:
            pprofit_percent = 0
        if adt_percent > 100:
            adt_percent = 0
        
        weight = round(pprofit_percent + adt_percent)
        
        item_list.append(i)
        item_list[-1].weight = weight
        
        #Item.objects.filter(id=i.id).update(weight = pprofit_percent + adt_percent)
        

    Item_Stats.objects.bulk_update(item_list, ['weight'])
        
def save_item_stats(item,
                    average_sale_velocity,
                    average_daily_transactions,
                    average_items_per_transaction,
                    market_data_list,
                    region_delta,
                    dc_delta,
                    region_low_world,
                    dc_low_world,
                    potential_profit,
                    weight):
    return Item_Stats(item = item,
                    average_sale_velocity = average_sale_velocity,
                    average_daily_transactions = average_daily_transactions,
                    average_items_per_transaction = average_items_per_transaction,
                    market_data_list = market_data_list,
                    region_delta = region_delta,
                    dc_delta = dc_delta,
                    region_low_world = region_low_world,
                    dc_low_world = dc_low_world,
                    potential_profit = potential_profit,
                    weight = weight)

#@silk_profile(name='calculate_item_stats_worker')
def calculate_item_stats_worker(item_queue, weight_queue):    
    target_list_size = 100
    item_list = []
    
    while not item_queue.empty():
        i = item_queue.get()
        
        market_data = Market_Data.objects.filter(item=i)
        sale_velocity = 0
        daily_transactions = 0
        items_per_transaction = 0
        market_data_str = ""
        region_lowest = None
        dc_lowest = None
        kraken = None
        
        for m in market_data:
            sale_velocity += m.regular_sale_velocity
            daily_transactions += m.average_daily_transactions
            items_per_transaction += m.units_sold/m.history_entries if not m.history_entries == 0 else 0
            market_data_str += str(m.id) + ','
            
            if region_lowest == None or m.price_per_unit < region_lowest.price_per_unit:
                region_lowest = m
            
            # check if in dc
            if m.world.dc.id == 4:
                if dc_lowest == None or m.price_per_unit < dc_lowest.price_per_unit:
                    dc_lowest = m
        
            if m.world.id == 409:
                kraken = m
        
        num_market_data = len(market_data)
        
        r_delta = 0
        d_delta = 0
        
        if kraken:
            r_delta = kraken.price_per_unit - region_lowest.price_per_unit
            d_delta = kraken.price_per_unit - dc_lowest.price_per_unit
        
        # set celining for max delta
        if r_delta > 1000000:
            r_delta = 0
        if d_delta > 1000000:
            d_delta = 0
        
        adt = daily_transactions/num_market_data if not num_market_data == 0 else 0
        aipt = items_per_transaction/num_market_data if not num_market_data == 0 else 0
        
        pprofit = d_delta * aipt
        
        '''
        Item.objects.filter(id=i.id).update(
            average_sale_velocity = sale_velocity/num_market_data if not num_market_data == 0 else 0,
            average_daily_transactions = adt,
            average_items_per_transaction = aipt,
            market_data_list = market_data_str[:-1],
            region_delta = r_delta,
            dc_delta = d_delta,
            region_low_world = region_lowest.world,
            dc_low_world = dc_lowest.world,
            potential_profit = pprofit
        )
        '''
        
        '''
        item_list.append(i)
        item_list[-1].item = i.id
        item_list[-1].average_sale_velocity = sale_velocity/num_market_data if not num_market_data == 0 else 0
        item_list[-1].average_daily_transactions = adt
        item_list[-1].average_items_per_transaction = aipt
        item_list[-1].market_data_list = market_data_str[:-1]
        item_list[-1].region_delta = r_delta
        item_list[-1].dc_delta = d_delta
        item_list[-1].region_low_world = region_lowest.world.name if region_lowest else ""
        item_list[-1].dc_low_world = dc_lowest.world.name if dc_lowest else ""
        item_list[-1].potential_profit = pprofit
        item_list[-1].weight = 0
        '''
        item_stat = Item_Stats(
            item = i.id,
            average_sale_velocity = sale_velocity/num_market_data if not num_market_data == 0 else 0,
            average_daily_transactions = adt,
            average_items_per_transaction = aipt,
            market_data_list = market_data_str[:-1],
            region_delta = r_delta,
            dc_delta = d_delta,
            region_low_world = region_lowest.world.name if region_lowest else "",
            dc_low_world = dc_lowest.world.name if dc_lowest else "",
            potential_profit = pprofit,
            weight = 0
        )
        item_list.append(item_stat)
        
        weight_queue.put(item_stat)
        '''
        item_list_len = len(item_list)
        if (item_list_len == target_list_size):
            #Market_Data.objects.bulk_create(item_list, target_list_size)
            Item.objects.bulk_update(item_list, ['average_sale_velocity',
                                                 'average_daily_transactions',
                                                 'average_items_per_transaction',
                                                 'market_data_list',
                                                 'region_delta',
                                                 'dc_delta',
                                                 'region_low_world',
                                                 'dc_low_world',
                                                 'potential_profit'
                                                 ], target_list_size)
            item_list.clear()
        '''
    '''    
    Item_Stats.objects.bulk_create(item_list, ['item',
                                                'average_sale_velocity',
                                                'average_daily_transactions',
                                                'average_items_per_transaction',
                                                'market_data_list',
                                                'region_delta',
                                                'dc_delta',
                                                'region_low_world',
                                                'dc_low_world',
                                                'potential_profit'
                                                ], target_list_size)
    '''
    Item_Stats.objects.bulk_create(item_list, batch_size=target_list_size)
    #new_item_stats = Item_Stats.objects.bulk_create(item_list, target_list_size)
    #new_item_stats.save()

#@silk_profile(name='calculate_item_stats')
def calculate_item_stats():
    global calculating_stats
    global item_stats_calculated
    global total_items
    
    Item_Stats.objects.all().delete()
    
    item_queue = queue.Queue()
    weight_queue = queue.Queue()
    event_stats_done = threading.Event()
    event_weight_done = threading.Event()
    
    item_list = Item.objects.all()
    total_items = len(item_list)
    for i in item_list:
        item_queue.put(i)
    
    update_items_calcd_thread = threading.Thread(target=update_items_calcd, args=[item_queue, weight_queue, event_stats_done, event_weight_done])
    #t.setDaemon(True)
    update_items_calcd_thread.start()
    
    calc_item_stats_thread1 = threading.Thread(target=calculate_item_stats_worker, args=[item_queue, weight_queue])
    calc_item_stats_thread2 = threading.Thread(target=calculate_item_stats_worker, args=[item_queue, weight_queue])
    calc_item_stats_thread3 = threading.Thread(target=calculate_item_stats_worker, args=[item_queue, weight_queue])
    calc_item_stats_thread4 = threading.Thread(target=calculate_item_stats_worker, args=[item_queue, weight_queue])
    calc_item_stats_thread5 = threading.Thread(target=calculate_item_stats_worker, args=[item_queue, weight_queue])
    calc_item_stats_thread6 = threading.Thread(target=calculate_item_stats_worker, args=[item_queue, weight_queue])
    calc_item_stats_thread7 = threading.Thread(target=calculate_item_stats_worker, args=[item_queue, weight_queue])
    calc_item_stats_thread8 = threading.Thread(target=calculate_item_stats_worker, args=[item_queue, weight_queue])
    
    calc_item_stats_thread1.start()
    calc_item_stats_thread2.start()
    calc_item_stats_thread3.start()
    calc_item_stats_thread4.start()
    calc_item_stats_thread5.start()
    calc_item_stats_thread6.start()
    calc_item_stats_thread7.start()
    calc_item_stats_thread8.start()
    
    calc_item_stats_thread1.join()
    calc_item_stats_thread2.join()
    calc_item_stats_thread3.join()
    calc_item_stats_thread4.join()
    calc_item_stats_thread5.join()
    calc_item_stats_thread6.join()
    calc_item_stats_thread7.join()
    calc_item_stats_thread8.join()
    
    calc_weight_thread1 = threading.Thread(target=calculate_weight_worker, args=[weight_queue, event_stats_done])
    calc_weight_thread2 = threading.Thread(target=calculate_weight_worker, args=[weight_queue, event_stats_done])
    calc_weight_thread3 = threading.Thread(target=calculate_weight_worker, args=[weight_queue, event_stats_done])
    calc_weight_thread4 = threading.Thread(target=calculate_weight_worker, args=[weight_queue, event_stats_done])

    calc_weight_thread1.start()
    calc_weight_thread2.start()
    calc_weight_thread3.start()
    calc_weight_thread4.start()
    
    calc_weight_thread1.join()
    calc_weight_thread2.join()
    calc_weight_thread3.join()
    calc_weight_thread4.join()

    '''
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        executor.submit(calculate_item_stats_worker, item_queue, weight_queue)
        executor.submit(calculate_item_stats_worker, item_queue, weight_queue)
        executor.submit(calculate_item_stats_worker, item_queue, weight_queue)
        executor.submit(calculate_item_stats_worker, item_queue, weight_queue)
        executor.submit(calculate_item_stats_worker, item_queue, weight_queue)
        executor.submit(calculate_item_stats_worker, item_queue, weight_queue)
        executor.submit(calculate_item_stats_worker, item_queue, weight_queue)
        executor.submit(calculate_item_stats_worker, item_queue, weight_queue)
        executor.submit(calculate_weight_worker, weight_queue, event_stats_done)
        executor.submit(calculate_weight_worker, weight_queue, event_stats_done)
        executor.submit(calculate_weight_worker, weight_queue, event_stats_done)
        executor.submit(calculate_weight_worker, weight_queue, event_stats_done)
        executor.submit(calculate_weight_worker, weight_queue, event_stats_done)
        executor.submit(calculate_weight_worker, weight_queue, event_stats_done)
        executor.submit(calculate_weight_worker, weight_queue, event_stats_done)
        executor.submit(calculate_weight_worker, weight_queue, event_stats_done)
    '''
    event_weight_done.set()
    
    update_items_calcd_thread.join()

    item_stats_calculated = True
    calculating_stats = False

class _Item():
    def __init__(self,
                 id,
                 name,
                 icon_file,
                 average_sale_velocity,
                 average_daily_transactions,
                 region_delta,
                 region_low_world,
                 dc_delta,
                 dc_low_world,
                 lowest_price,
                 weight):
        self.id = id
        self.name = name
        self.icon_file = icon_file
        self.average_sale_velocity = average_sale_velocity
        self.average_daily_transactions = average_daily_transactions
        self.region_delta = region_delta
        self.region_low_world = region_low_world
        self.dc_delta = dc_delta
        self.dc_low_world = dc_low_world
        self.lowest_price = lowest_price
        self.weight = weight

#
# views
#
#@silk_profile(name='index')
def home(request):
    item_stats = Item_Stats.objects.all().order_by('-weight')[:100]
    item_list = []
    for i in item_stats:
        item = Item.objects.get(pk=i.item)
        lowest_price = Market_Data.objects.get(item=item, world=World.objects.get(name=i.dc_low_world))
        item_list.append(_Item(id=item.id,
                               name=item.name,
                               icon_file=item.icon_file,
                               average_sale_velocity=i.average_sale_velocity,
                               average_daily_transactions=i.average_daily_transactions,
                               region_delta=i.region_delta,
                               region_low_world=i.region_low_world,
                               dc_delta=i.dc_delta,
                               dc_low_world=i.dc_low_world,
                               lowest_price=lowest_price,
                               weight=i.weight
                               ))
    
    context = {
        "item_list": item_list,
    }
    return render(request, 'delta_checker/home.html', context)

#@silk_profile(name='reset_calc_item_stats')
def reset_calc_item_stats(request=None):
    global item_stats_calculated
    item_stats_calculated = False
    return redirect('calc_item_stats')

#@silk_profile(name='calc_item_stats')
def calc_item_stats(request=None):
    global calculating_stats
    global item_stats_calculated
    global total_items
    global num_items_calculated
    global num_weight_calculated
    
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
        
        weight_percent_complete = ""
        if total_items == 0:
            weight_percent_complete = "0"
        else:
            weight_percent_complete = str(round((num_weight_calculated * 100)/total_items))
         
        hx_trigger = "every 1s" if calculating_stats else "once"
        
        context = {
            "calculating_stats": calculating_stats,
            "num_items_calculated": num_items_calculated,
            "num_weight_calculated": num_weight_calculated,
            "total_items": total_items,
            "stats_percent_complete": stats_percent_complete,
            "weight_percent_complete": weight_percent_complete,
            "hx_trigger": hx_trigger,
        }
        
        if request is None:
            return context
        
        return render(request, 'delta_checker/calc_item_stats.html', context)
    else:
        return redirect('home')

#@silk_profile(name='reset_build_market_data')
def reset_build_market_data(request=None):
    global data_retrieved
    data_retrieved = False
    return redirect('build_market_data')

#@silk_profile(name='build_market_data')
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
        return redirect('home')