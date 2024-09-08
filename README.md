### TODO

think of way to make how market data is stored more efficient. do i just make a custom object for market data and attach a list of them to an item rather than having the market data in a separate table? is that more efficient?
    i might've already done this with market_data_list?

i'm not sure what i did with the weight really did anything
    i need to look into the data more to make sure its calculating correctly and its getting displayed correctly

list the lowest price in the main table
update main table to reflect weight changes 

make whole row on main page clickable, sends you to the universalis page for that item

might need to tweak how database is organized so that data pulled from universalis is separate from statistics i calculate

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
run the django server with the profiler and output to file
- `austin -s python .\manage.py runserver > ../sample.austin`


### References

https://docs.universalis.app/

https://github.com/CameronDeweerd/FFXIV-Market-Calculator

https://xivapi.com/docs
https://xivapi.com/docs/Icons