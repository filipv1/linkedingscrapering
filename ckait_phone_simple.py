import csv
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

class SimplePhoneExtractor:
    def __init__(self, headless=True, max_workers=3):
        self.headless = headless
        self.max_workers = max_workers
        self.results = []
        self.results_lock = threading.Lock()
        self.processed_count = 0
        self.total_count = 0
        
    def setup_driver(self):
        """Setup Chrome driver - same as working test"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
            
        # Anti-detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
        
    def extract_single_phone(self, member_data):
        """Extract phone - exactly like working test"""
        driver = None
        try:
            driver = self.setup_driver()
            
            member_number = member_data['member_number']
            name = f"{member_data.get('firstname', '')} {member_data.get('surname', '')}".strip()
            
            # Use profile_url directly from CSV (clean up any duplicates)
            profile_url = member_data.get('profile_url', '').strip()
            
            # Fix duplicate URL issue: remove duplicate https://www.ckait.cz
            if profile_url.startswith('https://www.ckait.czhttps://www.ckait.cz'):
                profile_url = profile_url.replace('https://www.ckait.czhttps://www.ckait.cz', 'https://www.ckait.cz')
            
            # Fallback: construct URL if profile_url is empty
            if not profile_url:
                formatted_number = member_number.zfill(7) if member_number.isdigit() else member_number
                profile_url = f"https://www.ckait.cz/expert/form/{formatted_number}"
                print(f"Generated URL (fallback): {profile_url}")
            else:
                print(f"Using URL from CSV: {profile_url}")
            
            # Validate URL before using
            if not profile_url or not profile_url.startswith('http'):
                raise Exception(f"Invalid URL: '{profile_url}'")
            
            print(f"Processing: {member_number} - {name}")
            
            # Navigate to profile
            driver.get(profile_url)
            time.sleep(random.uniform(2, 4))
            
            # Extract contact phone - EXACT same logic as test
            contact_phone = ""
            try:
                contact_phone_elem = driver.find_element(By.ID, "edit-contact-phone")
                contact_phone_text = contact_phone_elem.text.strip()
                lines = contact_phone_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and line != "Telefon" and len(line) > 3:
                        clean_line = line.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
                        if clean_line.isdigit() and len(clean_line) >= 9:
                            contact_phone = line
                            break
            except:
                pass
                
            # Extract company phone - EXACT same logic as test  
            company_phone = ""
            try:
                company_phone_elem = driver.find_element(By.ID, "edit-company-phone")
                company_phone_text = company_phone_elem.text.strip()
                lines = company_phone_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and line != "Telefon" and len(line) > 3:
                        clean_line = line.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
                        if clean_line.isdigit() and len(clean_line) >= 9:
                            company_phone = line
                            break
            except:
                pass
            
            result = {
                'name': name,
                'member_id': member_number,
                'contact_phone': contact_phone,
                'company_phone': company_phone
            }
            
            # Thread-safe results
            with self.results_lock:
                self.results.append(result)
                self.processed_count += 1
                
            # Output exactly like test
            if contact_phone or company_phone:
                print(f"📞 {member_number}: Contact={contact_phone or 'N/A'}, Company={company_phone or 'N/A'} ({self.processed_count}/{self.total_count})")
            else:
                print(f"❌ {member_number}: No phones found ({self.processed_count}/{self.total_count})")
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing {member_number}: {e}")
            
            with self.results_lock:
                self.results.append({
                    'name': name if 'name' in locals() else member_data.get('member_number', ''),
                    'member_id': member_data.get('member_number', ''),
                    'contact_phone': '',
                    'company_phone': ''
                })
                self.processed_count += 1
                
            return None
            
        finally:
            if driver:
                driver.quit()
                
    def load_csv_data(self, csv_file_path):
        """Load CSV data"""
        members = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('member_number'):
                        members.append(row)
                        
            print(f"Loaded {len(members)} members from CSV")
            return members
            
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return []
            
    def process_all(self, csv_file_path):
        """Process with parallel workers"""
        print(f"=== SIMPLE CKAIT PHONE EXTRACTOR ===")
        print(f"Headless: {self.headless}, Workers: {self.max_workers}")
        
        members = self.load_csv_data(csv_file_path)
        if not members:
            return False
            
        self.total_count = len(members)
        print(f"Starting extraction for {self.total_count} members...")
        
        # Process with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_member = {
                executor.submit(self.extract_single_phone, member): member 
                for member in members
            }
            
            for future in as_completed(future_to_member):
                member = future_to_member[future]
                try:
                    result = future.result()
                except Exception as e:
                    print(f"❌ Thread error for {member.get('member_number', 'unknown')}: {e}")
                    
        print(f"\n🎉 EXTRACTION COMPLETED!")
        print(f"Processed: {len(self.results)} profiles")
        
        # Count results
        contact_phones = sum(1 for r in self.results if r['contact_phone'])
        company_phones = sum(1 for r in self.results if r['company_phone'])
        
        print(f"Found contact phones: {contact_phones}")
        print(f"Found company phones: {company_phones}")
        
        return True
        
    def save_results(self, output_file='ckait_phones_simple.csv'):
        """Save results to CSV"""
        try:
            print(f"Saving {len(self.results)} results to {output_file}...")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'member_id', 'contact_phone', 'company_phone']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in self.results:
                    writer.writerow(result)
                    
            print(f"✅ Results saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple CKAIT Phone Extractor - Based on Working Test')
    parser.add_argument('csv_file', help='Input CSV file')
    parser.add_argument('--headless', action='store_true', default=True, help='Headless mode (default)')
    parser.add_argument('--gui', action='store_true', help='Show GUI')
    parser.add_argument('--workers', type=int, default=3, help='Workers (default: 3)')
    parser.add_argument('--output', default='ckait_phones_simple.csv', help='Output file')
    
    args = parser.parse_args()
    
    headless_mode = args.headless and not args.gui
    
    extractor = SimplePhoneExtractor(
        headless=headless_mode,
        max_workers=args.workers
    )
    
    try:
        if extractor.process_all(args.csv_file):
            extractor.save_results(args.output)
            print("\n✅ SUCCESS!")
        else:
            print("\n❌ FAILED")
            
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()