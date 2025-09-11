from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

def debug_phone_page():
    """Debug single profile page to see actual HTML structure"""
    
    chrome_options = Options()
    # Run with GUI to see what's happening
    chrome_options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Test URL from user example
        test_url = "https://www.ckait.cz/expert/form/0601040"
        print(f"Opening: {test_url}")
        
        driver.get(test_url)
        time.sleep(5)
        
        print("\n=== PAGE TITLE ===")
        print(driver.title)
        
        print("\n=== LOOKING FOR PHONE ELEMENTS ===")
        
        # Try to find contact phone element
        try:
            contact_phone_elem = driver.find_element(By.ID, "edit-contact-phone")
            print("✅ Found contact phone element:")
            print(f"  Full HTML: {contact_phone_elem.get_attribute('outerHTML')}")
            print(f"  Text content: '{contact_phone_elem.text}'")
        except Exception as e:
            print(f"❌ Contact phone element not found: {e}")
            
        # Try to find company phone element  
        try:
            company_phone_elem = driver.find_element(By.ID, "edit-company-phone")
            print("✅ Found company phone element:")
            print(f"  Full HTML: {company_phone_elem.get_attribute('outerHTML')}")
            print(f"  Text content: '{company_phone_elem.text}'")
        except Exception as e:
            print(f"❌ Company phone element not found: {e}")
            
        print("\n=== LOOKING FOR ALL PHONE-RELATED ELEMENTS ===")
        
        # Search for any element containing "telefon" or "phone"
        phone_elements = driver.find_elements(By.XPATH, "//*[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'phone') or contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'phone') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'telefon')]")
        
        print(f"Found {len(phone_elements)} phone-related elements:")
        for i, elem in enumerate(phone_elements[:10]):  # Show first 10
            print(f"  Element {i+1}:")
            print(f"    Tag: {elem.tag_name}")
            print(f"    ID: {elem.get_attribute('id')}")
            print(f"    Class: {elem.get_attribute('class')}")
            print(f"    Text: '{elem.text[:100]}'")
            print(f"    HTML: {elem.get_attribute('outerHTML')[:200]}...")
            print()
            
        print("\n=== LOOKING FOR FORMS AND INPUTS ===")
        
        # Look for form elements that might contain phone data
        form_elements = driver.find_elements(By.CSS_SELECTOR, "div.form-item, .js-form-item, input, div[id*='edit']")
        
        phone_like_elements = []
        for elem in form_elements:
            elem_id = elem.get_attribute('id') or ''
            elem_class = elem.get_attribute('class') or ''
            elem_text = elem.text or ''
            
            if any(keyword in (elem_id + elem_class + elem_text).lower() 
                   for keyword in ['phone', 'telefon', 'contact', 'company']):
                phone_like_elements.append(elem)
                
        print(f"Found {len(phone_like_elements)} potentially relevant elements:")
        for i, elem in enumerate(phone_like_elements[:15]):  # Show first 15
            print(f"  Element {i+1}:")
            print(f"    Tag: {elem.tag_name}")
            print(f"    ID: '{elem.get_attribute('id')}'")
            print(f"    Class: '{elem.get_attribute('class')}'")
            print(f"    Text: '{elem.text}'")
            print()
            
        print("\n=== RAW PAGE SOURCE SEARCH ===")
        page_source = driver.page_source
        
        # Look for phone patterns in source
        phone_patterns = ['493524195', 'edit-contact-phone', 'edit-company-phone', 'telefon']
        for pattern in phone_patterns:
            if pattern in page_source.lower():
                print(f"✅ Found '{pattern}' in page source")
                # Show context around the pattern
                index = page_source.lower().find(pattern.lower())
                start = max(0, index - 100)
                end = min(len(page_source), index + 200)
                context = page_source[start:end]
                print(f"  Context: ...{context}...")
                print()
            else:
                print(f"❌ Pattern '{pattern}' NOT found in page source")
        
        print("\n=== WAITING FOR MANUAL INSPECTION ===")
        print("Browser will stay open for 30 seconds for manual inspection...")
        time.sleep(30)
        
    except Exception as e:
        print(f"Debug error: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_phone_page()