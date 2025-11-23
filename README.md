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


### Switching to Selenium
When trying to scrape the USAU results website, the searching functionality turns
out to be an archaic design such that the whole dataset is not loaded to the page
to begin with so we need to submit the correct webform.

The other big issue is that the webform returns a whole html page but importantly,
dynamically loads it.

Because of these two reasons, instead of using the simpler BeautifulSoup, we will
use the webdriver driven package called Selenium. We will use this to interact
with the website like submitting the correct settings into the search
functionality. And it allows us to go to the next page since it is not a seperate
url but instead calls a javascript function that loads the html of the next page
into our current page.
