from functools import total_ordering
import requests

from time import sleep, time

import pandas as pd

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

session = requests.Session()
URL = "https://play.usaultimate.org/events/tournament/"
options = Options()
options.add_argument("--headless")
options.add_argument("--blink-settings=imagesEnabled=false")
driver = webdriver.Chrome(options=options)

RESULT_DATE = 0
RESULT_SCORE = 1
RESULT_OPP = 2

# 60min * 60sec = 1h
SEC_PER_HR = 60*60
SCRAPE_PERIOD = 1*SEC_PER_HR
# found in testing for 2025 season
TOTAL_ACTIONS = 1238
# 1-0.78 = 0.22, expected time spend fufilling requests
DELAY_BETWEEN_ACTIONS = (SCRAPE_PERIOD / TOTAL_ACTIONS)*0.78



# total request count
# - any javascript redirects...
total_request_count = 0

def get_url_w_delay(cur_driver: WebDriver, url):
    global total_request_count
    total_request_count = total_request_count + 1
    cur_driver.get(url)
    sleep(DELAY_BETWEEN_ACTIONS)


def get_tournament_urls_on_page(cur_page: WebDriver) -> list[str]:
    completed_events = cur_page.find_element(By.ID, "CT_HP_Mid_1_gvPastEvents")
    rows = completed_events.find_elements(By.CSS_SELECTOR, "tr.row")
    rows += completed_events.find_elements(By.CSS_SELECTOR, "tr.alt.alternate")

    return [row.find_element(By.TAG_NAME, "a").get_attribute("href") for row in rows]


def get_2025_tournaments() -> list[str]:
    get_url_w_delay(driver, URL)

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
    get_url_w_delay(driver, tournament_url)

    try:
        mens_section_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "dl.groupType"))
        )
    except TimeoutException:
        # tournament information has not been posted
        print(f"WARNING: Events have not been posted: {tournament_url}")
        return []

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
        sleep(1)

        _ = WebDriverWait(driver, 10).until(
            lambda d: driver.current_url != tournament_url
        )

        event_urls.append(driver.current_url)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    return event_urls


def get_team_urls(event_url) -> list[str]:
    get_url_w_delay(driver, event_url)

    try:
        pools = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.pool"))
        )
    except TimeoutException:
        # pools have not been posted yet
        print(f"WARNING: Pools not posted: {event_url}")
        return []

    team_links = []
    for pool in pools:
        team_links += list(map(lambda e: e.get_attribute("href"), \
                          pool.find_elements(By.TAG_NAME, "a")))

    return team_links


def get_results(tournament_url) -> pd.DataFrame:
    event_urls = get_event_urls(tournament_url)
    team_urls = [team_url for event_url in event_urls \
        for team_url in get_team_urls(event_url)]


    tournament_results = [get_team_results(team_url) for team_url in team_urls]

    if len(tournament_results) == 0:
        return pd.DataFrame() # empty

    return pd.concat(tournament_results).reset_index()\
        .drop(columns=['index']).drop_duplicates()


def get_team_results(team_event_url) -> pd.DataFrame:
    get_url_w_delay(driver, team_event_url)

    if driver.current_url == "https://play.usaultimate.org/":
        # team has been deleted
        print(f"WARNING: Team has been deleted {team_event_url}")
        return pd.DataFrame()

    results_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "CT_Right_0_gvEventScheduleScores"))
    )

    tournament_name = driver.find_element(By.ID, "CT_Right_1_lblHeading").text

    unformatted_team_name = driver.find_element(By.ID, "CT_Main_0_ucTeamDetails_lnkTeamName")\
        .text

    # remove acroym and space between
    team_name = unformatted_team_name.split('(')[0].strip()
    if team_name.endswith("-B"):
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

        if len(score_str) == 0:
            # score not reported
            continue
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
    tourny_urls = get_2025_tournaments()
    results = []
    count = 0
    start_time = time()
    for tourny_url in tourny_urls:
        print(f"Completed {count}/82: {100*total_request_count/TOTAL_ACTIONS:.2f}%", end='\r')
        results.append(get_results(tourny_url))
        count += 1

    return pd.concat(results).reset_index()\
        .drop(columns=['index']).drop_duplicates()
    print(f"Total Time = {time() - start_time:.1f}s")
    print(f"Total Requests = {total_request_count}")
    return results
