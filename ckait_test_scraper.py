import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class CkaitTestScraper:
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
        
    def test_ckait_filtering(self):
        """Test basic filtering on CKAIT expert page"""
        try:
            print("=== CKAIT SECURITY TEST ===")
            print("Testing filtering functionality...")
            
            # Navigate to target page
            print("1. Opening CKAIT expert page...")
            self.driver.get("https://www.ckait.cz/expert")
            time.sleep(3)
            
            # Find and select stavbyvedouci option
            print("2. Looking for stavbyvedouci filter...")
            
            # Try to find the select element
            select_element = None
            try:
                # Look for select with stavbyvedouci option
                select_elements = self.driver.find_elements(By.TAG_NAME, "select")
                print(f"Found {len(select_elements)} select elements")
                
                for i, select in enumerate(select_elements):
                    options = select.find_elements(By.TAG_NAME, "option")
                    print(f"Select {i+1} has {len(options)} options:")
                    
                    for j, option in enumerate(options):
                        option_text = option.text.strip()
                        option_value = option.get_attribute("value")
                        print(f"  Option {j+1}: value='{option_value}' text='{option_text}'")
                        
                        if "stavbyvedoucí" in option_text.lower() or option_value == "4":
                            select_element = select
                            print(f"✅ Found matching stavbyvedouci option!")
                            break
                    if select_element:
                        break
                        
            except Exception as e:
                print(f"Error finding select element: {e}")
                
            if select_element:
                print("3. Selecting stavbyvedouci...")
                select_obj = Select(select_element)
                try:
                    # Try selecting by value first
                    select_obj.select_by_value("4")
                    print("Selected stavbyvedouci by value=4")
                except:
                    # Fallback: select by text containing stavbyvedouci
                    for option in select_obj.options:
                        if "stavbyvedoucí" in option.text.lower():
                            select_obj.select_by_visible_text(option.text)
                            print(f"Selected stavbyvedouci by text: {option.text}")
                            break
                            
            else:
                print("❌ Could not find stavbyvedouci filter")
                self.debug_page_structure()
                return False
                
            # Find and click search button
            print("4. Looking for search button...")
            search_button = None
            
            try:
                # Try the exact selector from user
                search_button = self.driver.find_element(By.ID, "edit-submit")
                print("Found search button by ID")
            except:
                # Fallback selectors
                selectors = [
                    "input[value='Hledat']",
                    "input[type='submit']",
                    ".button.form-submit",
                    "input.js-form-submit"
                ]
                
                for selector in selectors:
                    try:
                        search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"Found search button with selector: {selector}")
                        break
                    except:
                        continue
                        
            if search_button:
                print("5. Attempting to click search button...")
                
                # Multiple click strategies
                click_success = False
                
                # Strategy 1: Scroll to element and wait
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                    time.sleep(1)
                    self.wait.until(EC.element_to_be_clickable(search_button))
                    search_button.click()
                    click_success = True
                    print("✅ Clicked with scroll + wait")
                except Exception as e:
                    print(f"Strategy 1 failed: {e}")
                
                # Strategy 2: JavaScript click
                if not click_success:
                    try:
                        self.driver.execute_script("arguments[0].click();", search_button)
                        click_success = True
                        print("✅ Clicked with JavaScript")
                    except Exception as e:
                        print(f"Strategy 2 failed: {e}")
                
                # Strategy 3: Actions chain click
                if not click_success:
                    try:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        actions.move_to_element(search_button).click().perform()
                        click_success = True
                        print("✅ Clicked with ActionChains")
                    except Exception as e:
                        print(f"Strategy 3 failed: {e}")
                
                if not click_success:
                    print("❌ All click strategies failed")
                    print("Button state:")
                    print(f"  Displayed: {search_button.is_displayed()}")
                    print(f"  Enabled: {search_button.is_enabled()}")
                    print(f"  Location: {search_button.location}")
                    print(f"  Size: {search_button.size}")
                    return False
                    
                time.sleep(3)
                
                print("✅ SEARCH COMPLETED")
                print(f"Current URL: {self.driver.current_url}")
                
                # Check if we got results and extract data
                if "expert" in self.driver.current_url:
                    print("Search executed successfully - extracting results...")
                    self.extract_results_from_table()
                    return True
                else:
                    print("Unexpected page after search")
                    return False
                    
            else:
                print("❌ Could not find search button")
                self.debug_page_structure()
                return False
                
        except Exception as e:
            print(f"Test error: {e}")
            return False
    
    def extract_results_from_table(self):
        """Extract data from results table"""
        try:
            print("6. Extracting data from table...")
            
            # Find the results table - try multiple selectors
            table = None
            table_selectors = [
                "table.responsive-enabled",
                "table[data-striping='1']", 
                "table",
                ".view-content table"
            ]
            
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found table with selector: {selector}")
                    break
                except:
                    continue
                    
            if not table:
                print("❌ No table found with any selector")
                return
            
            # Find all data rows (skip header)
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            print(f"Found {len(rows)} result rows")
            
            for i, row in enumerate(rows):
                try:
                    # Extract cells
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    print(f"Row {i+1}: Found {len(cells)} cells")
                    if len(cells) > 0:
                        print(f"  First cell content: '{cells[0].text[:100]}'")
                    
                    if len(cells) >= 6:
                        # Extract member number (first column with link)
                        member_number_cell = cells[0]
                        member_link = member_number_cell.find_element(By.TAG_NAME, "a")
                        member_number = member_link.text.strip()
                        member_url = member_link.get_attribute('href')
                        
                        # Extract other data
                        surname = cells[1].text.strip()
                        firstname = cells[2].text.strip()
                        
                        # Extract address (handle complex structure)
                        address_parts = []
                        address_cell = cells[3]
                        address_items = address_cell.find_elements(By.TAG_NAME, "li")
                        for item in address_items:
                            if item.text.strip():
                                address_parts.append(item.text.strip())
                        address = ", ".join(address_parts)
                        
                        # Svobodny inzenyr
                        svobodny_ing = cells[4].text.strip()
                        
                        # Extract obor (field specializations)
                        obor_parts = []
                        obor_cell = cells[5]
                        obor_spans = obor_cell.find_elements(By.TAG_NAME, "span")
                        for span in obor_spans:
                            title = span.get_attribute('title')
                            if title:
                                obor_parts.append(title)
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
                        print(f"Extracted: {member_number} - {firstname} {surname}")
                        
                except Exception as e:
                    print(f"Error extracting row {i+1}: {e}")
                    # Show row HTML for debugging
                    print(f"  Row HTML: {row.get_attribute('outerHTML')[:200]}...")
                    continue
                    
            print(f"✅ Extracted {len(self.results)} records")
            
        except Exception as e:
            print(f"Table extraction error: {e}")
            
    def save_to_csv(self, filename='ckait_stavbyvedouci.csv'):
        """Save results to CSV file"""
        try:
            print(f"7. Saving {len(self.results)} records to {filename}...")
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if self.results:
                    fieldnames = self.results[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    # Write header
                    writer.writeheader()
                    
                    # Write data
                    for result in self.results:
                        writer.writerow(result)
                        
            print(f"✅ Data saved to {filename}")
            
        except Exception as e:
            print(f"CSV save error: {e}")
            
    def debug_page_structure(self):
        """Debug current page structure"""
        print("\n=== DEBUG INFO ===")
        print(f"Current URL: {self.driver.current_url}")
        print(f"Page title: {self.driver.title}")
        
        # Find all select elements
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        print(f"Found {len(selects)} select elements:")
        for i, select in enumerate(selects):
            print(f"  Select {i}: name='{select.get_attribute('name')}' id='{select.get_attribute('id')}'")
            options = select.find_elements(By.TAG_NAME, "option")
            for option in options[:5]:  # Show first 5 options
                print(f"    Option: value='{option.get_attribute('value')}' text='{option.text}'")
                
        # Find all submit buttons
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
        print(f"Found {len(buttons)} submit buttons:")
        for i, button in enumerate(buttons):
            print(f"  Button {i}: id='{button.get_attribute('id')}' value='{button.get_attribute('value')}' class='{button.get_attribute('class')}'")
            
    def close(self):
        self.driver.quit()

def main():
    print("=== CKAIT PENETRATION TEST ===")
    print("Testing basic filtering functionality")
    
    scraper = CkaitTestScraper(headless=False)
    
    try:
        success = scraper.test_ckait_filtering()
        
        if success:
            print("\n✅ CKAIT SCRAPING TEST PASSED")
            print("Filter, search, and data extraction working")
            scraper.save_to_csv()
            print("Ready for production scraping")
        else:
            print("\n❌ CKAIT TEST FAILED") 
            print("Check debug output above")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        scraper.close()

if __name__ == "__main__":
    main()