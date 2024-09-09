### TODO



list the lowest price in the main table
update main table to reflect weight changes 

i think i need to eliminate the line `Market_Data.objects.filter(item=i)` in calculate_item_stats_worker?
    move market_data_list into the Item model, populate when market data is pulled, then use here?

maybe the way i'm making api requests can be improved
    if i make my api requests less lengthy then the server should respond quicker?

make configuration page so i can choose how things are compared, like to what world is the baseline?

find and add some css or something to make the table not look like shit, and maybe make it user sortable

fix the bug where both the calculating pages will send you back to the index, but the url still looks like the previous page

## main page
list of top 100 most interesting items on market, use `index.html` template

### table

|  | Name | Velocity | Region Delta | DC Delta |
| ---- | ---- | ---- | ---- | ---- |
| Item Icon | Item Name | velocity data (how<br>quickly its selling) | high/low price delta<br> within NA region | high/low price delta<br> within Dynamis |
| ![Fire Crystal](ff14_market_checker\delta_checker\static\icons\8.png) | Fire Crystal | 298764.30 | 10<br>80@Behemoth(Primal)<br>90@Kraken(Dynamis) | 5<br>85@Seraph(Dynamis)<br>90@Kraken(Dynamis) |

## item page
list more specific market data for an item, use `item.html` template

have icon and item name at top of page above table

### table


### commands

move to dir with main django script
- `cd .\ff14_market_checker\`
stage changes to the database model
- `python .\manage.py makemigrations`
push changes to the database model
- `python .\manage.py migrage`
run the django server
- `python .\manage.py runserver`



### References

https://docs.universalis.app/

https://github.com/CameronDeweerd/FFXIV-Market-Calculator

https://xivapi.com/docs
https://xivapi.com/docs/Icons