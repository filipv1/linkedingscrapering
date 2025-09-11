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

class SmartLinkedInScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.setup_driver()
        self.results = []
        
        if not headless:
            self.manual_login()
            
    def setup_driver(self):
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
            
        # Anti-detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
    def manual_login(self):
        """Manual login for session setup"""
        print("Opening LinkedIn for manual login...")
        self.driver.get("https://www.linkedin.com/feed/")
        
        print("\n" + "="*50)
        print("MANUAL LOGIN REQUIRED")
        print("1. Log in to LinkedIn")
        print("2. Press Enter when ready...")
        print("="*50)
        
        input("Press Enter after login: ")
        print("Login completed. Starting scraping...")
        
    def wait_for_page_load(self, timeout=15):
        """Wait until page is fully loaded"""
        try:
            # Wait for page to be in ready state
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            return True
        except:
            return False
            
    def smart_click(self, element):
        """Click element only when it's ready"""
        try:
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Wait for element to be clickable
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(element))
            
            # Click
            element.click()
            return True
        except:
            return False
            
    def search_company(self, company_name):
        """Smart company search with minimal delays"""
        try:
            print(f"Searching: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            
            # Go to LinkedIn if not there
            if "linkedin.com" not in self.driver.current_url:
                self.driver.get("https://www.linkedin.com/feed/")
                self.wait_for_page_load()
            
            # Find search input
            search_input = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.search-global-typeahead__input")
            ))
            
            # Clear and search
            search_input.clear()
            search_input.send_keys(company_name)
            search_input.send_keys(Keys.RETURN)
            self.wait_for_page_load()
            
            # Click "Společnosti" filter
            companies_filter = None
            try:
                companies_filter = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Společnosti')]")
                ))
            except:
                # Fallback to find by text
                all_filters = self.driver.find_elements(By.CSS_SELECTOR, ".search-reusables__filter-pill-button")
                for filter_btn in all_filters:
                    if "Společnosti" in filter_btn.text:
                        companies_filter = filter_btn
                        break
                        
            if companies_filter and self.smart_click(companies_filter):
                self.wait_for_page_load()
            else:
                raise Exception("Cannot click company filter")
            
            # Find best matching company
            company_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/company/']")
            if not company_links:
                return None, None
                
            # Find best match
            company_name_clean = company_name.lower().replace(",", "").replace(".", "").strip()
            best_match = None
            
            for link in company_links:
                link_text = link.text.lower().replace(",", "").replace(".", "").strip()
                if company_name_clean in link_text or link_text in company_name_clean:
                    if len(link_text) > 3:
                        best_match = link
                        break
                        
            if not best_match:
                best_match = company_links[0]
                
            return best_match.get_attribute('href'), best_match.text.strip()
            
        except Exception as e:
            print(f"Company search failed: {e}")
            return None, None
    
    def get_people_from_company(self, company_url, company_name):
        """Smart people extraction"""
        try:
            print(f"Getting people from: {company_name.encode('ascii', 'ignore').decode('ascii')}")
            
            # Navigate to company
            self.driver.get(company_url)
            self.wait_for_page_load()
            
            # Click "Lidé" tab
            people_tab = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "a.org-page-navigation__item-anchor[href*='/people/']")
            ))
            
            if not self.smart_click(people_tab):
                raise Exception("Cannot click People tab")
                
            self.wait_for_page_load()
            
            # Search for stavbyvedoucí
            search_textarea = self.wait.until(EC.presence_of_element_located(
                (By.ID, "people-search-keywords")
            ))
            
            search_textarea.clear()
            search_textarea.send_keys("stavbyvedoucí")
            search_textarea.send_keys(Keys.RETURN)
            self.wait_for_page_load()
            
            # Click all "Show more" buttons until none left
            print("Loading all pages...")
            clicks_made = 0
            max_clicks = 20
            
            while clicks_made < max_clicks:
                try:
                    show_more_btn = self.driver.find_element(By.CSS_SELECTOR, ".scaffold-finite-scroll__load-button")
                    
                    if show_more_btn.is_enabled() and show_more_btn.is_displayed():
                        print(f"Clicking 'Show more' ({clicks_made + 1})...")
                        
                        if self.smart_click(show_more_btn):
                            self.wait_for_page_load()  # Wait for new content
                            clicks_made += 1
                        else:
                            break
                    else:
                        break
                        
                except:
                    break  # No more button found
            
            print(f"Loaded {clicks_made} additional pages")
            
            # Extract all people from fully loaded page
            people_found = self.extract_people_from_page()
            
            if people_found:
                print(f"Found {len(people_found)} stavbyvedoucí")
                for person in people_found:
                    self.results.append({
                        'company': company_name,
                        'name': person['name'],
                        'position': person['position'],
                        'linkedin_url': person['url']
                    })
            else:
                print("No stavbyvedoucí found")
                self.results.append({
                    'company': company_name,
                    'name': 'nenalezeno',
                    'position': 'nenalezeno',
                    'linkedin_url': 'nenalezeno'
                })
                
        except Exception as e:
            print(f"Error getting people: {e}")
            self.results.append({
                'company': company_name,
                'name': 'nenalezeno',
                'position': 'nenalezeno',
                'linkedin_url': 'nenalezeno'
            })
    
    def extract_people_from_page(self):
        """Extract all people from current page"""
        people = []
        
        try:
            # Ensure all content is loaded
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find profile links
            profile_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
            
            # Filter actual people profiles
            people_profiles = []
            for link in profile_links:
                href = link.get_attribute('href')
                if '/in/' in href and '/posts/' not in href and '/activity/' not in href:
                    try:
                        parent = link.find_element(By.XPATH, "./..")
                        if parent.text.strip() and len(parent.text.strip()) > 5:
                            people_profiles.append(link)
                    except:
                        continue
            
            # Extract data from profiles
            for profile_link in people_profiles[:50]:  # Reasonable limit
                try:
                    url = profile_link.get_attribute('href')
                    
                    # Find parent card
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
                    name_selectors = [".lt-line-clamp", ".t-16", ".t-bold"]
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
                    lines = parent_card.text.split('\n')
                    for line in lines:
                        line_clean = line.strip()
                        if (line_clean and line_clean != name and 
                            not line_clean.startswith('Člen') and len(line_clean) > 10 and
                            ('stavby' in line_clean.lower() or 'vedoucí' in line_clean.lower() or 
                             'manager' in line_clean.lower() or 'ved' in line_clean.lower())):
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
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Extract error: {e}")
            
        return people
    
    def process_companies(self, csv_file_path):
        """Process all companies efficiently"""
        companies = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row:
                    companies.append(row[0].strip())
                    
        print(f"Processing {len(companies)} companies...")
        
        for i, company in enumerate(companies, 1):
            print(f"\n--- {i}/{len(companies)}: {company.encode('ascii', 'ignore').decode('ascii')} ---")
            
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
            
            # Minimal delay between companies
            time.sleep(random.uniform(3, 6))
            
            # Save every 25 companies
            if i % 25 == 0:
                self.save_results(f'linkedin_progress_{i}.xlsx')
                print(f"Progress saved at {i} companies")
                
    def save_results(self, output_file='linkedin_stavbyvedouci_smart.xlsx'):
        """Save results to Excel"""
        df = pd.DataFrame(self.results)
        df.columns = ['Firma', 'Jméno', 'Pozice', 'LinkedIn odkaz']
        
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
                
        print(f"Results saved to: {output_file}")
        print(f"Total entries: {len(self.results)}")
        
    def close(self):
        self.driver.quit()

def main():
    print("=== SMART LINKEDIN SCRAPER ===")
    print("Efficient page loading + smart clicking")
    
    scraper = SmartLinkedInScraper(headless=False)  # Set True for headless
    
    try:
        scraper.process_companies(r'C:\Users\vaclavik\Downloads\firmy.csv')
        scraper.save_results('linkedin_stavbyvedouci_smart.xlsx')
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()