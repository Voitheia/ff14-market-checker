import json
import time
import requests
#from ff14_market_checker.delta_checker.models import DC, World, Item, Market_Data

xivapi_key = 'e650e180eb1b465ea36269a571fd06b27a64f732f295458aabc8bf28a7fd68b4'

# config
region = 'North-America'
dc_name = 'Dynamis'
dynamis_worlds = {404: 'Marilith',
                  405: 'Seraph',
                  406: 'Halicarnassus',
                  407: 'Maduin',
                  408: 'Cuchulainn',
                  409: 'Kraken',
                  410: 'Rafflesia',
                  411: 'Golem'}

# print json to console
def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def extract_velocity(json):
    try:
        return json["dailySaleVelocity"]
    except KeyError:
        return 0

def get_velocity_data():
    static = 'ff14_market_checker/delta_checker/static/'
    with open(f'{static}json/names_velocity.json') as f:
        d = json.load(f)
        for i in d:
            icon = f'icons/{i["itemId"]}.png'
            print(icon)
            break
    
    
    
    '''
    with open('data/json/marketable.json') as f:
        d = json.load(f)
        for i in d:
            f_name = f'data/json/item_data/{i}.json'
            with open(f_name) as item_data:
                i_d = json.load(item_data)
                uri = f'https://xivapi.com{i_d["IconHD"]}?private_key={xivapi_key}'
                img_data = requests.get(uri).content
                with open(f'data/icon/{i}.png', 'wb') as image_handler:
                    image_handler.write(img_data)
            time.sleep(.05)
    '''            
    
    
    
    '''
    with open('data/json/marketable.json') as f:
        d = json.load(f)
        for i in d:
            f_name = f'data/json/item_data/{i}.json'
            with open(f_name, 'w') as out:
                uri = f'https://xivapi.com/item/{i}?private_key={xivapi_key}'
                r = requests.get(uri)
                json_obj = json.dumps(r.json(), indent=4)
                out.write(json_obj)
            time.sleep(.05)
    '''
    
    '''
    items_list = []
    with open('data/json/marketable.json') as f:
        d = json.load(f)
        counter = 0
        items = ""
        for i in d:
            if counter == 99:
                items += str(i)
                items_list.append(items)
                items = ""
                counter = 0
                continue
            
            items += str(i) + ','
            counter += 1
    
    #print(items_list)
    out_list = []
    
    for items in items_list:
        uri = f'https://universalis.app/api/v2/aggregated/{dc_name}/{items}'
        response = requests.get(uri)
        j = response.json()["results"]
        for e in j:
            id = e["itemId"]
            v = ""
            try:
                v = e["nq"]["dailySaleVelocity"]["dc"]["quantity"]
            except Exception as ex:
                # couldn't find velocity for dc specifically, just skip
                continue
            #print(f'id: {id} | v: {v}')
            r = requests.get(f'https://xivapi.com/item/{id}')
            name = r.json()["Name_en"]
            out_list.append({"name": name, "itemId": id, "dailySaleVelocity": v})
            time.sleep(.05)
        time.sleep(.05)
    
    out_list.sort(key=extract_velocity, reverse=True)
    json_obj = json.dumps(out_list, indent=4)
    with open("data/json/names_velocity.json", "w") as outfile:
        outfile.write(json_obj)
    '''
    
    '''
    out_list = []
    
    items = "44300,44301,44302"
    
    #uri = f'/api/v2/aggregated/{worldDcRegion}/{itemIds}'
    uri = f'https://universalis.app/api/v2/aggregated/{dc_name}/{items}'
    response = requests.get(uri)
    #print(response.json())
    j = response.json()["results"]
    #print(j)
    for e in j:
        id = e["itemId"]
        v = e["nq"]["dailySaleVelocity"]["dc"]["quantity"]
        #print(f'id: {id} | v: {v}')
        out_list.append({"itemId": id, "dailySaleVelocity": v})

    #print(out_list)
    
    # wait .05 seconds between requests
    
    
    
    json_obj = json.dumps(out_list, indent=4)
    with open("data.json", "w") as outfile:
        outfile.write(json_obj)
    '''
    
    
    
    
    
    
    '''
    # get NA world ids
    na_worlds_ids = []
    response = requests.get("https://universalis.app/api/v2/data-centers")
    for j in response.json():
        if j["region"] == "North-America":
            jprint(j)
            na_worlds_ids.extend(j["worlds"])
            
    print(na_worlds_ids)
    
    # get corresponding names to worlds
    na_worlds = {}
    response = requests.get("https://universalis.app/api/v2/worlds")
    for j in response.json():
        if j["id"] in na_worlds_ids:
            na_worlds[j["id"]] = j["name"]
    
    print(na_worlds)
    '''
    
def main():
    get_velocity_data()
    i=1

if __name__ == "__main__":
    main()