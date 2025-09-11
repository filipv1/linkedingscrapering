import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def setup_chrome(headless=False):
    """Setup Chrome driver for testing"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_all_fields(driver, url):
    """Test extraction of all fields"""
    print(f"Testing URL: {url}")
    driver.get(url)
    time.sleep(3)
    
    results = {}
    
    # Extract phones (existing working logic)
    print("\n=== EXTRACTING PHONES ===")
    contact_phone = ""
    try:
        elem = driver.find_element(By.ID, "edit-contact-phone")
        text = elem.text.strip()
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and line != "Telefon" and len(line) > 3:
                clean = line.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
                if clean.isdigit() and len(clean) >= 9:
                    contact_phone = line
                    break
        results['contact_phone'] = contact_phone
        print(f"Contact phone: {contact_phone}")
    except Exception as e:
        print(f"Contact phone error: {e}")
        results['contact_phone'] = ""
        
    company_phone = ""
    try:
        elem = driver.find_element(By.ID, "edit-company-phone")
        text = elem.text.strip()
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and line != "Telefon" and len(line) > 3:
                clean = line.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
                if clean.isdigit() and len(clean) >= 9:
                    company_phone = line
                    break
        results['company_phone'] = company_phone
        print(f"Company phone: {company_phone}")
    except Exception as e:
        print(f"Company phone error: {e}")
        results['company_phone'] = ""
    
    # Extract new fields
    print("\n=== EXTRACTING NEW FIELDS ===")
    
    # Birth date
    print("Looking for birth date...")
    birth_date = ""
    try:
        import re
        page_text = driver.page_source
        # Look for date pattern
        date_patterns = [
            r'\d{1,2}\.\s*\d{1,2}\.\s*\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                birth_date = matches[0]
                break
        results['birth_date'] = birth_date
        print(f"Birth date: {birth_date}")
    except Exception as e:
        print(f"Birth date error: {e}")
        results['birth_date'] = ""
    
    # Emails
    print("Looking for emails...")
    emails = []
    try:
        import re
        page_text = driver.page_source
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)
        results['personal_email'] = emails[0] if emails else ""
        results['company_email'] = emails[1] if len(emails) > 1 else emails[0] if emails else ""
        print(f"Emails found: {emails}")
    except Exception as e:
        print(f"Email error: {e}")
        results['personal_email'] = ""
        results['company_email'] = ""
    
    # Addresses
    print("Looking for addresses...")
    try:
        import re
        page_text = driver.page_source
        
        # Look for Czech postal code pattern (5 digits)
        postal_pattern = r'[^\d]\d{5}[^\d]'
        postal_matches = re.findall(r'\d{5}', page_text)
        
        # Look for common Czech address patterns
        address_patterns = [
            r'[A-Za-z\s]+\s+\d+[a-z]?,\s*[A-Za-z\s]+,?\s*\d{5}',  # Street N, City, Postal
            r'[A-Za-z\s]+\s+\d+[a-z]?,\s*\d{5}\s*[A-Za-z\s]+',    # Street N, Postal City
        ]
        
        address_lines = []
        for pattern in address_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.UNICODE)
            address_lines.extend(matches)
        
        # Also look for lines containing Czech city names
        czech_cities = ['Praha', 'Brno', 'Ostrava', 'Plzeň', 'Liberec', 'Olomouc', 'Ústí', 'Hradec', 'Pardubice', 'Zlín', 'Rokycany']
        for line in page_text.split('\n'):
            clean_line = line.strip()
            if (len(clean_line) > 10 and len(clean_line) < 100 and
                any(city in clean_line for city in czech_cities) and
                any(c.isdigit() for c in clean_line)):
                if clean_line not in address_lines:
                    address_lines.append(clean_line)
        
        # Remove duplicates and HTML artifacts
        cleaned_addresses = []
        for addr in address_lines:
            clean_addr = re.sub(r'<[^>]+>', '', addr).strip()
            if len(clean_addr) > 15 and clean_addr not in cleaned_addresses:
                cleaned_addresses.append(clean_addr)
        
        results['personal_address'] = cleaned_addresses[0] if cleaned_addresses else ""
        results['company_address'] = cleaned_addresses[1] if len(cleaned_addresses) > 1 else cleaned_addresses[0] if cleaned_addresses else ""
        print(f"Addresses found: {len(cleaned_addresses)}")
        for i, addr in enumerate(cleaned_addresses[:3]):  # Show first 3
            print(f"  Address {i+1}: {addr}")
    except Exception as e:
        print(f"Address error: {e}")
        results['personal_address'] = ""
        results['company_address'] = ""
    
    # ICO (company registration)
    print("Looking for ICO...")
    try:
        import re
        page_text = driver.page_source
        # Look for 8-digit numbers (typical for Czech ICO)
        ico_pattern = r'\b\d{8}\b'
        matches = re.findall(ico_pattern, page_text)
        results['ico'] = matches[0] if matches else ""
        print(f"ICO: {results['ico']}")
    except Exception as e:
        print(f"ICO error: {e}")
        results['ico'] = ""
    
    # Roles
    print("Looking for roles...")
    try:
        page_text = driver.page_source.lower()
        roles = []
        role_keywords = ['projektant', 'stavbyvedoucí', 'technický dozor', 'designer']
        for keyword in role_keywords:
            if keyword in page_text:
                roles.append(keyword.title())
        results['roles'] = ', '.join(roles)
        print(f"Roles: {results['roles']}")
    except Exception as e:
        print(f"Roles error: {e}")
        results['roles'] = ""
    
    # Specializations
    print("Looking for specializations...")
    try:
        page_text = driver.page_source.lower()
        specializations = []
        spec_keywords = ['ocelové konstrukce', 'průmyslové areály', 'technologické stavby', 'steel', 'industrial']
        for keyword in spec_keywords:
            if keyword in page_text:
                specializations.append(keyword)
        results['specializations'] = ', '.join(specializations)
        print(f"Specializations: {results['specializations']}")
    except Exception as e:
        print(f"Specializations error: {e}")
        results['specializations'] = ""
    
    # Languages
    print("Looking for languages...")
    try:
        page_text = driver.page_source.lower()
        languages = []
        lang_keywords = ['čeština', 'angličtina', 'němčina', 'english', 'german', 'czech']
        for keyword in lang_keywords:
            if keyword in page_text:
                languages.append(keyword)
        results['languages'] = ', '.join(languages)
        print(f"Languages: {results['languages']}")
    except Exception as e:
        print(f"Languages error: {e}")
        results['languages'] = ""
    
    return results

def main():
    print("=== EXTENDED EXTRACTION TEST ===")
    
    # Test URL
    test_url = "https://www.ckait.cz/expert/form/0202268"
    
    driver = setup_chrome(headless=False)  # Use GUI for testing
    
    try:
        results = extract_all_fields(driver, test_url)
        
        print("\n=== EXTRACTION RESULTS ===")
        for field, value in results.items():
            print(f"{field}: {value}")
            
        print("\n=== CSV FORMAT ===")
        csv_row = [
            "0202268", "Václav Hatlman",
            results['contact_phone'], results['company_phone'],
            results['birth_date'], results['personal_email'], results['company_email'],
            results['personal_address'], results['company_address'], results['ico'],
            results['roles'], results['specializations'], results['languages']
        ]
        
        import csv
        print("CSV row format:")
        print(csv_row)
        
        # Test CSV writing
        with open('test_extraction_result.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'member_id', 'name', 'contact_phone', 'company_phone',
                'birth_date', 'personal_email', 'company_email', 
                'personal_address', 'company_address', 'ico', 
                'roles', 'specializations', 'languages'
            ])
            writer.writerow(csv_row)
        
        print("SUCCESS Test extraction saved to test_extraction_result.csv")
        
    except Exception as e:
        print(f"ERROR Test failed: {e}")
        
    finally:
        print("\nPress Enter to close browser...")
        try:
            input()
        except:
            pass
        driver.quit()

if __name__ == "__main__":
    main()