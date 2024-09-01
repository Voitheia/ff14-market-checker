import json
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