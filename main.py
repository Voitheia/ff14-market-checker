import json
import time
import requests

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

def main():
    
    items_list = []
    with open('marketable.json') as f:
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
            out_list.append({"itemId": id, "dailySaleVelocity": v})
        time.sleep(.05)
    
    json_obj = json.dumps(out_list, indent=4)
    with open("data.json", "w") as outfile:
        outfile.write(json_obj)
    
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
    
    

if __name__ == "__main__":
    main()