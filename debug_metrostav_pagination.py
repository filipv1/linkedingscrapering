from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class MetrostavPaginationDebugger:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
        print("Opening LinkedIn...")
        self.driver.get("https://www.linkedin.com/feed/")
        
        print("Please log in and press Enter to continue...")
        input("Press Enter after login: ")
        
    def debug_metrostav_search(self):
        # Navigate directly to Metrostav people page with search
        people_url = "https://www.linkedin.com/company/metrostav-a-s-/people/"
        print(f"Navigating to Metrostav people page: {people_url}")
        self.driver.get(people_url)
        time.sleep(5)
        
        print(f"\n=== DEBUGGING METROSTAV SEARCH & PAGINATION ===")
        print(f"Current URL: {self.driver.current_url}")
        
        # 1. Search for stavbyvedoucí
        print("\n--- Step 1: Searching for stavbyvedoucí ---")
        try:
            search_textarea = self.wait.until(EC.presence_of_element_located(
                (By.ID, "people-search-keywords")
            ))
            search_textarea.clear()
            search_textarea.send_keys("stavbyvedoucí")
            search_textarea.send_keys(Keys.RETURN)
            time.sleep(5)
            print("Search completed")
        except Exception as e:
            print(f"Search failed: {e}")
            return
            
        # 2. Check for any people results
        print("\n--- Step 2: Looking for people results ---")
        people_selectors = [
            "a[href*='/in/']",
            ".org-people-profile-card",
            "[data-test-app-aware-link*='/in/']",
            ".lt-line-clamp",
            ".entity-result"
        ]
        
        total_people = 0
        for selector in people_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with '{selector}':")
                    for i, elem in enumerate(elements[:3]):
                        text = elem.text.strip()[:50]
                        href = elem.get_attribute('href') or 'no-href'
                        print(f"  {i+1}. Text: '{text}' | Href: {href}")
                        if '/in/' in href:
                            total_people += 1
            except Exception as e:
                print(f"Error with {selector}: {e}")
                
        print(f"Total people profiles found: {total_people}")
        
        if total_people == 0:
            print("❌ NO PEOPLE FOUND - This indicates LinkedIn blocking or search issue")
            self.debug_page_content()
            return
        
        # 3. Look for pagination buttons
        print("\n--- Step 3: Looking for pagination buttons ---")
        pagination_selectors = [
            "//span[contains(text(), 'Zobrazit více výsledků')]/parent::button",
            "//button[contains(text(), 'Zobrazit více')]",
            "//button[contains(text(), 'Show more')]",
            "//button[contains(text(), 'Další')]",
            ".artdeco-button--secondary",
            "button[aria-label*='Show more']",
            "button[aria-label*='Load more']",
            ".scaffold-finite-scroll__load-button",
            ".pv5 button"
        ]
        
        pagination_found = False
        for selector in pagination_selectors:
            try:
                if selector.startswith("//"):
                    buttons = self.driver.find_elements(By.XPATH, selector)
                else:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                if buttons:
                    print(f"Found {len(buttons)} buttons with '{selector}':")
                    for i, btn in enumerate(buttons):
                        text = btn.text.strip()
                        enabled = btn.is_enabled()
                        displayed = btn.is_displayed()
                        classes = btn.get_attribute('class')
                        print(f"  {i+1}. Text: '{text}' | Enabled: {enabled} | Visible: {displayed}")
                        print(f"      Classes: {classes}")
                        if enabled and displayed:
                            pagination_found = True
            except Exception as e:
                print(f"Error with {selector}: {e}")
                
        if not pagination_found:
            print("❌ NO PAGINATION BUTTONS FOUND")
            
        # 4. Try scrolling to load more
        print("\n--- Step 4: Testing infinite scroll ---")
        initial_people = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']"))
        print(f"Initial people count: {initial_people}")
        
        # Scroll to bottom
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        after_scroll_people = len(self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']"))
        print(f"People count after scroll: {after_scroll_people}")
        
        if after_scroll_people > initial_people:
            print("✅ INFINITE SCROLL WORKS - More people loaded")
        else:
            print("❌ INFINITE SCROLL DIDN'T WORK")
            
    def debug_page_content(self):
        """Debug page content when no people are found"""
        print("\n--- PAGE CONTENT DEBUG ---")
        
        # Check for blocking messages
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        blocking_keywords = [
            "can't show you these results",
            "nenalezeny žádné výsledky",
            "no results found",
            "blocked",
            "restricted"
        ]
        
        for keyword in blocking_keywords:
            if keyword.lower() in page_text.lower():
                print(f"🚫 BLOCKING DETECTED: Found '{keyword}' in page content")
        
        # Show page title and first 500 chars of content
        print(f"Page title: {self.driver.title}")
        print(f"First 500 chars of page content:")
        print(page_text[:500])
        
    def close(self):
        input("\nPress Enter to close browser...")
        self.driver.quit()

def main():
    debugger = MetrostavPaginationDebugger()
    
    try:
        debugger.debug_metrostav_search()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        debugger.close()

if __name__ == "__main__":
    main()