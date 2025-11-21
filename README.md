# Frisbee Rankings

This is a passion project recreating the official USAU ranking alogrithm, found
[here](https://play.usaultimate.org/teams/events/rankings/#algorithm).

To create it I will be webscaping the USAU calendar website to find all of the
sactioned games, which will be loaded into a pandas dataframe.

Then, I will pass the dataframe into an alogrithm (the offical USAU one to start
with), which will return a ranking of each team.

## Webscaping
Since the format of the results page of each tournament will be very hard to
parse, we will just use the first page, grab the tournament results of each team
for each tournament and load results from that.

So the scraping workflow will look something like so:
1. Load Tournaments page on USAU
2. Load next page until complete
3. For each Tournament:
    1. Load all teams competing's tournament results page
    2. Scrape results from that
