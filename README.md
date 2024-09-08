### TODO

scrap weight
    get a percent score
        average daily transactions
        dc delta
    then get a score out of 200, and use that as weight

    1. Delta between lowest world and kraken
    2. Average items sold per transaction
    3. Average transactions per day

    Multiplying 1 and 2 should give lower delta but higher volume items more weight. Maybe call this potential profit?

    Then rank items like I was thinking by converting potential profit and atd into percentages and then averaging them

    Also list the lowest price in the main table 

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