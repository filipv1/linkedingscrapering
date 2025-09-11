from linkedin_scraper import LinkedInScraper
from production_scraper import ProductionLinkedInScraper
import csv
import os
import pandas as pd
import argparse
import time
from datetime import datetime
import json

class ResilientLinkedInScraper:
    def __init__(self, input_file, headless=False, autosave_interval=50, resume=False, max_companies=None):
        self.input_file = input_file
        self.headless = headless
        self.autosave_interval = autosave_interval
        self.resume = resume
        self.max_companies = max_companies
        
        # State management
        self.state_file = 'scraper_state.json'
        self.results = []
        self.processed_companies = set()
        self.current_index = 0
        self.session_restarts = 0
        self.max_session_restarts = 5
        
        # Output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_excel = f'merk_linkedin_results_{timestamp}.xlsx'
        self.output_csv = f'merk_linkedin_results_{timestamp}.csv'
        self.checkpoint_file = f'checkpoint_{timestamp}.xlsx'
        
        # Load previous state if resuming
        if self.resume:
            self.load_state()
        
        self.scraper = None
        
    def load_state(self):
        """Load previous scraping state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.current_index = state.get('current_index', 0)
                    self.processed_companies = set(state.get('processed_companies', []))
                    self.results = state.get('results', [])
                    print(f"Resuming from company {self.current_index + 1}")
                    print(f"Already processed: {len(self.processed_companies)} companies")
                    
                    # Load existing results if available
                    if state.get('checkpoint_file') and os.path.exists(state['checkpoint_file']):
                        self.checkpoint_file = state['checkpoint_file']
                        df = pd.read_excel(self.checkpoint_file)
                        self.results = df.to_dict('records')
                        print(f"Loaded {len(self.results)} existing results from checkpoint")
            except Exception as e:
                print(f"Error loading state: {e}")
                print("Starting fresh...")
    
    def save_state(self):
        """Save current scraping state"""
        state = {
            'current_index': self.current_index,
            'processed_companies': list(self.processed_companies),
            'results': self.results,
            'checkpoint_file': self.checkpoint_file,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def save_checkpoint(self, force=False):
        """Save intermediate results"""
        if not self.results:
            return
            
        # Check if we should save (every N companies or forced)
        if not force and len(self.results) % self.autosave_interval != 0:
            return
        
        try:
            # Save to Excel
            df = pd.DataFrame(self.results)
            df.to_excel(self.checkpoint_file, index=False)
            
            # Also save to CSV as backup
            csv_checkpoint = self.checkpoint_file.replace('.xlsx', '.csv')
            df.to_csv(csv_checkpoint, index=False, encoding='utf-8')
            
            print(f"\n[AUTOSAVE] Saved {len(self.results)} results to checkpoint")
            print(f"  - Excel: {self.checkpoint_file}")
            print(f"  - CSV: {csv_checkpoint}")
            
            # Save state
            self.save_state()
            
        except Exception as e:
            print(f"[ERROR] Failed to save checkpoint: {e}")
    
    def init_scraper(self):
        """Initialize or reinitialize the scraper"""
        try:
            # Close existing scraper if any
            if self.scraper:
                try:
                    self.scraper.close()
                except:
                    pass
            
            # Create new scraper instance
            if self.headless:
                print("Initializing headless scraper...")
                self.scraper = ProductionLinkedInScraper(headless=True, conservative_mode=True)
            else:
                print("Initializing standard scraper (manual login required)...")
                self.scraper = LinkedInScraper()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize scraper: {e}")
            return False
    
    def process_single_company(self, company_name):
        """Process a single company with error handling"""
        try:
            # Skip if already processed
            if company_name in self.processed_companies:
                print(f"Skipping (already processed): {company_name}")
                return None
            
            print(f"\nProcessing: {company_name}")
            
            # Search for company
            company_url, actual_name = self.scraper.search_company(company_name)
            
            if company_url:
                # Search for people
                people = self.scraper.search_people_at_company(
                    company_url, 
                    "stavbyvedoucí", 
                    actual_name
                )
                
                if people:
                    for person in people:
                        result = {
                            'Company': actual_name or company_name,
                            'Name': person.get('name', 'N/A'),
                            'Title': person.get('title', 'N/A'),
                            'LinkedIn': person.get('linkedin_url', ''),
                            'Processed_At': datetime.now().isoformat()
                        }
                        self.results.append(result)
                        print(f"  Found: {person.get('name', 'N/A')} - {person.get('title', 'N/A')}")
                else:
                    # No people found
                    result = {
                        'Company': company_name,
                        'Name': 'nenalezeno',
                        'Title': 'nenalezeno',
                        'LinkedIn': '',
                        'Processed_At': datetime.now().isoformat()
                    }
                    self.results.append(result)
                    print(f"  No people found")
            else:
                # Company not found
                result = {
                    'Company': company_name,
                    'Name': 'firma nenalezena',
                    'Title': 'firma nenalezena',
                    'LinkedIn': '',
                    'Processed_At': datetime.now().isoformat()
                }
                self.results.append(result)
                print(f"  Company not found")
            
            # Mark as processed
            self.processed_companies.add(company_name)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to process {company_name}: {e}")
            return False
    
    def run(self):
        """Main execution loop with resilience"""
        print("=" * 60)
        print("RESILIENT LINKEDIN SCRAPER FOR MERK COMPANIES")
        print("=" * 60)
        print(f"Input file: {self.input_file}")
        print(f"Autosave every: {self.autosave_interval} companies")
        print(f"Resume mode: {self.resume}")
        print("=" * 60)
        
        # Read companies from CSV
        try:
            df = pd.read_csv(self.input_file, encoding='utf-8')
            companies = df.iloc[:, 0].tolist()
            
            # Apply max_companies limit if specified
            if self.max_companies and self.max_companies > 0:
                companies = companies[:self.max_companies]
                print(f"Limited to first {self.max_companies} companies")
            
            total_companies = len(companies)
            print(f"Total companies to process: {total_companies}")
        except Exception as e:
            print(f"[ERROR] Failed to read input file: {e}")
            return
        
        # Initialize scraper
        if not self.init_scraper():
            print("[ERROR] Failed to initialize scraper")
            return
        
        # Main processing loop
        try:
            for idx in range(self.current_index, total_companies):
                self.current_index = idx
                company = companies[idx]
                
                print(f"\n--- Processing {idx + 1}/{total_companies}: {company} ---")
                
                # Try to process company
                success = False
                retry_count = 0
                max_retries = 3
                
                while not success and retry_count < max_retries:
                    try:
                        success = self.process_single_company(company)
                        
                        if not success and retry_count < max_retries - 1:
                            print(f"  Retrying ({retry_count + 1}/{max_retries - 1})...")
                            time.sleep(5)
                            retry_count += 1
                        else:
                            break
                            
                    except Exception as e:
                        if "invalid session id" in str(e).lower():
                            print("\n[SESSION ERROR] Browser session lost. Attempting to restart...")
                            
                            # Save current progress
                            self.save_checkpoint(force=True)
                            
                            # Try to restart session
                            if self.session_restarts < self.max_session_restarts:
                                self.session_restarts += 1
                                print(f"Restarting session (attempt {self.session_restarts}/{self.max_session_restarts})...")
                                
                                time.sleep(10)  # Wait before restart
                                
                                if self.init_scraper():
                                    print("Session restarted successfully")
                                    retry_count += 1
                                    continue
                                else:
                                    print("[FATAL] Failed to restart session")
                                    break
                            else:
                                print("[FATAL] Maximum session restarts exceeded")
                                break
                        else:
                            print(f"[ERROR] Unexpected error: {e}")
                            retry_count += 1
                
                # Autosave checkpoint
                if (idx + 1) % self.autosave_interval == 0:
                    self.save_checkpoint(force=True)
                    
                # Add small delay between companies
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n[INTERRUPTED] Scraping stopped by user")
        except Exception as e:
            print(f"\n[CRITICAL ERROR] {e}")
        finally:
            # Save final results
            self.save_final_results()
            
            # Clean up
            try:
                if self.scraper:
                    self.scraper.close()
            except:
                pass
    
    def save_final_results(self):
        """Save final results"""
        if not self.results:
            print("\nNo results to save")
            return
        
        try:
            df = pd.DataFrame(self.results)
            
            # Save to Excel
            df.to_excel(self.output_excel, index=False)
            print(f"\nFinal results saved to: {self.output_excel}")
            
            # Save to CSV
            df.to_csv(self.output_csv, index=False, encoding='utf-8')
            print(f"CSV backup saved to: {self.output_csv}")
            
            # Statistics
            print("\n" + "=" * 60)
            print("SCRAPING STATISTICS:")
            print(f"  Total companies processed: {len(self.processed_companies)}")
            print(f"  Total results: {len(self.results)}")
            print(f"  Session restarts: {self.session_restarts}")
            
            # Clean up state file if completed successfully
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
                print("\nState file cleaned up")
                
        except Exception as e:
            print(f"[ERROR] Failed to save final results: {e}")

def main():
    parser = argparse.ArgumentParser(description='Resilient LinkedIn Scraper for Merk Companies')
    parser.add_argument('--input', type=str, 
                       default=r'C:\Users\vaclavik\scrpr\merk_companies_20250910_153225.csv',
                       help='Input CSV file with companies')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode')
    parser.add_argument('--autosave', type=int, default=50,
                       help='Autosave interval (number of companies)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from previous state')
    parser.add_argument('--max', type=int, default=None,
                       help='Maximum number of companies to process')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        return
    
    # Create scraper and run
    scraper = ResilientLinkedInScraper(
        input_file=args.input,
        headless=args.headless,
        autosave_interval=args.autosave,
        resume=args.resume,
        max_companies=args.max
    )
    
    scraper.run()

if __name__ == "__main__":
    main()