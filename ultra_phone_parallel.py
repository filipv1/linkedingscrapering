import csv
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class UltraPhoneExtractor:
    def __init__(self, headless=True, workers=3):
        self.headless = headless
        self.workers = workers
        self.results = []
        self.results_lock = threading.Lock()
        self.count = 0
        
    def setup_chrome(self):
        """Setup Chrome driver for each worker"""
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def extract_single(self, data):
        """Extract phones for single person"""
        member_id, name, url, total = data
        driver = None
        
        try:
            driver = self.setup_chrome()
            
            print(f"Processing: {member_id} - {name}")
            print(f"URL: {url}")
            
            if not url or not url.startswith('http'):
                raise Exception("Invalid URL")
                
            driver.get(url)
            time.sleep(random.uniform(1, 3))
            
            # Extract contact phone
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
                
            # Extract company phone
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
                
            result = [member_id, name, contact_phone, company_phone]
            
            # Thread-safe results
            with self.results_lock:
                self.results.append(result)
                self.count += 1
                
            if contact_phone or company_phone:
                print(f"📞 {member_id}: Contact={contact_phone or 'N/A'}, Company={company_phone or 'N/A'} ({self.count}/{total})")
            else:
                print(f"❌ {member_id}: No phones found ({self.count}/{total})")
                
            return result
            
        except Exception as e:
            print(f"❌ Error {member_id}: {e}")
            
            with self.results_lock:
                self.results.append([member_id, name, "", ""])
                self.count += 1
                
            return None
            
        finally:
            if driver:
                driver.quit()

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ultra_phone_parallel.py <csv_file> [--headless] [--workers N]")
        print("Column G should contain URLs: https://www.ckait.cz/expert/form/0000698")
        return
        
    csv_file = sys.argv[1]
    headless = "--headless" in sys.argv
    
    # Get workers count
    workers = 3
    if "--workers" in sys.argv:
        try:
            idx = sys.argv.index("--workers")
            workers = int(sys.argv[idx + 1])
        except:
            workers = 3
    
    print(f"=== ULTRA PHONE PARALLEL EXTRACTOR ===")
    print(f"CSV: {csv_file}")
    print(f"Headless: {headless}")
    print(f"Workers: {workers}")
    
    extractor = UltraPhoneExtractor(headless=headless, workers=workers)
    
    # Load CSV data
    people_data = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            print(f"CSV columns: {header}")
            
            if len(header) < 7:
                print("❌ CSV needs at least 7 columns (G = index 6)")
                return
                
            for row in reader:
                if len(row) < 7:
                    continue
                    
                member_id = row[0] if len(row) > 0 else ""
                surname = row[1] if len(row) > 1 else ""  
                firstname = row[2] if len(row) > 2 else ""
                url = row[6].strip()  # Column G
                
                name = f"{firstname} {surname}".strip()
                people_data.append((member_id, name, url, len(people_data)))
                
        total = len(people_data)
        print(f"Loaded {total} people from CSV")
        
        # Update total count in data
        people_data = [(mid, name, url, total) for mid, name, url, _ in people_data]
        
        # Process with ThreadPoolExecutor
        print(f"\nStarting parallel extraction with {workers} workers...")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_person = {
                executor.submit(extractor.extract_single, person_data): person_data
                for person_data in people_data
            }
            
            for future in as_completed(future_to_person):
                person_data = future_to_person[future]
                try:
                    result = future.result()
                except Exception as e:
                    print(f"❌ Thread error: {e}")
        
        print(f"\n🎉 EXTRACTION COMPLETED!")
        print(f"Processed: {len(extractor.results)} people")
        
        # Save results to CSV and Excel
        csv_output = csv_file.replace('.csv', '_phones_parallel.csv')
        excel_output = csv_file.replace('.csv', '_phones_parallel.xlsx')
        
        print(f"💾 Saving CSV: {csv_output}")
        with open(csv_output, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['member_id', 'name', 'contact_phone', 'company_phone'])
            writer.writerows(extractor.results)
        
        # Also save to Excel for perfect Czech characters
        try:
            import pandas as pd
            df = pd.DataFrame(extractor.results, columns=['member_id', 'name', 'contact_phone', 'company_phone'])
            
            print(f"💾 Saving Excel: {excel_output}")
            with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Telefony', index=False)
                
                # Format worksheet  
                worksheet = writer.sheets['Telefony']
                worksheet.column_dimensions['A'].width = 15
                worksheet.column_dimensions['B'].width = 25
                worksheet.column_dimensions['C'].width = 20
                worksheet.column_dimensions['D'].width = 20
                
                # Bold header
                for cell in worksheet[1]:
                    cell.font = cell.font.copy(bold=True)
                    
            print(f"✅ Excel saved with perfect Czech encoding!")
            
        except ImportError:
            print("⚠️ pandas not available - install with: pip install pandas openpyxl")
        except Exception as e:
            print(f"⚠️ Excel save failed: {e}")
            
        # Stats
        contact_count = sum(1 for r in extractor.results if r[2])
        company_count = sum(1 for r in extractor.results if r[3])
        print(f"📞 Found {contact_count} contact phones, {company_count} company phones")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()