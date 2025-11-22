import requests

import pandas as pd

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.support.ui import Select, WebDriverWait

from form_request import payload2025 as payload
from form_request import headers2025 as headers


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
    comp_lvl = Select(driver.find_element(By.ID, "CT_HP_Mid_1_drpCompetitionLevelId"))
    event_type = Select(driver.find_element(By.ID, "CT_HP_Mid_1_drpEventTypeId"))
    season = Select(driver.find_element(By.ID, "CT_HP_Mid_1_drpSeasonId"))
    from_date = driver.find_element(By.ID, "CT_HP_Mid_1_dpDateFrom_cal")
    submit_btn = driver.find_element(By.ID, "CT_HP_Mid_1_btnSubmit")
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
        print(next_btn.get_attribute("outerHTML"))
        next_btn.click()

        _ = WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.TAG_NAME, "nobr")[-1].text != page_element_text
        )
        page_element = driver.find_elements(By.TAG_NAME, "nobr")[-1]
        page_element_text = page_element.text

        tournament_urls += get_tournament_urls_on_page(driver)

    return tournament_urls

def get_team_urls(tournament_url) -> list[str]:
    pass

def get_results(tournament_url) -> pd.DataFrame:
    pass

def get_team_results(team_event_url) -> pd.DataFrame:
    pass

def get_2025_results() -> pd.DataFrame:
    pass

urls = get_2025_tournaments()
