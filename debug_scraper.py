from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class DebugLinkedInScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content") 
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        print("Opening LinkedIn...")
        self.driver.get("https://www.linkedin.com/feed/")
        
        print("Please log in and press Enter to continue...")
        input("Press Enter after login: ")
        
    def debug_search(self, company_name):
        print(f"\n=== DEBUGGING SEARCH FOR: {company_name} ===")
        
        try:
            # Step 1: Find search input
            print("1. Looking for search input...")
            search_selectors = [
                "input.search-global-typeahead__input",
                "input[placeholder*='Vyhledat']",
                "input[placeholder*='Search']",
                ".search-global-typeahead__input"
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"   ✓ Found search input with: {selector}")
                    break
                except:
                    print(f"   ✗ Not found: {selector}")
                    
            if not search_input:
                print("   ERROR: No search input found!")
                return
                
            # Step 2: Enter search term
            print("2. Entering search term...")
            search_input.clear()
            search_input.send_keys(company_name)
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            # Step 3: Look for "Společnosti" filter
            print("3. Looking for 'Společnosti' filter...")
            filter_selectors = [
                "//button[contains(text(), 'Společnosti')]",
                "//button[contains(text(), 'Companies')]",
                ".search-reusables__filter-pill-button",
                "button[aria-label*='Companies']"
            ]
            
            companies_filter = None
            for selector in filter_selectors:
                try:
                    if selector.startswith("//"):
                        companies_filter = self.driver.find_element(By.XPATH, selector)
                    else:
                        companies_filter = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"   ✓ Found filter with: {selector}")
                    break
                except:
                    print(f"   ✗ Not found: {selector}")
                    
            if not companies_filter:
                print("   ERROR: No 'Společnosti' filter found!")
                self.print_page_info()
                return
                
            # Step 4: Click filter
            print("4. Clicking 'Společnosti' filter...")
            companies_filter.click()
            time.sleep(3)
            
            # Step 5: Look for company results
            print("5. Looking for company results...")
            company_selectors = [
                "a[href*='/company/']",
                "a.YTEbxfHDGCFyuvPAyVvzNRyzZYcheiwKQ",
                "a[data-test-app-aware-link][href*='/company/']",
                ".entity-result__title-text a",
                ".search-result__title a"
            ]
            
            for selector in company_selectors:
                try:
                    companies = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"   Found {len(companies)} companies with: {selector}")
                    if companies:
                        for i, company in enumerate(companies[:3]):
                            print(f"     Company {i+1}: {company.text} -> {company.get_attribute('href')}")
                        return companies[0]  # Return first company
                except Exception as e:
                    print(f"   ✗ Error with {selector}: {e}")
                    
            print("   ERROR: No companies found!")
            self.print_page_info()
            
        except Exception as e:
            print(f"ERROR in debug_search: {e}")
            self.print_page_info()
            
    def print_page_info(self):
        print("\n=== PAGE DEBUG INFO ===")
        print(f"Current URL: {self.driver.current_url}")
        print(f"Page title: {self.driver.title}")
        
        # Get all buttons on page
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        print(f"Found {len(buttons)} buttons on page:")
        for i, btn in enumerate(buttons[:10]):  # Show first 10
            text = btn.text.strip()
            if text:
                print(f"  Button {i+1}: '{text}'")
                
        # Get all links
        links = self.driver.find_elements(By.TAG_NAME, "a") 
        company_links = [link for link in links if '/company/' in link.get_attribute('href') or '']
        print(f"Found {len(company_links)} company links")
        
    def close(self):
        input("\nPress Enter to close browser...")
        self.driver.quit()

def main():
    scraper = DebugLinkedInScraper()
    
    try:
        # Test with one company
        result = scraper.debug_search("Metrostav")
        
        if result:
            print(f"\n✓ SUCCESS: Found company {result.text} at {result.get_attribute('href')}")
        else:
            print(f"\n✗ FAILED: Could not find company")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()