import csv
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import os
from datetime import datetime
import logging

class ProductionLinkedInScraper:
    def __init__(self, headless=True, conservative_mode=True):
        self.headless = headless
        self.conservative_mode = conservative_mode
        self.setup_logging()
        self.setup_driver()
        self.results = []
        self.companies_processed = 0
        self.start_time = datetime.now()
        
        if not headless:
            self.manual_login()
            
    def setup_logging(self):
        """Setup logging for production monitoring"""
        logging.basicConfig(
            filename='scraper_production.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        chrome_options = Options()
        
        # Production headless setup
        if self.headless:
            chrome_options.add_argument("--headless=new")  # New headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
        # Enhanced anti-detection for production
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_argument("--disable-javascript")  # Even more stealth
        
        # Realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 15)  # Longer timeout for production
        
    def manual_login(self):
        """Manual login only for non-headless mode"""
        print("Opening LinkedIn for manual login...")
        self.driver.get("https://www.linkedin.com/feed/")
        
        print("\n" + "="*60)
        print("PRODUCTION MANUAL LOGIN")
        print("1. Log in to LinkedIn in the opened browser")
        print("2. Navigate to the feed page")
        print("3. Press Enter here when ready...")
        print("="*60)
        
        input("Press Enter after login: ")
        print("Login completed. Starting production scraping...")
        
    def production_rate_limit(self, min_delay=15, max_delay=25):
        """Conservative rate limiting for production"""
        if self.conservative_mode:
            min_delay = max(min_delay, 20)  # At least 20s in conservative mode
            max_delay = max(max_delay, 35)  # Up to 35s
            
        delay = random.uniform(min_delay, max_delay)
        self.logger.info(f"Rate limiting: {delay:.1f}s")
        print(f"Waiting {delay:.1f}s...")
        time.sleep(delay)
        
    def human_like_behavior(self):
        """Enhanced human-like behavior for production"""
        # Random scroll
        scroll_amount = random.randint(200, 600)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(2, 4))
        
        # Random mouse movement
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        self.driver.execute_script(f"""
            var event = new MouseEvent('mouseover', {{
                'view': window,
                'bubbles': true,
                'cancelable': true,
                'clientX': {x},
                'clientY': {y}
            }});
            document.elementFromPoint({x}, {y})?.dispatchEvent(event);
        """)
        time.sleep(random.uniform(1, 3))
        
    def search_company(self, company_name):
        """Search for company with production safety"""
        try:
            self.logger.info(f"Searching for company: {company_name}")
            print(f"Searching for company: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            
            # Navigate or refresh to LinkedIn feed
            current_url = self.driver.current_url
            if "linkedin.com" not in current_url:
                self.driver.get("https://www.linkedin.com/feed/")
                self.production_rate_limit(10, 15)
            
            # Find search input with retries
            search_input = None
            for attempt in range(3):
                try:
                    search_input = self.wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input.search-global-typeahead__input")
                    ))
                    break
                except:
                    self.logger.warning(f"Search input not found, attempt {attempt + 1}")
                    time.sleep(5)
                    
            if not search_input:
                raise TimeoutException("Cannot find search input")
            
            # Clear and enter company name
            search_input.clear()
            time.sleep(random.uniform(1, 2))
            search_input.send_keys(company_name)
            search_input.send_keys(Keys.RETURN)
            self.production_rate_limit(8, 12)
            
            # Click on "Společnosti" filter
            companies_filter = None
            filter_selectors = [
                "//button[contains(., 'Společnosti')]",
                "//button[contains(., 'Companies')]", 
                "//button[@aria-pressed='false' and contains(., 'Společnosti')]"
            ]
            
            for selector in filter_selectors:
                try:
                    companies_filter = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, selector)
                    ))
                    self.logger.info(f"Found filter with: {selector}")
                    break
                except:
                    continue
                    
            if not companies_filter:
                # Try to find all filter buttons
                all_filters = self.driver.find_elements(By.CSS_SELECTOR, ".search-reusables__filter-pill-button")
                for filter_btn in all_filters:
                    if "Společnosti" in filter_btn.text or "Companies" in filter_btn.text:
                        companies_filter = filter_btn
                        self.logger.info(f"Found filter by text: {filter_btn.text}")
                        break
                        
            if not companies_filter:
                raise TimeoutException("Cannot find 'Společnosti' filter button")
                
            companies_filter.click()
            self.production_rate_limit(8, 12)
            
            # Find best matching company
            all_company_links = []
            selectors_to_try = [
                "a[href*='/company/']",
                "a.YTEbxfHDGCFyuvPAyVvzNRyzZYcheiwKQ",
                "a[data-test-app-aware-link][href*='/company/']"
            ]
            
            for selector in selectors_to_try:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_company_links.extend(links)
                    if links:
                        self.logger.info(f"Found {len(links)} companies with: {selector}")
                except:
                    continue
            
            if not all_company_links:
                raise TimeoutException("No company links found")
                
            # Find best match
            best_match = None
            company_name_clean = company_name.lower().replace(",", "").replace(".", "").strip()
            
            for link in all_company_links:
                link_text = link.text.lower().replace(",", "").replace(".", "").strip()
                
                if company_name_clean in link_text or link_text in company_name_clean:
                    if len(link_text) > 3:
                        best_match = link
                        self.logger.info(f"Best match: {link.text}")
                        break
                        
            if not best_match and all_company_links:
                best_match = all_company_links[0]
                self.logger.info(f"Using first result: {best_match.text}")
                
            company_url = best_match.get_attribute('href')
            actual_company_name = best_match.text.strip()
            
            return company_url, actual_company_name
            
        except Exception as e:
            self.logger.error(f"Company search failed for {company_name}: {e}")
            print(f"Company not found: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            return None, None
    
    def get_people_from_company(self, company_url, company_name):
        """Get people with production-safe approach"""
        try:
            self.logger.info(f"Getting people from: {company_name}")
            print(f"Getting people from: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            
            # Navigate to company page
            self.driver.get(company_url)
            self.production_rate_limit(10, 15)
            
            # Click on "Lidé" tab
            people_tab = None
            try:
                people_tab = self.wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.org-page-navigation__item-anchor[href*='/people/']")
                ))
                self.logger.info("Found 'Lidé' tab")
            except:
                # Fallback: find all navigation links
                nav_links = self.driver.find_elements(By.CSS_SELECTOR, "a.org-page-navigation__item-anchor")
                for link in nav_links:
                    if "Lidé" in link.text:
                        people_tab = link
                        break
                        
            if not people_tab:
                raise TimeoutException("Cannot find 'Lidé' tab")
                
            people_tab.click()
            self.production_rate_limit(8, 12)
            
            # Search for stavbyvedoucí
            search_term = "stavbyvedoucí"
            self.logger.info(f"Searching for: {search_term}")
            
            try:
                search_textarea = self.wait.until(EC.presence_of_element_located(
                    (By.ID, "people-search-keywords")
                ))
                
                self.human_like_behavior()
                
                # Type slowly and naturally
                search_textarea.clear()
                time.sleep(random.uniform(1, 2))
                
                for char in search_term:
                    search_textarea.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.2))
                
                time.sleep(random.uniform(2, 3))
                search_textarea.send_keys(Keys.RETURN)
                self.production_rate_limit(10, 15)
                
            except Exception as e:
                self.logger.error(f"Search failed: {e}")
                return
            
            # Load all pages by clicking "Show more"
            print("Loading all pages...")
            self.logger.info("Starting pagination")
            
            max_clicks = 15  # Conservative limit
            clicks_made = 0
            
            while clicks_made < max_clicks:
                self.logger.info(f"Looking for 'Show more' button (click {clicks_made + 1})")
                
                if clicks_made > 0:
                    self.human_like_behavior()
                
                show_more_found = False
                try:
                    show_more_btn = self.driver.find_element(By.CSS_SELECTOR, ".scaffold-finite-scroll__load-button")
                    
                    if show_more_btn.is_enabled() and show_more_btn.is_displayed():
                        self.logger.info("Found 'Show more' button - clicking")
                        
                        # Scroll to button
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", show_more_btn)
                        time.sleep(random.uniform(1, 2))
                        show_more_btn.click()
                        
                        # Conservative wait for content to load
                        self.production_rate_limit(12, 18)
                        
                        show_more_found = True
                        clicks_made += 1
                except:
                    pass
                
                if not show_more_found:
                    self.logger.info(f"No more 'Show more' button found after {clicks_made} clicks")
                    break
            
            # Extract all people from fully loaded page
            print("Extracting all people from loaded page...")
            self.logger.info("Starting people extraction")
            
            people_found = self.extract_people_from_page()
            
            if people_found:
                self.logger.info(f"Found {len(people_found)} people")
                print(f"Found {len(people_found)} people with 'stavbyvedoucí' at {company_name.encode('ascii', 'ignore').decode('ascii')}")
                for person in people_found:
                    self.results.append({
                        'company': company_name,
                        'name': person['name'],
                        'position': person['position'],
                        'linkedin_url': person['url']
                    })
            else:
                self.logger.warning("No people found")
                print(f"No 'stavbyvedoucí' found at {company_name.encode('ascii', 'ignore').decode('ascii')}")
                self.results.append({
                    'company': company_name,
                    'name': 'nenalezeno',
                    'position': 'nenalezeno',
                    'linkedin_url': 'nenalezeno'
                })
                
        except Exception as e:
            self.logger.error(f"Error getting people from {company_name}: {e}")
            print(f"Cannot access people page for: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            self.results.append({
                'company': company_name,
                'name': 'nenalezeno',
                'position': 'nenalezeno',
                'linkedin_url': 'nenalezeno'
            })
    
    def extract_people_from_page(self):
        """Extract people with production safety"""
        people = []
        
        try:
            # Wait for content to fully load
            time.sleep(5)
            
            # Try scrolling to ensure all content is loaded
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Find all LinkedIn profile links
            profile_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
            self.logger.info(f"Found {len(profile_links)} profile links")
            
            # Filter for actual people profiles
            people_profiles = []
            for link in profile_links:
                href = link.get_attribute('href')
                if '/in/' in href and '/posts/' not in href and '/activity/' not in href:
                    try:
                        parent = link.find_element(By.XPATH, "./..")
                        text_content = parent.text.strip()
                        
                        if text_content and len(text_content) > 5:
                            people_profiles.append(link)
                    except:
                        continue
            
            self.logger.info(f"Filtered to {len(people_profiles)} actual people profiles")
            
            # Extract data from each profile (limit to avoid overload)
            for profile_link in people_profiles[:30]:  # Conservative limit
                try:
                    url = profile_link.get_attribute('href')
                    
                    # Find the person's card
                    parent_card = profile_link
                    for _ in range(5):
                        try:
                            parent_card = parent_card.find_element(By.XPATH, "./..")
                            if 'card' in parent_card.get_attribute('class').lower():
                                break
                        except:
                            break
                    
                    # Extract name
                    name = ""
                    name_selectors = [".lt-line-clamp", ".t-16", ".t-bold", "span[aria-hidden='true']"]
                    for selector in name_selectors:
                        try:
                            name_elem = parent_card.find_element(By.CSS_SELECTOR, selector)
                            potential_name = name_elem.text.strip()
                            if potential_name and 5 < len(potential_name) < 50 and not potential_name.startswith('Člen'):
                                name = potential_name
                                break
                        except:
                            continue
                    
                    # Extract position
                    position = ""
                    card_text = parent_card.text
                    lines = card_text.split('\n')
                    for line in lines:
                        line_clean = line.strip()
                        if (line_clean and 
                            line_clean != name and 
                            not line_clean.startswith('Člen') and
                            len(line_clean) > 10 and
                            ('stavby' in line_clean.lower() or 
                             'vedoucí' in line_clean.lower() or
                             'manager' in line_clean.lower() or
                             'ved' in line_clean.lower())):
                            position = line_clean
                            break
                    
                    if not position:
                        position = "pozice obsahuje 'stavbyvedoucí'"
                    
                    if name and url:
                        people.append({
                            'name': name,
                            'position': position,
                            'url': url
                        })
                        self.logger.info(f"Added: {name}")
                        
                except Exception as e:
                    self.logger.warning(f"Error processing profile: {e}")
                    continue
                    
            self.logger.info(f"Successfully extracted {len(people)} people")
                    
        except Exception as e:
            self.logger.error(f"Error extracting people: {e}")
            
        return people
    
    def process_companies(self, csv_file_path):
        """Process companies with production monitoring"""
        companies = []
        
        # Read companies
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row:
                    companies.append(row[0].strip())
                    
        total_companies = len(companies)
        self.logger.info(f"Starting production scraping of {total_companies} companies")
        print(f"Processing {total_companies} companies in production mode...")
        
        for i, company in enumerate(companies, 1):
            self.companies_processed = i
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = i / (elapsed / 60) if elapsed > 0 else 0
            
            print(f"\n--- Processing {i}/{total_companies}: {company.encode('ascii', 'ignore').decode('ascii')} ---")
            print(f"Rate: {rate:.1f} companies/minute, Elapsed: {elapsed/60:.1f}min")
            self.logger.info(f"Processing {i}/{total_companies}: {company}")
            
            # Search for company
            company_url, actual_name = self.search_company(company)
            
            if company_url and actual_name:
                self.get_people_from_company(company_url, actual_name)
            else:
                self.results.append({
                    'company': company,
                    'name': 'nenalezeno',
                    'position': 'nenalezeno',
                    'linkedin_url': 'nenalezeno'
                })
                
            # Conservative rate limiting between companies
            self.production_rate_limit(20, 30)
            
            # Save intermediate results every 10 companies
            if i % 10 == 0:
                self.save_results(f'linkedin_intermediate_{i}.xlsx')
                self.logger.info(f"Intermediate results saved at company {i}")
                
    def save_results(self, output_file='linkedin_stavbyvedouci_production.xlsx'):
        """Save results with production formatting"""
        df = pd.DataFrame(self.results)
        df.columns = ['Firma', 'Jméno', 'Pozice', 'LinkedIn odkaz']
        
        # Save to Excel
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Stavbyvedoucí', index=False)
            
            worksheet = writer.sheets['Stavbyvedoucí']
            
            # Format columns
            worksheet.column_dimensions['A'].width = 35
            worksheet.column_dimensions['B'].width = 25  
            worksheet.column_dimensions['C'].width = 50
            worksheet.column_dimensions['D'].width = 20
            
            # Format header
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)
                cell.fill = cell.fill.copy(fgColor='E6E6FA')
            
            # Make links clickable
            for row in range(2, len(df) + 2):
                linkedin_cell = worksheet[f'D{row}']
                if linkedin_cell.value and linkedin_cell.value != 'nenalezeno':
                    linkedin_cell.hyperlink = linkedin_cell.value
                    linkedin_cell.value = 'Otevřít profil'
                    linkedin_cell.font = linkedin_cell.font.copy(color='0000FF', underline='single')
                
        self.logger.info(f"Results saved to: {output_file}")
        print(f"\nResults saved to: {output_file}")
        print(f"Total entries: {len(self.results)}")
        
        # Save CSV backup
        csv_file = output_file.replace('.xlsx', '.csv')
        df.to_csv(csv_file, sep=';', encoding='utf-8-sig', index=False)
        
    def close(self):
        """Close browser and cleanup"""
        self.logger.info("Closing scraper")
        self.driver.quit()

def main():
    print("=== LINKEDIN PRODUCTION SCRAPER ===")
    print("Conservative mode: ON")
    print("Rate limiting: 20-30s between companies")
    print("Headless: ON")
    
    scraper = ProductionLinkedInScraper(headless=True, conservative_mode=True)
    
    try:
        scraper.process_companies(r'C:\Users\vaclavik\Downloads\firmy.csv')
        scraper.save_results('linkedin_stavbyvedouci_production.xlsx')
        
    except Exception as e:
        scraper.logger.error(f"Production error: {e}")
        print(f"Production error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()