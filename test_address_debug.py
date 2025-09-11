from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re

def setup_chrome():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    return driver

def debug_address_extraction(url):
    driver = setup_chrome()
    
    try:
        print(f"Debugging address extraction for: {url}")
        driver.get(url)
        time.sleep(3)
        
        page_source = driver.page_source
        print(f"\nPage source length: {len(page_source)}")
        
        # Test 1: Look for address keywords
        keywords = ["Adresa kontaktni", "Adresa pracoviste", "Ulice", "Obec", "PSC", "Liskova", "Caslav"]
        for keyword in keywords:
            if keyword in page_source.lower():
                print(f"FOUND keyword: {keyword}")
            else:
                print(f"MISSING keyword: {keyword}")
        
        # Test 2: Extract sections around address keywords
        print("\n=== SEARCHING FOR ADDRESS SECTIONS ===")
        
        for heading in ["Adresa kontaktní", "Adresa pracoviště"]:
            print(f"\nLooking for: {heading}")
            
            # Find text around the heading
            heading_pos = page_source.find(heading)
            if heading_pos != -1:
                print(f"Found {heading} at position {heading_pos}")
                
                # Get 500 characters after the heading
                section = page_source[heading_pos:heading_pos + 500]
                lines = section.split('\n')
                
                print(f"Section content (first 10 lines):")
                for i, line in enumerate(lines[:10]):
                    clean_line = re.sub(r'<[^>]+>', '', line).strip()
                    if clean_line:
                        print(f"  Line {i}: '{clean_line}'")
            else:
                print(f"❌ {heading} not found")
        
        # Test 3: Look for postal codes (5 digits)
        print(f"\n=== LOOKING FOR POSTAL CODES ===")
        postal_pattern = r'\b\d{5}\b'
        postal_codes = re.findall(postal_pattern, page_source)
        print(f"Found postal codes: {postal_codes}")
        
        # Test 4: Look for street-like patterns
        print(f"\n=== LOOKING FOR STREET PATTERNS ===")
        street_patterns = [
            r'[A-Za-zÀ-žŽ\s]+\s+\d+',  # Street name + number
            r'Lísková\s*\d+',          # Specific for this profile
        ]
        
        for pattern in street_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            print(f"Pattern '{pattern}': {matches}")
        
        # Test 5: Look for city names
        print(f"\n=== LOOKING FOR CITIES ===")
        czech_cities = ['Praha', 'Brno', 'Ostrava', 'Caslav', 'Plzen']
        for city in czech_cities:
            if city.lower() in page_source.lower():
                print(f"FOUND city: {city}")
                # Find context around city
                city_pos = page_source.lower().find(city.lower())
                context = page_source[max(0, city_pos-50):city_pos+50]
                clean_context = re.sub(r'<[^>]+>', '', context).replace('\n', ' ').strip()
                print(f"   Context: {clean_context}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    # Test the specific profile that should have addresses
    test_url = "https://www.ckait.cz/expert/form/0003569"
    debug_address_extraction(test_url)