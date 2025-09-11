from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_linkedin():
    """Simple test to open LinkedIn with minimal setup"""
    chrome_options = Options()
    
    # Minimal options to avoid conflicts
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Opening LinkedIn...")
        driver.get("https://www.linkedin.com/feed/")
        
        print("Please log in manually to LinkedIn in the opened browser window.")
        print("After login, press Enter here to continue...")
        input()
        
        # Test search
        print("Testing search functionality...")
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-global-typeahead__input"))
        )
        
        search_input.clear()
        search_input.send_keys("Chládek a Tintěra a.s.")
        search_input.submit()
        
        time.sleep(3)
        
        print("Search completed! Check if results are visible.")
        print("Press Enter to close...")
        input()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_linkedin()