from typing import NamedTuple
from numpy.char import isdigit
import requests

from time import sleep

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

session = requests.Session()
url = "https://play.usaultimate.org/events/tournament/"
options = Options()
#options.add_argument("--headless")
options.add_argument("--blink-settings=imagesEnabled=false")
driver = webdriver.Chrome(options=options)

RESULT_DATE = 0
RESULT_SCORE = 1
RESULT_OPP = 2

SCRAPE_PERIOD = 60*60
# 5 pages, 85 tournaments, 100 events x 20 teams
TOTAL_ACTIONS = 5+85+(100*20)
DELAY_BETWEEN_ACTIONS = SCRAPE_PERIOD / TOTAL_ACTIONS


def get_tournament_urls_on_page(cur_page: WebDriver) -> list[str]:
    completed_events = cur_page.find_element(By.ID, "CT_HP_Mid_1_gvPastEvents")
    rows = completed_events.find_elements(By.CSS_SELECTOR, "tr.row")
    rows += completed_events.find_elements(By.CSS_SELECTOR, "tr.alt.alternate")

    return [row.find_element(By.TAG_NAME, "a").get_attribute("href") for row in rows]


def get_2025_tournaments() -> list[str]:
    driver.get(url)

    submit_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "CT_HP_Mid_1_btnSubmit"))
    )
    comp_lvl = Select(driver.find_element(By.ID, "CT_HP_Mid_1_drpCompetitionLevelId"))
    event_type = Select(driver.find_element(By.ID, "CT_HP_Mid_1_drpEventTypeId"))
    season = Select(driver.find_element(By.ID, "CT_HP_Mid_1_drpSeasonId"))
    from_date = driver.find_element(By.ID, "CT_HP_Mid_1_dpDateFrom_cal")
    # page element is last "nobr" element on page
    page_element_text = driver.find_elements(By.TAG_NAME, "nobr")[-1].text

    comp_lvl.select_by_visible_text("College - Men")
    event_type.select_by_visible_text("Sanctioned Tournament")
    season.select_by_visible_text("2025")
    from_date.send_keys(r"01/01/2025")
    submit_btn.click()

    _ = WebDriverWait(driver, 10).until(
        lambda d: d.find_elements(By.TAG_NAME, "nobr")[-1].text != page_element_text
    )

    page_element = driver.find_elements(By.TAG_NAME, "nobr")[-1]
    page_element_text = page_element.text
    # get page count
    page_count = int([word for word in page_element.text.split() if word.isdigit()][-1])
    print(f"Page count: {page_count}")

    tournament_urls = []
    tournament_urls += get_tournament_urls_on_page(driver)
    for _ in range(page_count-1): # one page already searched
        next_btn = [e for e in driver.find_elements(By.TAG_NAME, "a") if "»" in e.text][0]
        next_btn.click()

        sleep(1)
        _ = WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.TAG_NAME, "nobr")[-1].text != page_element_text
        )
        page_element = driver.find_elements(By.TAG_NAME, "nobr")[-1]
        page_element_text = page_element.text

        tournament_urls += get_tournament_urls_on_page(driver)

    return tournament_urls


def get_event_urls(tournament_url) -> list[str]:
    driver.get(tournament_url)

    events_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div.eventInfo2"))
    )

    mens_section_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "dl.groupType"))
    )

    button_elements = mens_section_element.find_elements(By.TAG_NAME, "input")
    event_buttons = [button for button in button_elements if "College" in button.get_attribute("value")]
    event_urls = []
    for btn_i in range(len(event_buttons)):
        """
        duplicate current tab, this will be out 'working' tab
        click button on that tab, get url and close
        repeat
        """
        driver.execute_script("window.open(arguments[0], '_blank');", driver.current_url)
        driver.switch_to.window(driver.window_handles[-1])

        mens_section_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "dl.groupType"))
        )

        button_elements = mens_section_element.find_elements(By.TAG_NAME, "input")
        event_button = [button for button in button_elements \
                        if "College" in button.get_attribute("value")][btn_i]
        event_button.click()

        _ = WebDriverWait(driver, 10).until(
            lambda d: driver.current_url != tournament_url
        )

        event_urls.append(driver.current_url)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    return event_urls


def get_team_urls(event_url) -> list[str]:
    driver.get(event_url)

    pools = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.pool"))
    )

    team_links = []
    for pool in pools:
        team_links += list(map(lambda e: e.get_attribute("href"), \
                          pool.find_elements(By.TAG_NAME, "a")))

    return team_links


def get_results(tournament_url) -> pd.DataFrame:
    pass

def get_team_results(team_event_url) -> pd.DataFrame:
    driver.get(team_event_url)

    results_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "CT_Right_0_gvEventScheduleScores"))
    )

    tournament_name = driver.find_element(By.ID, "CT_Right_1_lblHeading").text

    unformatted_team_name = driver.find_element(By.ID, "CT_Main_0_ucTeamDetails_lnkTeamName")\
        .text

    # remove acroym and space between
    team_name = unformatted_team_name.split('(')[0].strip()
    if "-B" in team_name:
        team_name = team_name.replace("-B", "") # remove "-B"
        team_name += " [B]"

    # cull first element since it is header row
    result_elements = results_table.find_elements(By.TAG_NAME, "tr")[1:]

    #Result = NamedTuple('Result', ['date_str', 'tournament', 'score_tuple', 'team', 'opponent'])
    results = []
    for result_element in result_elements:
        date_str = result_element\
            .find_elements(By.TAG_NAME, "span")[0]\
            .text
        score_str = result_element\
            .find_elements(By.TAG_NAME, "span")[1]\
            .text
        score_tuple = (score_str.split()[0], score_str.split()[-1])
        opponent = result_element\
            .find_elements(By.TAG_NAME, "span")[2]\
            .text

        if not score_tuple[0].isdigit() and not score_tuple[1].isdigit():
            # if score is not reported, skip
            continue

        results.append([date_str, tournament_name, score_tuple, team_name, opponent])

    return pd.DataFrame(results, \
        columns=["Date String", "Tournament", "Score(F,A)", "Team Name", "Opponent"])

def get_2025_results() -> pd.DataFrame:
    pass

