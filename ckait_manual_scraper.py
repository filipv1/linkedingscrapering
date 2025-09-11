import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class CkaitManualScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.setup_driver()
        self.results = []
        
    def setup_driver(self):
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
            
        # Anti-detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
    def open_site_for_manual_filtering(self):
        """Open CKAIT site and wait for user to manually filter"""
        try:
            print("=== CKAIT MANUAL FILTERING ===")
            print("Opening CKAIT expert page for manual filtering...")
            
            # Navigate to target page
            self.driver.get("https://www.ckait.cz/expert")
            time.sleep(3)
            
            print("\n" + "="*60)
            print("MANUAL FILTERING INSTRUCTIONS:")
            print("1. In the browser, select 'Stavbyvedoucí' filter")  
            print("2. Click 'Hledat' button")
            print("3. Wait for results to load")
            print("4. Press Enter here when ready for scraping...")
            print("="*60)
            
            input("Press Enter when filtering is done and results are displayed: ")
            
            print("Manual filtering completed. Starting automatic scraping...")
            return True
            
        except Exception as e:
            print(f"Error opening site: {e}")
            return False
    
    def scrape_current_results(self):
        """Scrape whatever results are currently displayed"""
        try:
            print("=== AUTOMATIC SCRAPING ===")
            print("Scraping displayed results...")
            
            # Find the results table - try multiple selectors
            table = None
            table_selectors = [
                "table.responsive-enabled",
                "table[data-striping='1']", 
                "table",
                ".view-content table",
                ".views-table"
            ]
            
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found table with selector: {selector}")
                    break
                except:
                    continue
                    
            if not table:
                print("❌ No table found - checking page content...")
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                if "Žádný obsah není k dispozici" in page_text:
                    print("❌ No results found - page shows 'Žádný obsah není k dispozici'")
                    print("Please check if filtering worked correctly")
                else:
                    print(f"Page content preview: {page_text[:200]}...")
                return False
            
            # Find all data rows
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            print(f"Found {len(rows)} result rows")
            
            if len(rows) == 0:
                print("❌ No data rows found in table")
                return False
                
            # Check if it's the empty message row
            if len(rows) == 1:
                first_row_text = rows[0].text.strip()
                if "žádný obsah" in first_row_text.lower():
                    print(f"❌ Empty results: '{first_row_text}'")
                    return False
            
            # Extract data from each row
            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 6:
                        # Extract member number (first column with link)
                        member_number_cell = cells[0]
                        try:
                            member_link = member_number_cell.find_element(By.TAG_NAME, "a")
                            member_number = member_link.text.strip()
                            member_url = "https://www.ckait.cz" + member_link.get_attribute('href')
                        except:
                            member_number = member_number_cell.text.strip()
                            member_url = ""
                        
                        # Extract other data
                        surname = cells[1].text.strip()
                        firstname = cells[2].text.strip()
                        
                        # Extract address (handle complex structure)
                        address_parts = []
                        address_cell = cells[3]
                        address_items = address_cell.find_elements(By.TAG_NAME, "li")
                        if address_items:
                            for item in address_items:
                                if item.text.strip():
                                    address_parts.append(item.text.strip())
                        else:
                            # Fallback to cell text if no list items
                            address_parts = [address_cell.text.strip()]
                        address = ", ".join(address_parts)
                        
                        # Svobodny inzenyr
                        svobodny_ing = cells[4].text.strip() if len(cells) > 4 else ""
                        
                        # Extract obor (field specializations)
                        obor_parts = []
                        if len(cells) > 5:
                            obor_cell = cells[5]
                            obor_spans = obor_cell.find_elements(By.TAG_NAME, "span")
                            for span in obor_spans:
                                title = span.get_attribute('title')
                                if title:
                                    obor_parts.append(title)
                            if not obor_parts:
                                # Fallback to cell text
                                obor_text = obor_cell.text.strip()
                                if obor_text:
                                    obor_parts = [obor_text]
                        obor = "; ".join(obor_parts)
                        
                        # Store result
                        result = {
                            'member_number': member_number,
                            'surname': surname,
                            'firstname': firstname,
                            'address': address,
                            'svobodny_ing': svobodny_ing,
                            'obor': obor,
                            'profile_url': member_url
                        }
                        
                        self.results.append(result)
                        print(f"✅ Extracted: {member_number} - {firstname} {surname}")
                        
                    else:
                        print(f"Row {i+1}: Only {len(cells)} cells (expected 6+)")
                        
                except Exception as e:
                    print(f"Error extracting row {i+1}: {e}")
                    continue
                    
            print(f"✅ Successfully extracted {len(self.results)} records")
            return True
            
        except Exception as e:
            print(f"Scraping error: {e}")
            return False
    
    def save_to_csv(self, filename='ckait_stavbyvedouci_manual.csv'):
        """Save results to CSV file"""
        try:
            print(f"Saving {len(self.results)} records to {filename}...")
            
            if not self.results:
                print("❌ No results to save")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = self.results[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write data
                for result in self.results:
                    writer.writerow(result)
                    
            print(f"✅ Data saved to {filename}")
            print(f"Total records: {len(self.results)}")
            return True
            
        except Exception as e:
            print(f"CSV save error: {e}")
            return False
    
    def scrape_all_pages(self):
        """Scrape all pages with pagination support"""
        page_number = 1
        
        while True:
            print(f"\n=== SCRAPING PAGE {page_number} ===")
            
            # Scrape current page
            if not self.scrape_current_page():
                print(f"❌ Failed to scrape page {page_number}")
                break
                
            # Check for "Další" (next) button
            next_button = self.find_next_button()
            
            if next_button:
                print(f"Found 'Další' button - going to page {page_number + 1}")
                
                try:
                    # Click next button with multiple strategies
                    if self.click_next_button(next_button):
                        time.sleep(3)  # Wait for page to load
                        page_number += 1
                        print(f"Successfully moved to page {page_number}")
                        continue
                    else:
                        print("❌ Failed to click next button")
                        break
                        
                except Exception as e:
                    print(f"Error clicking next button: {e}")
                    break
            else:
                print("✅ No more pages - scraping completed!")
                break
                
        print(f"\n🎉 SCRAPING FINISHED!")
        print(f"Total pages scraped: {page_number}")
        print(f"Total records collected: {len(self.results)}")
        return True
    
    def scrape_current_page(self):
        """Scrape whatever results are currently displayed on this page"""
        try:
            # Find the results table - try multiple selectors
            table = None
            table_selectors = [
                "table.responsive-enabled",
                "table[data-striping='1']", 
                "table",
                ".view-content table",
                ".views-table"
            ]
            
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found table with selector: {selector}")
                    break
                except:
                    continue
                    
            if not table:
                print("❌ No table found - checking page content...")
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                if "Žádný obsah není k dispozici" in page_text:
                    print("❌ No results found - page shows 'Žádný obsah není k dispozici'")
                    print("Please check if filtering worked correctly")
                else:
                    print(f"Page content preview: {page_text[:200]}...")
                return False
            
            # Find all data rows
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            print(f"Found {len(rows)} result rows on current page")
            
            if len(rows) == 0:
                print("❌ No data rows found in table")
                return False
                
            # Check if it's the empty message row
            if len(rows) == 1:
                first_row_text = rows[0].text.strip()
                if "žádný obsah" in first_row_text.lower():
                    print(f"❌ Empty results: '{first_row_text}'")
                    return False
            
            # Extract data from each row
            page_results = 0
            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 6:
                        # Extract member number (first column with link)
                        member_number_cell = cells[0]
                        try:
                            member_link = member_number_cell.find_element(By.TAG_NAME, "a")
                            member_number = member_link.text.strip()
                            member_url = "https://www.ckait.cz" + member_link.get_attribute('href')
                        except:
                            member_number = member_number_cell.text.strip()
                            member_url = ""
                        
                        # Extract other data
                        surname = cells[1].text.strip()
                        firstname = cells[2].text.strip()
                        
                        # Extract address (handle complex structure)
                        address_parts = []
                        address_cell = cells[3]
                        address_items = address_cell.find_elements(By.TAG_NAME, "li")
                        if address_items:
                            for item in address_items:
                                if item.text.strip():
                                    address_parts.append(item.text.strip())
                        else:
                            # Fallback to cell text if no list items
                            address_parts = [address_cell.text.strip()]
                        address = ", ".join(address_parts)
                        
                        # Svobodny inzenyr
                        svobodny_ing = cells[4].text.strip() if len(cells) > 4 else ""
                        
                        # Extract obor (field specializations)
                        obor_parts = []
                        if len(cells) > 5:
                            obor_cell = cells[5]
                            obor_spans = obor_cell.find_elements(By.TAG_NAME, "span")
                            for span in obor_spans:
                                title = span.get_attribute('title')
                                if title:
                                    obor_parts.append(title)
                            if not obor_parts:
                                # Fallback to cell text
                                obor_text = obor_cell.text.strip()
                                if obor_text:
                                    obor_parts = [obor_text]
                        obor = "; ".join(obor_parts)
                        
                        # Store result
                        result = {
                            'member_number': member_number,
                            'surname': surname,
                            'firstname': firstname,
                            'address': address,
                            'svobodny_ing': svobodny_ing,
                            'obor': obor,
                            'profile_url': member_url
                        }
                        
                        self.results.append(result)
                        page_results += 1
                        print(f"✅ Extracted: {member_number} - {firstname} {surname}")
                        
                    else:
                        print(f"Row {i+1}: Only {len(cells)} cells (expected 6+)")
                        
                except Exception as e:
                    print(f"Error extracting row {i+1}: {e}")
                    continue
                    
            print(f"✅ Page completed: {page_results} records extracted")
            return True
            
        except Exception as e:
            print(f"Scraping error: {e}")
            return False
    
    def find_next_button(self):
        """Find the 'Další' (next) pagination button"""
        try:
            # Try multiple selectors for next button
            next_selectors = [
                'a[rel="next"]',
                'a[title*="Přejít na další"]',
                'a[href*="?page="]',
                '.pager-next a',
                '.pagination .next a'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found next button with selector: {selector}")
                    print(f"Button text: '{next_button.text}' href: '{next_button.get_attribute('href')}'")
                    return next_button
                except:
                    continue
                    
            # Additional fallback - look for any link with "Další" text
            try:
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    if "další" in link.text.lower() or "›" in link.text:
                        print(f"Found next button by text: '{link.text}'")
                        return link
            except:
                pass
                
            print("❌ No next button found")
            return None
            
        except Exception as e:
            print(f"Error finding next button: {e}")
            return None
    
    def click_next_button(self, next_button):
        """Click next button with multiple strategies"""
        try:
            # Strategy 1: Scroll to element and wait
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                self.wait.until(EC.element_to_be_clickable(next_button))
                next_button.click()
                print("✅ Clicked next button with scroll + wait")
                return True
            except Exception as e:
                print(f"Strategy 1 failed: {e}")
            
            # Strategy 2: JavaScript click
            try:
                self.driver.execute_script("arguments[0].click();", next_button)
                print("✅ Clicked next button with JavaScript")
                return True
            except Exception as e:
                print(f"Strategy 2 failed: {e}")
            
            # Strategy 3: Direct navigation to href
            try:
                href = next_button.get_attribute('href')
                if href:
                    self.driver.get(href)
                    print("✅ Navigated directly to next page URL")
                    return True
            except Exception as e:
                print(f"Strategy 3 failed: {e}")
                
            return False
            
        except Exception as e:
            print(f"Click next button error: {e}")
            return False

    def close(self):
        self.driver.quit()

def main():
    print("=== CKAIT MANUAL + AUTO SCRAPER ===")
    print("Hybrid approach: Manual filtering + Automatic scraping")
    
    scraper = CkaitManualScraper(headless=False)
    
    try:
        # Step 1: Open site for manual filtering
        if scraper.open_site_for_manual_filtering():
            
            # Step 2: Automatic scraping of all pages with pagination
            if scraper.scrape_all_pages():
                
                # Step 3: Save to CSV
                scraper.save_to_csv()
                
                print("\n✅ CKAIT SCRAPING COMPLETED SUCCESSFULLY!")
                print("Check the CSV file for results")
            else:
                print("\n❌ SCRAPING FAILED")
                print("Please check if the filtering worked correctly")
        else:
            print("\n❌ COULD NOT OPEN SITE")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        scraper.close()

if __name__ == "__main__":
    main()