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
    pass

def get_2025_results() -> pd.DataFrame:
    pass

urls = get_2025_tournaments()
event_urls = []
for tournament_url in urls:
    event_urls += get_event_urls(tournament_url)
