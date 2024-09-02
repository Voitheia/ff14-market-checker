### TODO
next thing to do would be to pick a certain amount of items, maybe the 100 highest velocity, and pull current market price data for those items for each of those items.
i also should ideally pull item information for each marketable item and save them all to a json file since those are static, and make that separate from market data
then, i could also pull price history to see what those items usually sell at.
i need to get the delta between the lowest listed price within the dc and somewhere its listed high, and then whatever has those the highest should give me the best margins
for now this can just be data, but after the base functionality is working, it would be nice to built it into a django app so i can have a sortable table
probably also a good idea to put the data into a database instead of just json eventually. though maybe i don't want to do a database cause if the structure changes i'll have to rebuild it? maybe just stay json for a while until everything else is done?
it also seems like the three older NA dcs tend to be quite a lot less expensive than dynamis, so i might also want to compare price data across the whole region

### References

https://docs.universalis.app/

https://github.com/CameronDeweerd/FFXIV-Market-Calculator

https://xivapi.com/docs
https://xivapi.com/docs/Icons