import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from komkom_scraper.pipelines import PostgresUpsertPipeline

SEARCH_QUERIES = ["opportunité entrepreneuriale Sénégal"]


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def extract_results(driver):
    results = []
    for result in driver.find_elements(By.CSS_SELECTOR, "div.g"):
        h3s = result.find_elements(By.CSS_SELECTOR, "h3")
        title_elem = h3s[0] if h3s else None
        if not title_elem:
            continue
        title = title_elem.text.strip()
        parent_links = title_elem.find_elements(By.XPATH, "./ancestor::a[1]")
        parent = parent_links[0] if parent_links else None
        url = parent.get_attribute("href") if parent else None

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
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            driver.get(search_url)
            pages_scraped = 0

            while pages_scraped < 3:
                time.sleep(random.uniform(1, 2))
                items = extract_results(driver)
                for item in items:
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