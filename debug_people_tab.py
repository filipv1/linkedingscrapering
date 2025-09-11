from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class PeopleTabDebugger:
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
        
    def debug_company_page(self, company_name="Metrostav a.s."):
        print(f"\n=== DEBUGGING COMPANY PAGE FOR: {company_name} ===")
        
        try:
            # Step 1: Search for company
            print("1. Searching for company...")
            search_input = self.driver.find_element(By.CSS_SELECTOR, "input.search-global-typeahead__input")
            search_input.clear()
            search_input.send_keys(company_name)
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            # Step 2: Click Společnosti filter
            print("2. Clicking 'Společnosti' filter...")
            all_filters = self.driver.find_elements(By.CSS_SELECTOR, ".search-reusables__filter-pill-button")
            for filter_btn in all_filters:
                if "Společnosti" in filter_btn.text or "Companies" in filter_btn.text:
                    filter_btn.click()
                    break
            time.sleep(3)
            
            # Step 3: Find and click company
            print("3. Finding company...")
            company_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/company/']")
            company_link = None
            for link in company_links:
                if company_name.lower().replace(".", "").replace(",", "") in link.text.lower().replace(".", "").replace(",", ""):
                    company_link = link
                    break
                    
            if not company_link and company_links:
                company_link = company_links[0]
                
            if company_link:
                company_url = company_link.get_attribute('href')
                print(f"Found company: {company_link.text} -> {company_url}")
                
                # Navigate to company page
                print("4. Navigating to company page...")
                self.driver.get(company_url)
                time.sleep(5)
                
                # DEBUG: Show all navigation elements
                self.debug_navigation_elements()
                
            else:
                print("ERROR: No company found")
                
        except Exception as e:
            print(f"ERROR: {e}")
            
    def debug_navigation_elements(self):
        print("\n=== DEBUGGING NAVIGATION ELEMENTS ===")
        print(f"Current URL: {self.driver.current_url}")
        
        # Check if page loaded properly
        print(f"Page title: {self.driver.title}")
        
        # Find all navigation-like elements
        nav_selectors = [
            "a.org-page-navigation__item-anchor",
            "a[href*='/people/']", 
            ".org-page-navigation a",
            "nav a",
            ".artdeco-tabs__tab",
            ".org-page-navigation__item"
        ]
        
        print("\n--- Looking for navigation elements ---")
        for selector in nav_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"\nFound {len(elements)} elements with '{selector}':")
                    for i, elem in enumerate(elements[:5]):  # Show first 5
                        text = elem.text.strip()
                        href = elem.get_attribute('href') or 'no-href'
                        classes = elem.get_attribute('class') or 'no-class'
                        print(f"  {i+1}. Text: '{text}' | Href: {href}")
                        print(f"      Classes: {classes}")
            except Exception as e:
                print(f"Error with {selector}: {e}")
                
        # Look for any link containing 'people' or 'Lidé'
        print("\n--- Looking for 'people/Lidé' links ---")
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        people_links = []
        for link in all_links:
            href = link.get_attribute('href') or ''
            text = link.text.strip()
            if '/people/' in href or 'Lidé' in text or 'People' in text:
                people_links.append(link)
                
        if people_links:
            print(f"Found {len(people_links)} potential 'Lidé' links:")
            for i, link in enumerate(people_links[:3]):
                print(f"  {i+1}. Text: '{link.text}' | Href: {link.get_attribute('href')}")
                print(f"      Classes: {link.get_attribute('class')}")
        else:
            print("No 'people/Lidé' links found!")
            
        # Show page source snippet around navigation
        try:
            nav_section = self.driver.find_element(By.CSS_SELECTOR, ".org-page-navigation, nav, [role='navigation']")
            print(f"\nNavigation section HTML (first 500 chars):")
            print(nav_section.get_attribute('innerHTML')[:500])
        except:
            print("Could not find navigation section")
            
    def close(self):
        input("\nPress Enter to close browser...")
        self.driver.quit()

def main():
    debugger = PeopleTabDebugger()
    
    try:
        debugger.debug_company_page("Metrostav a.s.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        debugger.close()

if __name__ == "__main__":
    main()