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

### Rate Limiting
When initially running the webscraper, my network was timed-out by the USAU
website apparently due to the increadibly high number of requests I was sending
per minute. So, to avoid this issue I decided to set the ammount of time the
scraping would occur over (Lowest I've gotten to work is 1hr) and then through
testing, approximate the number of requests needed to be sent. Then, using a
simple formula:
```
DELAY_BETWEEN_REQUESTS = SCRAPE_PERIOD / NUM_REQUESTS
```
I am able to determine a delay that I will have to add to each request so that
the sraper will not trigger the website's rate limiting.

To achieve this I simply created a wrapper function for the selenium
`driver.get(url)` function that calls `time.sleep(DELAY_BETWEEN_REQUESTS)` every
time we get a new url for the driver.

## USAU Algorithm
Part of the reason I've been so excited about this whole project is the chance
to interact and work with such a interesting algorithm.

You can read about the algorithm from the source at the top of the page but I
will restate the main themes and describe my intended implementation details
for my own sake as well as yours.

At a very high level, we assign each game a rating for each team, and that
rating is then averaged for each team to give them a team rating.

But I think this simple definition hides the most beautiful part about the
algorithm, which is the iterative nature of the averaging process and the fact
that the way we stop the algorithm is when the ratings have stabalized.

### Implementation Details
From the webscraper, I expect a list of every game that has happened in a given
season (so far, if current) with a date of the game, score for and against, the
'home' team and the opposing team.

Quick sidenote but the reason why there are acctually two entries in the results
dataframe for each game played, one for each team, is because of the way the
webscraping works. This acctually works out well for us since it makes it easy
to split up games between teams.

The main datastructure at play will be pandas' Dataframe, which I chose only
since I have used them before. But either way, the webscraper will return our
'results' dataframe, which will contain 5 columns, in this order
```
"Date String", "Tournament", "Score(F,A)", "Team Name", "Opponent"
```
The Date String will look something like so "January 1" since that is how it's
stored on the USAU website.
Now, we need to figure out how we want to store the games while they are being
passed through the algorithm...

Well, as it in right now, we can get rid of the tournament name for now, we can
add it back later if we want to look at stats like rating differential over a
whole tournament, but for now we can overlook it. We need to add a rating
column, since the game rating will depend on what teams perspective you look at
it from.

For example Team A has a rating of 1000 points, while Team B has a rating of 500
points. For a given game where Team B beats Team A with a rating difference of
200 points. The game rating for this given game will be 800 and 700 for Teams A
and B respectively

So, to store that information, we will add 5 additional columns, the 'home' team
rating, the raw game score differential, the date weight, the score weight and
finally the effect of a game.

Now, the ratings dataframe will have the following columns:
```
"Date String", "Tournament", "Score(F,A)", "Team Name", "Opponent", "Team Rating",
   "Game Rating", "Date Weight", "Score Weight", "Game Effect"
```
At the start of each iteration, we will calculate the game rating of each game,
then update the Team Rating column. Since the Date Weight and Score Weight are
constant, we dont need to worry about updating those.

### Performance
The first working ratings test of the 2025 season, minus post season (oops) is
taking about 12 seconds per iteration, and we have the threshold set to 0.01. It
took 177 iterations to reach the threshold. Also, more importanly, it looks like
I've made an error in some way and the ratings are _way_ lower than expected, on
average around the 500 mark.

After fixing this issue I was able to use the cProfile Python module to profile
the algorithm and find what lines of code were using the most reasorces.
