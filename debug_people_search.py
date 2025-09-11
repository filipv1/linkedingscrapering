from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class PeopleSearchDebugger:
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
        
    def debug_people_page(self):
        # Navigate directly to Metrostav people page
        people_url = "https://www.linkedin.com/company/metrostav-a-s-/people/"
        print(f"Navigating to people page: {people_url}")
        self.driver.get(people_url)
        time.sleep(5)
        
        print(f"\n=== DEBUGGING PEOPLE PAGE ===")
        print(f"Current URL: {self.driver.current_url}")
        print(f"Page title: {self.driver.title}")
        
        # 1. Look for search textarea
        print("\n--- Looking for search textarea ---")
        search_selectors = [
            "textarea#people-search-keywords",
            "textarea.org-people__search-input", 
            "input[placeholder*='Vyhledávejte zaměstnance']",
            "input[placeholder*='Search employees']",
            "textarea[placeholder*='zaměstnance']",
            "input[type='text']",
            "textarea"
        ]
        
        search_found = False
        for selector in search_selectors:
            try:
                search_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if search_elements:
                    print(f"Found {len(search_elements)} elements with '{selector}':")
                    for elem in search_elements:
                        placeholder = elem.get_attribute('placeholder') or 'no-placeholder'
                        print(f"  - Placeholder: '{placeholder}' | ID: {elem.get_attribute('id')}")
                    search_found = True
            except Exception as e:
                print(f"Error with {selector}: {e}")
                
        if not search_found:
            print("No search textarea found!")
            
        # 2. Test search functionality
        print("\n--- Testing search functionality ---")
        try:
            search_input = self.driver.find_element(By.CSS_SELECTOR, "textarea#people-search-keywords")
            print("Found search textarea, testing search...")
            search_input.clear()
            search_input.send_keys("stavbyvedoucí")
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            print("Search completed")
        except Exception as e:
            print(f"Could not test search: {e}")
            
        # 3. Look for people cards
        print("\n--- Looking for people cards ---")
        people_selectors = [
            ".org-people-profile-card",
            ".lt-line-clamp",
            "[data-test-app-aware-link*='/in/']",
            ".org-people__profile-card-spacing",
            ".entity-result",
            ".people-result"
        ]
        
        all_people = []
        for selector in people_selectors:
            try:
                people_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if people_cards:
                    print(f"Found {len(people_cards)} people cards with '{selector}':")
                    for i, card in enumerate(people_cards[:3]):  # Show first 3
                        text = card.text.strip()[:100]  # First 100 chars
                        href = card.get_attribute('href') or 'no-href'
                        print(f"  {i+1}. Text: '{text}' | Href: {href}")
                        if 'stavby' in text.lower():
                            all_people.append(card)
                            print(f"     *** Contains 'stavby'! ***")
            except Exception as e:
                print(f"Error with {selector}: {e}")
                
        # 4. Look for pagination/show more button
        print("\n--- Looking for 'Show more' button ---")
        show_more_selectors = [
            "//span[contains(text(), 'Zobrazit více výsledků')]/parent::button",
            "//button[contains(text(), 'Zobrazit více')]",
            "//button[contains(text(), 'Show more')]",
            ".artdeco-button[aria-label*='Show more']",
            "button[data-test*='show-more']"
        ]
        
        for selector in show_more_selectors:
            try:
                if selector.startswith("//"):
                    buttons = self.driver.find_elements(By.XPATH, selector)
                else:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                if buttons:
                    print(f"Found {len(buttons)} 'show more' buttons with '{selector}':")
                    for btn in buttons:
                        print(f"  - Text: '{btn.text}' | Enabled: {btn.is_enabled()}")
            except Exception as e:
                print(f"Error with {selector}: {e}")
                
        # 5. Show page source snippet
        print("\n--- Page source analysis ---")
        page_source = self.driver.page_source
        if 'stavbyvedoucí' in page_source:
            print("✓ 'stavbyvedoucí' found in page source!")
        else:
            print("✗ 'stavbyvedoucí' NOT found in page source")
            
        # Count occurrences of common terms
        terms = ['stavby', 'vedoucí', 'manager', 'lead']
        for term in terms:
            count = page_source.lower().count(term)
            print(f"  '{term}' appears {count} times")
        
    def close(self):
        input("\nPress Enter to close browser...")
        self.driver.quit()

def main():
    debugger = PeopleSearchDebugger()
    
    try:
        debugger.debug_people_page()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        debugger.close()

if __name__ == "__main__":
    main()