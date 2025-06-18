import os
import time
import random
from typing import Optional, List
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from komkom_scraper.items import OpportunityItem
from komkom_scraper.pipelines import PostgresUpsertPipeline

SEARCH_QUERIES = ["opportunité entrepreneuriale Sénégal"]

def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--ignore-certificate-errors")
    # Path to Chromium/chromedriver if needed (Debian slim images)
    chrome_options.binary_location = "/usr/bin/chromium"
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_results(driver) -> List[dict]:
    results = []
    for result in driver.find_elements(By.CSS_SELECTOR, "div.g"):
        # Title and URL
        title_elem = result.find_element(By.CSS_SELECTOR, "h3") if len(result.find_elements(By.CSS_SELECTOR, "h3")) else None
        if not title_elem:
            continue
        title = title_elem.text.strip()
        # Find the ancestor <a> of the h3
        parent = title_elem.find_element(By.XPATH, "./ancestor::a[1]") if len(title_elem.find_elements(By.XPATH, "./ancestor::a[1]")) else None
        url = parent.get_attribute("href") if parent else None

        # Description snippet
        snippet = None
        snippet_elems = result.find_elements(By.CSS_SELECTOR, "div.IsZzjf span")
        if snippet_elems:
            snippet = snippet_elems[0].text.strip()
        else:
            snippet_elems = result.find_elements(By.CSS_SELECTOR, "div.VwiC3b span")
            if snippet_elems:
                snippet = snippet_elems[0].text.strip()

        if title and url:
            item = {
                "title": title,
                "url": url,
                "source_url": url,
                "source": "Google Search",
                "opportunity_type": "Opportunité Entrepreneuriale",
                "description": snippet if snippet else None,
                "eligibility_criteria": None,
                "application_deadline": None,
                "publication_date": None,
            }
            results.append(item)
    return results

def main():
    pipeline = PostgresUpsertPipeline()
    pipeline.open_spider(None)
    driver = setup_driver()
    try:
        for query in SEARCH_QUERIES:
            # Google search URL with query
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            driver.get(search_url)
            pages_scraped = 0

            while pages_scraped < 3:
                time.sleep(random.uniform(1, 2))
                items = extract_results(driver)
                for item in items:
                    # OpportunityItem is a subclass of dict, but for the pipeline we can pass dicts too
                    pipeline.process_item(item, None)
                pages_scraped += 1
                try:
                    next_btns = driver.find_elements(By.CSS_SELECTOR, "a#pnnext")
                    if not next_btns:
                        break
                    next_btns[0].click()
                except Exception:
                    break
    finally:
        driver.quit()
        pipeline.close_spider(None)

if __name__ == "__main__":
    main()