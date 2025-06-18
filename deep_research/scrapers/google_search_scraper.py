import random
import time
import uuid
from datetime import datetime, timezone
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
    # Use explicit wait for Google results container.
    try:
        # Google often uses 'div.g' as the primary result container, but this selector may change at any time.
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g'))
        )
    except TimeoutException:
        print("WARNING: Timeout waiting for Google results container. Dumping page source.")
        try:
            with open("google_page_source_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception as e:
            print(f"ERROR: Failed to write page source debug file: {e}")
        try:
            driver.save_screenshot("google_screenshot_debug.png")
        except Exception as e:
            print(f"ERROR: Could not save screenshot: {e}")
        return []

    search_results = driver.find_elements(By.CSS_SELECTOR, 'div.g')  # Google may change this selector.
    print(f"DEBUG: Found {len(search_results)} potential search results on this page.")

    if len(search_results) == 0:
        print("WARNING: Found 0 potential search results. Dumping page source for debugging.")
        try:
            with open("google_page_source_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception as e:
            print(f"ERROR: Failed to write page source debug file: {e}")
        try:
            driver.save_screenshot("google_screenshot_debug.png")
        except Exception as e:
            print(f"ERROR: Could not save screenshot: {e}")

    for idx, result in enumerate(search_results):
        try:
            # Extract title
            try:
                title_elem = result.find_element(By.CSS_SELECTOR, 'h3')
                title = clean_text(title_elem.text)
            except Exception as e:
                print(f"DEBUG: [{idx}] No title found in result block: {e}")
                title_elem = None
                title = None

            # Extract URL
            source_url = None
            try:
                if title_elem:
                    parent_links = title_elem.find_elements(By.XPATH, "./ancestor::a[1]")
                    if parent_links:
                        source_url = parent_links[0].get_attribute("href")
            except Exception as e:
                print(f"DEBUG: [{idx}] Failed to extract parent link for URL: {e}")

            # Extract description/snippet
            description = None
            # Try multiple selectors in order, each with its own try/except:
            try:
                snippet_elem = result.find_element(By.CSS_SELECTOR, 'div.IsZzjf span')
                description = clean_text(snippet_elem.text)
            except Exception:
                try:
                    snippet_elem = result.find_element(By.CSS_SELECTOR, 'div.VwiC3b span')
                    description = clean_text(snippet_elem.text)
                except Exception:
                    try:
                        snippet_elem = result.find_element(By.CSS_SELECTOR, 'span.aCOpRe')
                        description = clean_text(snippet_elem.text)
                    except Exception:
                        pass  # No description found

            # Double-check for Google internal links and missing data
            if title and source_url and "google.com/search?" not in source_url:
                now = datetime.now(timezone.utc)
                item = {
                    "id": str(uuid.uuid4()),
                    "source_id": f"Google Search_{uuid.uuid4().hex}",
                    "title": title,
                    "description": description,
                    "deadline": None,
                    "opportunity_type": "Opportunité Entrepreneuriale",
                    "sector": None,
                    "stage": None,
                    "amount": None,
                    "source_url": source_url,
                    "scraped_at": now,
                    "updated_at": now,
                    "eligibility_criteria": None,
                    "publication_date": None,
                    "source": "Google Search"
                }
                results.append(item)
                print(f"DEBUG: Successfully processed item ({idx}): Title='{item['title']}' URL='{item['source_url']}'")
            else:
                print(f"DEBUG: Skipping result ({idx}) (no title/URL or internal Google link): {title} - {source_url}")
        except Exception as e:
            print(f"ERROR: Failed to extract data from a search result block [{idx}]: {e}")
            # For deep debug, uncomment to dump block HTML:
            # try: print(result.get_attribute('outerHTML')) except: pass
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
                # Explicit wait after page load and before scraping
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g'))
                    )
                except TimeoutException:
                    print("WARNING: Timeout waiting for Google results container (pagination). Dumping page source.")
                    try:
                        with open("google_page_source_debug.html", "w", encoding="utf-8") as f:
                            f.write(driver.page_source)
                    except Exception as e:
                        print(f"ERROR: Failed to write page source debug file: {e}")
                    try:
                        driver.save_screenshot("google_screenshot_debug.png")
                    except Exception as e:
                        print(f"ERROR: Could not save screenshot: {e}")
                    break

                # Add a very small randomized sleep to avoid appearing too robotic.
                time.sleep(random.uniform(0.5, 1.0))

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
                    # Wait for results container to appear again after pagination
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g'))
                        )
                    except TimeoutException:
                        print("WARNING: Timeout after clicking 'Next'. Dumping page source.")
                        try:
                            with open("google_page_source_debug.html", "w", encoding="utf-8") as f:
                                f.write(driver.page_source)
                        except Exception as e:
                            print(f"ERROR: Failed to write page source debug file: {e}")
                        try:
                            driver.save_screenshot("google_screenshot_debug.png")
                        except Exception as e:
                            print(f"ERROR: Could not save screenshot: {e}")
                        break
                    time.sleep(random.uniform(0.5, 1.0))
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