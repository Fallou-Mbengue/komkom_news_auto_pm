import random
import time
import uuid
from datetime import datetime, timezone
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

import sys
sys.path.append('/app/scraper')  # Ensures komkom_scraper package is resolvable when script is executed via mounted volume.

from komkom_scraper.pipelines import PostgresUpsertPipeline

SEARCH_QUERIES = ["opportunité entrepreneuriale Sénégal"]

def clean_text(text):
    return text.strip() if text else None

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
    search_results = driver.find_elements(By.CSS_SELECTOR, 'div.g')
    print(f"DEBUG: Found {len(search_results)} potential search results on this page.")

    for result in search_results:
        try:
            # Extract title
            title_elements = result.find_elements(By.CSS_SELECTOR, 'h3')
            title_elem = title_elements[0] if title_elements else None
            title = clean_text(title_elem.text) if title_elem else None

            # Extract URL
            url = None
            parent_links = title_elem.find_elements(By.XPATH, "./ancestor::a[1]") if title_elem else []
            if parent_links:
                url = parent_links[0].get_attribute("href")

            # Extract description/snippet
            description = None
            try:
                snippet_elem = result.find_element(By.CSS_SELECTOR, 'div.IsZzjf span')
                description = clean_text(snippet_elem.text)
            except:
                try:
                    snippet_elem = result.find_element(By.CSS_SELECTOR, 'div.VwiC3b span')
                    description = clean_text(snippet_elem.text)
                except:
                    pass

            if title and url and "google.com/search?" not in url:
                now = datetime.now(timezone.utc)
                item = {
                    "id": str(uuid.uuid4()),
                    "source_id": f"Google Search_{uuid.uuid4().hex}",
                    "title": title,
                    "description": description,
                    "source_url": url,
                    "source": "Google Search",
                    "opportunity_type": "Opportunité Entrepreneuriale",
                    "eligibility_criteria": None,
                    "application_deadline": None,
                    "publication_date": None,
                    "sector": None,
                    "stage": None,
                    "amount": None,
                    "scraped_at": now,
                    "updated_at": now
                }
                results.append(item)
                print(f"DEBUG: Successfully processed item: Title='{item['title']}' URL='{item['source_url']}'")
            else:
                print(f"DEBUG: Skipping result (no title/URL or internal Google link): {title} - {url}")
        except Exception as e:
            print(f"ERROR: Failed to extract data from a search result block: {e}")
            # print(result.get_attribute('outerHTML')) # Uncomment for more debugging if needed
    return results

def main():
    pipeline = PostgresUpsertPipeline()
    pipeline.open_spider(None)
    driver = setup_driver()
    try:
        for query in SEARCH_QUERIES:
            # Use urllib.parse.quote to encode the query safely
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            print(f"DEBUG: Navigating to Google Search: {search_url}")
            driver.get(search_url)
            pages_scraped = 0

            while pages_scraped < 3:
                time.sleep(random.uniform(2, 4))
                # CAPTCHA/Blocker check
                if "captcha" in driver.current_url or "Sorry..." in driver.page_source:
                    print("WARNING: Google CAPTCHA or blocking page detected. Stopping.")
                    break

                print(f"DEBUG: Scraping page {pages_scraped+1} for query '{query}'")
                items = extract_results(driver)
                for item in items:
                    pipeline.process_item(item, None)
                pages_scraped += 1

                # Pagination
                try:
                    next_btns = driver.find_elements(By.CSS_SELECTOR, "a#pnnext")
                    if not next_btns:
                        print("DEBUG: No 'Next' button found. Ending pagination.")
                        break
                    print("DEBUG: Clicking 'Next' button to go to next results page.")
                    next_btns[0].click()
                except Exception as e:
                    print(f"ERROR: Failed to click 'Next' button: {e}")
                    break
    except Exception as e:
        print(f"ERROR: Error navigating or processing pages: {e}")
    finally:
        driver.quit()
        pipeline.close_spider(None)

if __name__ == "__main__":
    main()