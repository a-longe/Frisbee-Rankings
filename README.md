# Frisbee Rankings

This is a passion project recreating the official USAU ranking alogrithm, found
[here](https://play.usaultimate.org/teams/events/rankings/#algorithm).

To create it I will be webscaping the USAU calendar website to find all of the
sactioned games, which will be loaded into a pandas dataframe.

Then, I will pass the dataframe into an alogrithm (the offical USAU one to start
with), which will return a ranking of each team.
