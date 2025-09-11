import csv
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def setup_chrome(headless=True):
    """Setup Chrome driver"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_phones(url, driver):
    """Extract both phone numbers from profile page"""
    try:
        driver.get(url)
        time.sleep(random.uniform(1, 3))
        
        # Get contact phone
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
        except:
            pass
            
        # Get company phone
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
        except:
            pass
            
        return contact_phone, company_phone
        
    except Exception as e:
        print(f"Error with URL {url}: {e}")
        return "", ""

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ultra_simple_phone.py <csv_file> [--headless]")
        print("Column G should contain direct URLs like: https://www.ckait.cz/expert/form/0000698")
        return
        
    csv_file = sys.argv[1] 
    headless = "--headless" in sys.argv
    
    print(f"=== ULTRA SIMPLE PHONE EXTRACTOR ===")
    print(f"CSV: {csv_file}")
    print(f"Headless: {headless}")
    print(f"Opening URLs directly from Column G...")
    
    # Setup Chrome
    driver = setup_chrome(headless)
    results = []
    
    try:
        # Read CSV
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            
            print(f"Header: {header}")
            
            # Find column G (index 6)
            if len(header) < 7:
                print("❌ CSV doesn't have column G (index 6)")
                return
                
            for i, row in enumerate(reader, 1):
                if len(row) < 7:
                    continue
                    
                # Get data
                member_id = row[0] if len(row) > 0 else ""
                surname = row[1] if len(row) > 1 else ""  
                firstname = row[2] if len(row) > 2 else ""
                url = row[6].strip()  # Column G
                
                name = f"{firstname} {surname}".strip()
                
                print(f"\n{i}. {member_id} - {name}")
                print(f"URL: {url}")
                
                if not url or not url.startswith('http'):
                    print("❌ Invalid URL")
                    results.append([member_id, name, "", ""])
                    continue
                    
                # Extract phones
                contact, company = extract_phones(url, driver)
                
                if contact or company:
                    print(f"📞 Contact: {contact or 'N/A'}, Company: {company or 'N/A'}")
                else:
                    print("❌ No phones found")
                    
                results.append([member_id, name, contact, company])
                
                # Rate limit
                time.sleep(random.uniform(2, 4))
                
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        driver.quit()
        
    # Save results
    output_file = csv_file.replace('.csv', '_phones.csv')
    print(f"\n💾 Saving to: {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['member_id', 'name', 'contact_phone', 'company_phone'])
        writer.writerows(results)
        
    print(f"✅ Done! {len(results)} records processed")
    
    # Stats
    contact_count = sum(1 for r in results if r[2])
    company_count = sum(1 for r in results if r[3])
    print(f"📞 Found {contact_count} contact phones, {company_count} company phones")

if __name__ == "__main__":
    main()