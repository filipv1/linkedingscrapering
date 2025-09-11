import csv
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class UltraPhoneExtractorExtended:
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

    def extract_text_by_label(self, driver, label_text):
        """Extract text following a specific label"""
        try:
            # Try multiple strategies to find the text
            selectors = [
                f"//text()[contains(., '{label_text}')]/following-sibling::text()",
                f"//*[contains(text(), '{label_text}')]/following-sibling::*",
                f"//*[contains(text(), '{label_text}')]/parent::*/following-sibling::*"
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        text = elements[0].text.strip()
                        if text and text != label_text:
                            return text
                except:
                    continue
                    
            return ""
        except:
            return ""

    def extract_from_page_content(self, driver, search_text):
        """Extract information by searching page content"""
        try:
            page_text = driver.page_source
            lines = page_text.split('\n')
            
            for i, line in enumerate(lines):
                if search_text in line:
                    # Look in current and next few lines for the value
                    for j in range(i, min(i + 5, len(lines))):
                        candidate = lines[j].strip()
                        # Clean HTML tags
                        import re
                        clean_text = re.sub(r'<[^>]+>', '', candidate).strip()
                        if clean_text and clean_text != search_text and len(clean_text) > 2:
                            return clean_text
            return ""
        except:
            return ""

    def extract_birth_date(self, driver):
        """Extract birth date"""
        try:
            import re
            page_text = driver.page_source
            
            # More specific date patterns
            date_patterns = [
                r'\b\d{1,2}\.\s*\d{1,2}\.\s*\d{4}\b',  # DD. MM. YYYY
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',          # DD/MM/YYYY
                r'\b\d{4}-\d{1,2}-\d{1,2}\b'           # YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    # Filter out unlikely dates (not birth dates)
                    if ('19' in match or '20' in match) and len(match) >= 8:
                        # Additional validation - birth year should be reasonable
                        year_match = re.search(r'(19\d{2}|20\d{2})', match)
                        if year_match:
                            year = int(year_match.group(1))
                            if 1920 <= year <= 2005:  # Reasonable birth year range
                                return match.strip()
                
            return ""
        except:
            return ""

    def extract_emails(self, driver):
        """Extract personal and company emails"""
        try:
            personal_email = ""
            company_email = ""
            
            # Find all email addresses on page
            import re
            page_text = driver.page_source
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_text)
            
            # Usually there's one email that serves both purposes
            if emails:
                personal_email = emails[0]
                company_email = emails[1] if len(emails) > 1 else emails[0]
                
            return personal_email, company_email
        except:
            return "", ""

    def extract_addresses(self, driver):
        """Extract addresses using correct parsing logic"""
        try:
            import re
            page_source = driver.page_source
            
            def find_address_after_heading(heading):
                """Find address components after a specific heading"""
                try:
                    # Find the heading position
                    heading_pos = page_source.find(heading)
                    if heading_pos == -1:
                        return ""
                    
                    # Get text after heading (next 1000 chars)
                    section = page_source[heading_pos:heading_pos + 1000]
                    lines = section.split('\n')
                    
                    # Clean lines and remove HTML
                    clean_lines = []
                    for line in lines:
                        clean_line = re.sub(r'<[^>]+>', '', line).strip()
                        if clean_line and len(clean_line) > 1:
                            clean_lines.append(clean_line)
                    
                    # Parse structure: Heading -> Ulice -> Street -> Obec -> City -> PSC -> PostalCode
                    street = ""
                    city = ""
                    postal = ""
                    
                    i = 0
                    while i < len(clean_lines):
                        line = clean_lines[i]
                        
                        # After "Ulice", next line is street address
                        if line == "Ulice" and i + 1 < len(clean_lines):
                            street = clean_lines[i + 1]
                            i += 2
                            continue
                            
                        # After "Obec", next line is city
                        elif line == "Obec" and i + 1 < len(clean_lines):
                            city = clean_lines[i + 1]
                            i += 2
                            continue
                            
                        # After "PSC" or if line is 5 digits, it's postal code
                        elif (line == "PSC" and i + 1 < len(clean_lines)) or re.match(r'^\d{5}$', line):
                            if line == "PSC" and i + 1 < len(clean_lines):
                                postal = clean_lines[i + 1]
                            else:
                                postal = line
                            i += 1
                            continue
                            
                        else:
                            i += 1
                    
                    # Combine address parts
                    address_parts = [part for part in [street, city, postal] if part]
                    return ', '.join(address_parts) if address_parts else ""
                    
                except:
                    return ""
            
            # Extract both address types
            personal_address = find_address_after_heading("Adresa kontaktní")
            company_address = find_address_after_heading("Adresa pracoviště")
            
            return personal_address, company_address
            
        except Exception as e:
            return "", ""

    def extract_ico(self, driver):
        """Extract company registration number (IČ)"""
        try:
            # Look for IČ
            ico_selectors = [
                "//text()[contains(., 'IČ')]/../following-sibling::*",
                "//td[contains(text(), 'IČ')]/following-sibling::td",
                "//*[contains(text(), 'IČ')]/following-sibling::*"
            ]
            
            for selector in ico_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        # Check if it looks like IČ (8 digits)
                        clean_text = ''.join(c for c in text if c.isdigit())
                        if len(clean_text) == 8:
                            return clean_text
                except:
                    continue
                    
            # Fallback: search for 8-digit number pattern
            import re
            page_text = driver.page_source
            ico_pattern = r'\b\d{8}\b'
            matches = re.findall(ico_pattern, page_text)
            if matches:
                return matches[0]
                
            return ""
        except:
            return ""

    def extract_roles(self, driver):
        """Extract professional roles"""
        try:
            roles = ""
            
            # Look for roles/activities section
            role_keywords = ["Praktická forma", "Projektant", "Stavbyvedoucí", "Technický dozor"]
            
            for keyword in role_keywords:
                role_text = self.extract_from_page_content(driver, keyword)
                if role_text and len(role_text) > len(keyword):
                    roles = role_text
                    break
                    
            # Clean up roles text
            if roles:
                # Remove common prefixes
                roles = roles.replace("Praktická forma výkonu činnosti ve výstavbě", "").strip()
                roles = roles.replace(":", "").strip()
                
            return roles
        except:
            return ""

    def extract_specializations(self, driver):
        """Extract specializations"""
        try:
            specializations = ""
            
            # Look for comment/specialization section
            spec_keywords = ["Komentář", "Ocelové konstrukce", "projekty", "stavby", "technolog"]
            
            for keyword in spec_keywords:
                spec_text = self.extract_from_page_content(driver, keyword)
                if spec_text and len(spec_text) > 20:  # Likely a meaningful specialization
                    specializations = spec_text
                    break
                    
            return specializations
        except:
            return ""

    def extract_languages(self, driver):
        """Extract language skills"""
        try:
            languages = ""
            
            # Look for language section - avoid encoding issues
            page_text = driver.page_source.lower()
            lang_indicators = ['czech', 'english', 'german', 'cestina', 'anglictina', 'nemcina']
            found_langs = []
            
            for indicator in lang_indicators:
                if indicator in page_text:
                    if 'czech' in indicator or 'cestina' in indicator:
                        found_langs.append('Cestina')
                    elif 'english' in indicator or 'anglictina' in indicator:
                        found_langs.append('Anglictina') 
                    elif 'german' in indicator or 'nemcina' in indicator:
                        found_langs.append('Nemcina')
                        
            languages = ', '.join(found_langs)
            return languages
        except:
            return ""

    def extract_single(self, data):
        """Extract all information for single person - EXTENDED VERSION"""
        member_id, name, url, total = data
        driver = None
        
        try:
            driver = self.setup_chrome()
            
            print(f"Processing: {member_id} - {name}")
            print(f"URL: {url}")
            
            if not url or not url.startswith('http'):
                raise Exception("Invalid URL")
                
            driver.get(url)
            time.sleep(random.uniform(2, 4))  # Longer delay for complex extraction
            
            # Extract existing phone fields (UNCHANGED)
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

            # Extract NEW fields
            birth_date = self.extract_birth_date(driver)
            personal_email, company_email = self.extract_emails(driver)
            personal_address, company_address = self.extract_addresses(driver)
            ico = self.extract_ico(driver)
            roles = self.extract_roles(driver)
            specializations = self.extract_specializations(driver)
            languages = self.extract_languages(driver)
            
            result = [
                member_id, 
                name, 
                contact_phone, 
                company_phone,
                # NEW FIELDS:
                birth_date,
                personal_email,
                company_email,
                personal_address,
                company_address,
                ico,
                roles,
                specializations,
                languages
            ]
            
            # Thread-safe results
            with self.results_lock:
                self.results.append(result)
                self.count += 1
                
            if contact_phone or company_phone:
                print(f"PHONE {member_id}: Contact={contact_phone or 'N/A'}, Company={company_phone or 'N/A'} ({self.count}/{total})")
                if birth_date:
                    print(f"    BIRTH: {birth_date}")
                if personal_email:
                    print(f"    EMAIL: {personal_email}")
                if personal_address:
                    print(f"    ADDRESS_PERSONAL: {personal_address}")
                if company_address and company_address != personal_address:
                    print(f"    ADDRESS_COMPANY: {company_address}")
            else:
                print(f"NO_PHONE {member_id}: No phones found ({self.count}/{total})")
                
            return result
            
        except Exception as e:
            print(f"ERROR {member_id}: {e}")
            
            with self.results_lock:
                self.results.append([member_id, name, "", "", "", "", "", "", "", "", "", "", ""])
                self.count += 1
                
            return None
            
        finally:
            if driver:
                driver.quit()

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ultra_phone_parallel_extended.py <csv_file> [--headless] [--workers N]")
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
    
    print(f"=== ULTRA PHONE PARALLEL EXTRACTOR - EXTENDED ===")
    print(f"CSV: {csv_file}")
    print(f"Headless: {headless}")
    print(f"Workers: {workers}")
    print(f"Extracting: phones + birth_date + emails + addresses + ico + roles + specializations + languages")
    
    extractor = UltraPhoneExtractorExtended(headless=headless, workers=workers)
    
    # Load CSV data (UNCHANGED)
    people_data = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            print(f"CSV columns: {header}")
            
            if len(header) < 7:
                print("ERROR CSV needs at least 7 columns (G = index 6)")
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
        
        # Process with ThreadPoolExecutor (UNCHANGED)
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
                    print(f"THREAD_ERROR: {e}")
        
        print(f"\nEXTRACTION COMPLETED!")
        print(f"Processed: {len(extractor.results)} people")
        
        # Save results to CSV and Excel - EXTENDED COLUMNS
        csv_output = csv_file.replace('.csv', '_extended_parallel.csv')
        excel_output = csv_file.replace('.csv', '_extended_parallel.xlsx')
        
        print(f"SAVING CSV: {csv_output}")
        with open(csv_output, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'member_id', 'name', 'contact_phone', 'company_phone',
                'birth_date', 'personal_email', 'company_email', 
                'personal_address', 'company_address', 'ico', 
                'roles', 'specializations', 'languages'
            ])
            writer.writerows(extractor.results)
        
        # Also save to Excel for perfect Czech characters - EXTENDED COLUMNS
        try:
            import pandas as pd
            df = pd.DataFrame(extractor.results, columns=[
                'member_id', 'name', 'contact_phone', 'company_phone',
                'birth_date', 'personal_email', 'company_email', 
                'personal_address', 'company_address', 'ico', 
                'roles', 'specializations', 'languages'
            ])
            
            print(f"SAVING Excel: {excel_output}")
            with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Extended_Data', index=False)
                
                # Format worksheet  
                worksheet = writer.sheets['Extended_Data']
                # Set column widths
                columns_widths = {
                    'A': 15, 'B': 25, 'C': 20, 'D': 20, 'E': 15, 
                    'F': 30, 'G': 30, 'H': 40, 'I': 40, 'J': 15,
                    'K': 40, 'L': 50, 'M': 30
                }
                for col, width in columns_widths.items():
                    worksheet.column_dimensions[col].width = width
                
                # Bold header
                for cell in worksheet[1]:
                    cell.font = cell.font.copy(bold=True)
                    
            print(f"SUCCESS Excel saved with perfect Czech encoding!")
            
        except ImportError:
            print("WARNING pandas not available - install with: pip install pandas openpyxl")
        except Exception as e:
            print(f"WARNING Excel save failed: {e}")
            
        # Stats - EXTENDED
        contact_count = sum(1 for r in extractor.results if r[2])
        company_count = sum(1 for r in extractor.results if r[3])
        birth_count = sum(1 for r in extractor.results if r[4])
        email_count = sum(1 for r in extractor.results if r[5])
        address_count = sum(1 for r in extractor.results if r[7])
        ico_count = sum(1 for r in extractor.results if r[9])
        
        print(f"PHONES Found {contact_count} contact phones, {company_count} company phones")
        print(f"BIRTH Found {birth_count} birth dates")
        print(f"EMAIL Found {email_count} emails")
        print(f"ADDRESS Found {address_count} addresses")  
        print(f"COMPANY Found {ico_count} company IDs")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()