import requests
from bs4 import BeautifulSoup
from form_request import payload2025 as payload
from form_request import headers2025 as headers


url = "https://play.usaultimate.org/events/tournament/"

session = requests.Session()
page = session.post(url, data=payload, headers=headers)
res = BeautifulSoup(page.content, "html.parser")
# TODO: Change below line to past tournaments once season starts
upcoming_events = res.find(id="CT_HP_Mid_1_pnlCurrent")
past_events = res.find(id="CT_HP_Mid_1_gvPastEvents")

part1 = past_events.find_all("tr", class_="row")
part2 = past_events.find_all("tr", class_="alternate alt")

# TODO: load games from all pages

tournament_urls = []
for x in part1+part2:
    tournament_urls.append("https://play.usaultimate.org" + x.find("a", href=True)['href'])









