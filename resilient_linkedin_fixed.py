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
        self.current_index = 0
        self.processed_count = 0
        self.session_restarts = 0
        self.max_session_restarts = 5
        
        # Output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_excel = f'all_employees_{timestamp}.xlsx'
        self.output_csv = f'all_employees_{timestamp}.csv'
        self.checkpoint_file = f'checkpoint_all_employees_{timestamp}.xlsx'
        
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
                    self.processed_count = state.get('processed_count', 0)
                    print(f"Resuming from company {self.current_index + 1}")
                    print(f"Already processed: {self.processed_count} companies")
                    
                    # Use existing checkpoint file if available
                    if state.get('checkpoint_file') and os.path.exists(state['checkpoint_file']):
                        self.checkpoint_file = state['checkpoint_file']
                        print(f"Using existing checkpoint: {self.checkpoint_file}")
            except Exception as e:
                print(f"Error loading state: {e}")
                print("Starting fresh...")
    
    def save_state(self):
        """Save current scraping state"""
        state = {
            'current_index': self.current_index,
            'processed_count': self.processed_count,
            'checkpoint_file': self.checkpoint_file,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def save_checkpoint(self, force=False):
        """Save intermediate results from scraper"""
        if not self.scraper or not self.scraper.results:
            return
            
        # Check if we should save (every N companies or forced)
        if not force and self.processed_count % self.autosave_interval != 0:
            return
        
        try:
            # Get results from scraper
            self.scraper.save_results(self.checkpoint_file)
            
            # Also save to CSV as backup
            csv_checkpoint = self.checkpoint_file.replace('.xlsx', '.csv')
            df = pd.DataFrame(self.scraper.results)
            df.to_csv(csv_checkpoint, index=False, encoding='utf-8')
            
            print(f"\n[AUTOSAVE] Saved {len(self.scraper.results)} results to checkpoint")
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
            
            # If resuming, load existing results
            if self.resume and os.path.exists(self.checkpoint_file):
                try:
                    df = pd.read_excel(self.checkpoint_file)
                    # Convert back to scraper format
                    self.scraper.results = []
                    for _, row in df.iterrows():
                        self.scraper.results.append({
                            'company': row.get('Firma', row.get('company', '')),
                            'name': row.get('Jméno', row.get('name', '')),
                            'position': row.get('Pozice', row.get('position', '')),
                            'linkedin_url': row.get('LinkedIn odkaz', row.get('linkedin_url', ''))
                        })
                    print(f"Loaded {len(self.scraper.results)} existing results")
                except Exception as e:
                    print(f"Warning: Could not load previous results: {e}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize scraper: {e}")
            return False
    
    def process_single_company(self, company_name):
        """Process a single company - load all employees without filtering"""
        try:
            print(f"Processing: {company_name}")

            # Search for company (original method)
            company_url, actual_name = self.scraper.search_company(company_name)

            if company_url and actual_name:
                # Get all people from company (no filtering)
                self.scraper.get_all_people_from_company(company_url, actual_name)
            else:
                # Company not found - add fallback entry
                self.scraper.results.append({
                    'company': company_name,
                    'name': 'nenalezeno',
                    'position': 'nenalezeno',
                    'linkedin_url': 'nenalezeno'
                })
                print(f"  Company not found")

            # Rate limiting (original method)
            self.scraper.rate_limit(3, 6)

            self.processed_count += 1
            return True

        except Exception as e:
            print(f"[ERROR] Failed to process {company_name}: {e}")
            raise  # Re-raise to handle in main loop
    
    def run(self):
        """Main execution loop with resilience"""
        print("=" * 60)
        print("RESILIENT LINKEDIN SCRAPER - ALL EMPLOYEES")
        print("=" * 60)
        print(f"Input file: {self.input_file}")
        print(f"Autosave every: {self.autosave_interval} companies")
        print(f"Resume mode: {self.resume}")
        if self.max_companies:
            print(f"Max companies: {self.max_companies}")
        print("=" * 60)
        
        # Read companies from CSV
        try:
            companies = []
            with open(self.input_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if row:
                        companies.append(row[0].strip())
            
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
                
                print(f"\n--- Processing {idx + 1}/{total_companies}: {company.encode('ascii', 'ignore').decode('ascii')} ---")
                
                # Try to process company
                success = False
                retry_count = 0
                max_retries = 3
                
                while not success and retry_count < max_retries:
                    try:
                        success = self.process_single_company(company)
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        
                        if "invalid session id" in error_msg or "no such window" in error_msg:
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
                            if retry_count < max_retries:
                                print(f"  Retrying ({retry_count}/{max_retries - 1})...")
                                time.sleep(5)
                
                # Autosave checkpoint
                if self.processed_count > 0 and self.processed_count % self.autosave_interval == 0:
                    self.save_checkpoint(force=True)
                
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
        if not self.scraper or not self.scraper.results:
            print("\nNo results to save")
            return
        
        try:
            # Use scraper's save method for proper formatting
            self.scraper.save_results(self.output_excel)
            print(f"\nFinal results saved to: {self.output_excel}")
            
            # Also save CSV backup
            df = pd.DataFrame(self.scraper.results)
            df.to_csv(self.output_csv, index=False, encoding='utf-8')
            print(f"CSV backup saved to: {self.output_csv}")
            
            # Statistics
            print("\n" + "=" * 60)
            print("SCRAPING STATISTICS:")
            print(f"  Total companies processed: {self.processed_count}")
            print(f"  Total results: {len(self.scraper.results)}")
            print(f"  Session restarts: {self.session_restarts}")
            
            # Clean up state file if completed successfully
            if self.current_index >= self.processed_count - 1:
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