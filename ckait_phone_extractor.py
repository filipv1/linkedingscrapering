import csv
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import queue

class CkaitPhoneExtractor:
    def __init__(self, headless=True, max_workers=3):
        self.headless = headless
        self.max_workers = max_workers
        self.results = []
        self.results_lock = threading.Lock()
        self.processed_count = 0
        self.total_count = 0
        
    def setup_driver(self):
        """Setup Chrome driver for each thread"""
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
        
    def extract_phone_from_profile(self, member_data):
        """Extract phone numbers from individual profile page"""
        driver = None
        try:
            driver = self.setup_driver()
            wait = WebDriverWait(driver, 10)
            
            member_number = member_data['member_number']
            name = f"{member_data.get('firstname', '')} {member_data.get('surname', '')}".strip()
            
            # Build profile URL
            profile_url = f"https://www.ckait.cz/expert/form/{member_number}"
            
            print(f"Processing: {member_number} - {name}")
            
            # Navigate to profile
            driver.get(profile_url)
            time.sleep(random.uniform(2, 4))  # Random delay
            
            # Extract contact phone
            contact_phone = ""
            try:
                contact_phone_elem = driver.find_element(By.ID, "edit-contact-phone")
                contact_phone_text = contact_phone_elem.text.strip()
                print(f"DEBUG {member_number}: Contact element text: '{contact_phone_text}'")
                
                # Remove the label "Telefon" and get just the number
                lines = contact_phone_text.split('\n')
                print(f"DEBUG {member_number}: Contact lines: {lines}")
                
                for line in lines:
                    line = line.strip()
                    # More flexible phone number detection
                    if line and line != "Telefon" and len(line) > 3:
                        # Check if line contains mostly digits (allowing spaces, dashes, +)
                        clean_line = line.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
                        print(f"DEBUG {member_number}: Testing line '{line}' -> clean: '{clean_line}', isdigit: {clean_line.isdigit()}, len: {len(clean_line)}")
                        if clean_line.isdigit() and len(clean_line) >= 9:  # At least 9 digits for phone
                            contact_phone = line
                            print(f"DEBUG {member_number}: ✅ Found contact phone: '{contact_phone}'")
                            break
            except Exception as e:
                print(f"Contact phone extraction error for {member_number}: {e}")
                
            # Extract company phone
            company_phone = ""
            try:
                company_phone_elem = driver.find_element(By.ID, "edit-company-phone")
                company_phone_text = company_phone_elem.text.strip()
                # Remove the label "Telefon" and get just the number
                lines = company_phone_text.split('\n')
                for line in lines:
                    line = line.strip()
                    # More flexible phone number detection
                    if line and line != "Telefon" and len(line) > 3:
                        # Check if line contains mostly digits (allowing spaces, dashes, +)
                        clean_line = line.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
                        if clean_line.isdigit() and len(clean_line) >= 9:  # At least 9 digits for phone
                            company_phone = line
                            break
            except Exception as e:
                print(f"Company phone extraction error for {member_number}: {e}")
            
            result = {
                'name': name,
                'member_id': member_number,
                'contact_phone': contact_phone,
                'company_phone': company_phone
            }
            
            # Thread-safe results append
            with self.results_lock:
                self.results.append(result)
                self.processed_count += 1
                
            # Debug output for phone extraction
            if contact_phone or company_phone:
                print(f"📞 {member_number}: Contact={contact_phone or 'N/A'}, Company={company_phone or 'N/A'} ({self.processed_count}/{self.total_count})")
            else:
                print(f"❌ {member_number}: No phones found ({self.processed_count}/{self.total_count})")
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing {member_number}: {e}")
            
            # Still add empty result to maintain count
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
        """Load member data from CSV file"""
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
            
    def extract_phones_parallel(self, csv_file_path):
        """Extract phone numbers using parallel processing"""
        print(f"=== CKAIT PHONE EXTRACTOR ===")
        print(f"Headless mode: {self.headless}")
        print(f"Max workers: {self.max_workers}")
        
        # Load member data
        members = self.load_csv_data(csv_file_path)
        if not members:
            print("❌ No member data loaded")
            return False
            
        self.total_count = len(members)
        print(f"Starting extraction for {self.total_count} members...")
        
        # Process in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_member = {
                executor.submit(self.extract_phone_from_profile, member): member 
                for member in members
            }
            
            # Process completed tasks
            for future in as_completed(future_to_member):
                member = future_to_member[future]
                try:
                    result = future.result()
                except Exception as e:
                    print(f"❌ Thread error for {member.get('member_number', 'unknown')}: {e}")
                    
        print(f"\n🎉 EXTRACTION COMPLETED!")
        print(f"Processed: {len(self.results)} profiles")
        
        # Count successful extractions
        contact_phones = sum(1 for r in self.results if r['contact_phone'])
        company_phones = sum(1 for r in self.results if r['company_phone'])
        
        print(f"Found contact phones: {contact_phones}")
        print(f"Found company phones: {company_phones}")
        
        return True
        
    def save_results(self, output_file='ckait_phones.csv'):
        """Save phone extraction results to CSV"""
        try:
            print(f"Saving {len(self.results)} results to {output_file}...")
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'member_id', 'contact_phone', 'company_phone']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write data
                for result in self.results:
                    writer.writerow(result)
                    
            print(f"✅ Results saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract phone numbers from CKAIT member profiles')
    parser.add_argument('csv_file', help='Input CSV file with member data')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode (default: True)')
    parser.add_argument('--gui', action='store_true', help='Run with GUI (overrides headless)')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers (default: 3)')
    parser.add_argument('--output', default='ckait_phones.csv', help='Output CSV file (default: ckait_phones.csv)')
    
    args = parser.parse_args()
    
    # Handle GUI override
    headless_mode = args.headless and not args.gui
    
    print(f"=== CKAIT PHONE EXTRACTOR ===")
    print(f"Input file: {args.csv_file}")
    print(f"Output file: {args.output}")
    print(f"Headless mode: {headless_mode}")
    print(f"Workers: {args.workers}")
    
    extractor = CkaitPhoneExtractor(
        headless=headless_mode,
        max_workers=args.workers
    )
    
    try:
        if extractor.extract_phones_parallel(args.csv_file):
            extractor.save_results(args.output)
            print("\n✅ PHONE EXTRACTION COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ PHONE EXTRACTION FAILED")
            
    except KeyboardInterrupt:
        print("\n⚠️  Extraction interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    # For direct execution without arguments (development)
    import sys
    if len(sys.argv) == 1:
        print("Development mode - using default parameters")
        print("Usage: python ckait_phone_extractor.py <csv_file> [options]")
        print("Example: python ckait_phone_extractor.py ckait_stavbyvedouci_manual.csv --workers 5 --gui")
    else:
        main()