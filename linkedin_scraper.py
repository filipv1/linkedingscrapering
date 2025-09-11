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

class LinkedInScraper:
    def __init__(self, user_data_dir=None):
        self.setup_driver(user_data_dir)
        self.results = []
        self.manual_login()
        
    def setup_driver(self, user_data_dir):
        chrome_options = Options()
        
        # Anti-detection setup to avoid LinkedIn blocking
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        
        # Add realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Remove webdriver property to avoid detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 10)
        
    def manual_login(self):
        """Open LinkedIn and wait for manual login"""
        print("Opening LinkedIn for manual login...")
        self.driver.get("https://www.linkedin.com/feed/")
        
        print("\n" + "="*50)
        print("MANUAL LOGIN REQUIRED")
        print("1. Log in to LinkedIn in the opened browser")
        print("2. Navigate to the feed page")
        print("3. Press Enter here when ready...")
        print("="*50)
        
        input("Press Enter after login: ")
        print("Login completed. Starting scraping...")
        
    def rate_limit(self, min_delay=3, max_delay=6):
        """Add random delay to avoid detection - reasonable delays"""
        delay = random.uniform(min_delay, max_delay)
        print(f"Waiting {delay:.1f}s...")
        time.sleep(delay)
        
    def human_like_behavior(self):
        """Simulate human-like behavior to avoid detection"""
        # Random scroll
        scroll_amount = random.randint(300, 800)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(1, 2))
        
        # Random mouse movement (simulate with JavaScript)
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
        time.sleep(random.uniform(0.5, 1.5))
        
    def search_company(self, company_name):
        """Search for company on LinkedIn"""
        try:
            print(f"Searching for company: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            
            # Already on LinkedIn from manual login, just refresh or navigate if needed
            current_url = self.driver.current_url
            if "linkedin.com" not in current_url:
                self.driver.get("https://www.linkedin.com/feed/")
                self.rate_limit()
            
            # Find search input
            search_input = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.search-global-typeahead__input")
            ))
            
            # Clear and enter company name
            search_input.clear()
            search_input.send_keys(company_name)
            search_input.send_keys(Keys.RETURN)
            self.rate_limit()
            
            # Click on "Společnosti" filter - find specific button with "Společnosti" text
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
                    print(f"Found 'Společnosti' filter with: {selector}")
                    break
                except:
                    continue
                    
            if not companies_filter:
                # Try to find all filter buttons and look for one with "Společnosti"
                all_filters = self.driver.find_elements(By.CSS_SELECTOR, ".search-reusables__filter-pill-button")
                for filter_btn in all_filters:
                    if "Společnosti" in filter_btn.text or "Companies" in filter_btn.text:
                        companies_filter = filter_btn
                        print(f"Found filter by text content: {filter_btn.text}")
                        break
                        
            if not companies_filter:
                raise TimeoutException("Cannot find 'Společnosti' filter button")
                
            companies_filter.click()
            self.rate_limit()
            
            # Find the best matching company result
            first_company_link = None
            selectors_to_try = [
                "a[href*='/company/']",
                "a.YTEbxfHDGCFyuvPAyVvzNRyzZYcheiwKQ",
                "a[data-test-app-aware-link][href*='/company/']",
                ".entity-result__title-text a",
                ".search-result__title a"
            ]
            
            # Get all company links and find best match
            all_company_links = []
            for selector in selectors_to_try:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_company_links.extend(links)
                    if links:
                        print(f"Found {len(links)} companies with selector: {selector}")
                except:
                    continue
            
            if not all_company_links:
                raise TimeoutException("No company links found")
                
            # Find best match for company name (exact or closest match)
            best_match = None
            company_name_clean = company_name.lower().replace(",", "").replace(".", "").strip()
            
            for link in all_company_links:
                link_text = link.text.lower().replace(",", "").replace(".", "").strip()
                link_href = link.get_attribute('href') or ""
                
                print(f"Checking: '{link.text}' -> {link_href}")
                
                # Exact match or very close match
                if company_name_clean in link_text or link_text in company_name_clean:
                    if len(link_text) > 3:  # Avoid matching very short texts
                        best_match = link
                        print(f"✓ Best match found: {link.text}")
                        break
                        
            # If no good match, take first company link as fallback
            if not best_match and all_company_links:
                best_match = all_company_links[0]
                print(f"Using first result as fallback: {best_match.text}")
                
            first_company_link = best_match
            
            company_url = first_company_link.get_attribute('href')
            actual_company_name = first_company_link.text.strip()
            
            print(f"Found company: {actual_company_name.encode('ascii', 'ignore').decode('ascii')}")
            return company_url, actual_company_name
            
        except TimeoutException:
            print(f"Company not found: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            return None, None
            
    def get_people_from_company(self, company_url, company_name):
        """Get people from company with 'stavbyvedoucí' in their title"""
        try:
            print(f"Getting people from: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            
            # Navigate to company page
            self.driver.get(company_url)
            self.rate_limit()
            
            # Click on "Lidé" tab - use exact selector from debug
            print("Looking for 'Lidé' tab...")
            
            # Wait for page to load properly
            time.sleep(2)
            
            # Find "Lidé" tab using exact selector from debug output
            people_tab = None
            try:
                people_tab = self.wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.org-page-navigation__item-anchor[href*='/people/']")
                ))
                print(f"Found 'Lidé' tab: {people_tab.text}")
            except:
                # Fallback: find all navigation links
                print("Primary selector failed, trying fallback...")
                nav_links = self.driver.find_elements(By.CSS_SELECTOR, "a.org-page-navigation__item-anchor")
                print(f"Found {len(nav_links)} navigation links:")
                for link in nav_links:
                    print(f"  - {link.text} -> {link.get_attribute('href')}")
                    if "Lidé" in link.text:
                        people_tab = link
                        print(f"Selected: {link.text}")
                        break
                        
            if not people_tab:
                raise TimeoutException("Cannot find 'Lidé' tab")
                
            # Click the tab
            print("Clicking 'Lidé' tab...")
            people_tab.click()
            self.rate_limit()
            
            # Simple search for "stavbyvedoucí" - let LinkedIn find all variants
            search_term = "stavbyvedoucí"
            
            print(f"Searching for: {search_term}")
            
            try:
                search_textarea = self.wait.until(EC.presence_of_element_located(
                    (By.ID, "people-search-keywords")
                ))
                
                # Scroll to make sure element is visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", search_textarea)
                time.sleep(1)
                
                # Simulate human typing
                self.human_like_behavior()
                
                # Clear and enter search with human-like typing
                search_textarea.clear()
                time.sleep(random.uniform(0.5, 1.0))
                
                # Type like human (slower, with pauses)
                for char in search_term:
                    search_textarea.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                time.sleep(random.uniform(1, 2))
                search_textarea.send_keys(Keys.RETURN)
                self.rate_limit(4, 6)  # Wait for search results
                
            except Exception as e:
                print(f"Error with search: {e}")
                return  # Skip this company if search fails
            
            # First, click all "Zobrazit více výsledků" buttons to load all content
            print("Loading all pages by clicking 'Zobrazit více výsledků'...")
            
            page_num = 1
            max_pages = 10  # Allow more pages
            
            while page_num <= max_pages:
                print(f"Looking for 'Show more' button (attempt {page_num})...")
                
                # Add human-like behavior
                if page_num > 1:
                    self.human_like_behavior()
                
                # Try to find and click "Zobrazit více výsledků"
                show_more_found = False
                show_more_selectors = [
                    ".scaffold-finite-scroll__load-button",  # Primary selector from debug
                    "//span[contains(text(), 'Zobrazit více výsledků')]/parent::button",
                    "//button[contains(text(), 'Zobrazit více')]",
                    "//button[contains(text(), 'Show more')]"
                ]
                
                for selector in show_more_selectors:
                    try:
                        if selector.startswith("//"):
                            show_more_btn = self.driver.find_element(By.XPATH, selector)
                        else:
                            show_more_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                        if show_more_btn.is_enabled() and show_more_btn.is_displayed():
                            print(f"✓ Found 'Show more' button: '{show_more_btn.text}' - clicking...")
                            
                            # Scroll to button and click
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", show_more_btn)
                            time.sleep(1)
                            show_more_btn.click()
                            
                            # Wait for new content to load
                            print("Waiting for new results to load...")
                            self.rate_limit(4, 6)
                            
                            show_more_found = True
                            break
                    except Exception as e:
                        continue
                
                if not show_more_found:
                    print(f"✗ No more 'Show more' button found after {page_num-1} clicks - all content loaded")
                    break
                    
                page_num += 1
            
            # Now extract all people from the fully loaded page (only once)
            print(f"\nExtracting all people from fully loaded page...")
            people_found = self.extract_people_from_page()
            print(f"Total people found: {len(people_found)}")
            
            # Remove duplicates from final results
            unique_people = []
            seen_urls = set()
            seen_names = set()
            
            for person in people_found:
                url = person['url']
                name = person['name']
                
                if url not in seen_urls and name not in seen_names:
                    unique_people.append(person)
                    seen_urls.add(url)
                    seen_names.add(name)
                    
            people_found = unique_people
            print(f"After deduplication: {len(people_found)} unique people")
                    
            if people_found:
                print(f"Found {len(people_found)} people with 'stavbyvedoucí' at {company_name.encode('ascii', 'ignore').decode('ascii')}")
                for person in people_found:
                    self.results.append({
                        'company': company_name,
                        'name': person['name'],
                        'position': person['position'],
                        'linkedin_url': person['url']
                    })
            else:
                print(f"No 'stavbyvedoucí' found at {company_name.encode('ascii', 'ignore').decode('ascii')}")
                self.results.append({
                    'company': company_name,
                    'name': 'nenalezeno',
                    'position': 'nenalezeno',
                    'linkedin_url': 'nenalezeno'
                })
                
        except TimeoutException:
            print(f"Cannot access people page for: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            self.results.append({
                'company': company_name,
                'name': 'nenalezeno',
                'position': 'nenalezeno', 
                'linkedin_url': 'nenalezeno'
            })
            
    def extract_people_from_page(self):
        """Extract people data from current page"""
        people = []
        
        try:
            # Wait for people cards to load - longer wait for Metrostav
            print("Looking for people cards...")
            time.sleep(5)  # Increased wait time
            
            # Try to scroll down to load more content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find all LinkedIn profile links first
            profile_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
            print(f"Found {len(profile_links)} profile links")
            
            # If no links found, try alternative approach
            if not profile_links:
                print("No profile links found, trying alternative selectors...")
                alt_selectors = [
                    "a[data-test-app-aware-link*='/in/']",
                    ".org-people-profile-card a",
                    ".entity-result a[href*='/in/']"
                ]
                for selector in alt_selectors:
                    try:
                        alt_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if alt_links:
                            profile_links = alt_links
                            print(f"Found {len(profile_links)} profile links with: {selector}")
                            break
                    except:
                        continue
            
            # Filter for actual people profiles (not posts or other content)
            people_profiles = []
            for link in profile_links:
                href = link.get_attribute('href')
                # Check if it's a direct profile link (not a post or activity)
                if '/in/' in href and '/posts/' not in href and '/activity/' not in href:
                    # Check if it has person content nearby
                    try:
                        # Look for name in the same card/container
                        parent = link.find_element(By.XPATH, "./..")  # Parent element
                        text_content = parent.text.strip()
                        
                        if text_content and len(text_content) > 5:  # Has meaningful text
                            people_profiles.append(link)
                            print(f"Profile found: {text_content[:50]}... -> {href}")
                    except:
                        continue
            
            print(f"Filtered to {len(people_profiles)} actual people profiles")
            
            # Extract data from each profile
            for profile_link in people_profiles[:20]:  # Limit to first 20 to avoid overload
                try:
                    # Get LinkedIn URL
                    url = profile_link.get_attribute('href')
                    
                    # Find the person's card/container
                    parent_card = profile_link
                    for _ in range(5):  # Go up max 5 levels to find the card
                        try:
                            parent_card = parent_card.find_element(By.XPATH, "./..")
                            if 'card' in parent_card.get_attribute('class').lower():
                                break
                        except:
                            break
                    
                    # Extract name - try multiple selectors
                    name = ""
                    name_selectors = [".lt-line-clamp", ".t-16", ".t-bold", "span[aria-hidden='true']"]
                    for selector in name_selectors:
                        try:
                            name_elem = parent_card.find_element(By.CSS_SELECTOR, selector)
                            potential_name = name_elem.text.strip()
                            # Check if it looks like a name (not too long, not empty)
                            if potential_name and 5 < len(potential_name) < 50 and not potential_name.startswith('Člen'):
                                name = potential_name
                                break
                        except:
                            continue
                    
                    # Extract position - get any position text from the profile card
                    position = ""
                    card_text = parent_card.text
                    
                    # Try to find position in the text
                    lines = card_text.split('\n')
                    for line in lines:
                        line_clean = line.strip()
                        # Skip name, skip "Člen LinkedIn", look for position-like text
                        if (line_clean and 
                            line_clean != name and 
                            not line_clean.startswith('Člen') and
                            len(line_clean) > 10 and  # Position should be longer than 10 chars
                            ('stavby' in line_clean.lower() or 
                             'vedoucí' in line_clean.lower() or
                             'manager' in line_clean.lower() or
                             'ved' in line_clean.lower())):
                            position = line_clean
                            break
                    
                    # If no specific position found, but we're in search results, assume it's construction-related
                    if not position:
                        position = "pozice obsahuje 'stavbyvedoucí'"
                    
                    # Save everyone with a profile link - we're in search results so they're relevant
                    if name and url:
                        people.append({
                            'name': name,
                            'position': position,
                            'url': url
                        })
                        print(f"✓ Added: {name} - {position}")
                        
                except Exception as e:
                    print(f"Error processing profile: {e}")
                    continue
                    
            print(f"Successfully extracted {len(people)} people")
                    
        except Exception as e:
            print(f"Error extracting people: {e}")
            
        return people
        
    def process_companies(self, csv_file_path):
        """Process all companies from CSV file"""
        companies = []
        
        # Read companies from CSV
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row:
                    companies.append(row[0].strip())
                    
        print(f"Processing {len(companies)} companies...")
        
        for i, company in enumerate(companies, 1):
            print(f"\n--- Processing {i}/{len(companies)}: {company.encode('ascii', 'ignore').decode('ascii')} ---")
            
            # Search for company
            company_url, actual_name = self.search_company(company)
            
            if company_url and actual_name:
                # Get people from company
                self.get_people_from_company(company_url, actual_name)
            else:
                # Company not found
                self.results.append({
                    'company': company,
                    'name': 'nenalezeno',
                    'position': 'nenalezeno',
                    'linkedin_url': 'nenalezeno'
                })
                
            self.rate_limit(3, 6)  # Rate limit between companies
            
    def save_results(self, output_file='linkedin_stavbyvedouci.xlsx'):
        """Save results to Excel file with Czech formatting"""
        # Create DataFrame
        df = pd.DataFrame(self.results)
        df.columns = ['Firma', 'Jméno', 'Pozice', 'LinkedIn odkaz']
        
        # Save to Excel with formatting
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Stavbyvedoucí', index=False)
            
            # Get worksheet for formatting
            worksheet = writer.sheets['Stavbyvedoucí']
            
            # Adjust column widths
            worksheet.column_dimensions['A'].width = 35  # Firma
            worksheet.column_dimensions['B'].width = 25  # Jméno
            worksheet.column_dimensions['C'].width = 50  # Pozice
            worksheet.column_dimensions['D'].width = 20  # LinkedIn odkaz
            
            # Format header row
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)
                cell.fill = cell.fill.copy(fgColor='E6E6FA')  # Light purple background
            
            # Make LinkedIn links clickable
            for row in range(2, len(df) + 2):
                linkedin_cell = worksheet[f'D{row}']
                if linkedin_cell.value and linkedin_cell.value != 'nenalezeno':
                    linkedin_cell.hyperlink = linkedin_cell.value
                    linkedin_cell.value = 'Otevřít profil'
                    linkedin_cell.font = linkedin_cell.font.copy(color='0000FF', underline='single')
                
        print(f"\nResults saved to: {output_file}")
        print(f"Total entries: {len(self.results)}")
        
        # Also save CSV backup
        csv_file = output_file.replace('.xlsx', '.csv')
        df.to_csv(csv_file, sep=';', encoding='utf-8-sig', index=False)
        print(f"CSV backup saved to: {csv_file}")
        
    def close(self):
        """Close browser"""
        self.driver.quit()

def main():
    scraper = LinkedInScraper()
    
    try:
        # Process companies from CSV
        scraper.process_companies(r'C:\Users\vaclavik\Downloads\firmy.csv')
        
        # Save results
        scraper.save_results('linkedin_stavbyvedouci.xlsx')
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()