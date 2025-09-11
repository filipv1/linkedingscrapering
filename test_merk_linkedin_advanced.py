from production_scraper import ProductionLinkedInScraper
from linkedin_scraper import LinkedInScraper
import csv
import os
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def process_batch(companies_batch, worker_id, headless=False):
    """Process a batch of companies in a single worker thread"""
    results = []
    
    print(f"[Worker {worker_id}] Starting with {len(companies_batch)} companies")
    
    # Create temporary CSV for this batch
    temp_csv = f'temp_worker_{worker_id}.csv'
    df = pd.DataFrame(companies_batch, columns=['Název firmy'])
    df.to_csv(temp_csv, index=False, encoding='utf-8')
    
    try:
        if headless:
            # Use production scraper for headless mode
            scraper = ProductionLinkedInScraper(headless=True, conservative_mode=True)
        else:
            # Use regular scraper for manual mode
            scraper = LinkedInScraper()
        
        # Process companies
        scraper.process_companies(temp_csv)
        results = scraper.results
        
        print(f"[Worker {worker_id}] Completed {len(results)} results")
        
    except Exception as e:
        print(f"[Worker {worker_id}] Error: {e}")
    finally:
        # Clean up
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
        try:
            scraper.close()
        except:
            pass
    
    return results

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='LinkedIn Scraper for Merk Companies')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers (default: 1)')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    parser.add_argument('--input', type=str, default=r'C:\Users\vaclavik\scrpr\merk_companies_20250910_153225.csv',
                       help='Input CSV file path')
    
    args = parser.parse_args()
    
    # Path to merk companies CSV
    merk_csv_path = args.input
    
    # Check if file exists
    if not os.path.exists(merk_csv_path):
        print(f"ERROR: CSV file not found at {merk_csv_path}")
        return
    
    print("=" * 60)
    print("LINKEDIN SCRAPER - MERK COMPANIES (ADVANCED)")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  - Source file: {merk_csv_path}")
    print(f"  - Headless mode: {args.headless}")
    print(f"  - Workers: {args.workers}")
    print(f"  - Limit: {args.limit if args.limit else 'No limit'}")
    print("=" * 60)
    
    # Read companies from CSV
    try:
        df = pd.read_csv(merk_csv_path, encoding='utf-8')
        companies = df.iloc[:, 0].tolist()  # Get first column
        
        # Apply limit if specified
        if args.limit:
            companies = companies[:args.limit]
        
        total_companies = len(companies)
        print(f"\nTotal companies to process: {total_companies}")
        
        if args.workers > 1:
            # Parallel processing
            print(f"Using {args.workers} parallel workers...")
            
            # Split companies into batches
            batch_size = (total_companies + args.workers - 1) // args.workers
            batches = []
            for i in range(0, total_companies, batch_size):
                batch = companies[i:i + batch_size]
                batches.append(batch)
            
            all_results = []
            
            # Process batches in parallel
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = []
                for i, batch in enumerate(batches):
                    future = executor.submit(process_batch, batch, i+1, args.headless)
                    futures.append(future)
                
                # Collect results
                for future in as_completed(futures):
                    try:
                        results = future.result()
                        all_results.extend(results)
                    except Exception as e:
                        print(f"Worker error: {e}")
            
            # Save combined results
            if all_results:
                output_filename = f'merk_linkedin_results_workers{args.workers}.xlsx'
                df_results = pd.DataFrame(all_results)
                df_results.to_excel(output_filename, index=False)
                print(f"\nResults saved to: {output_filename}")
            
        else:
            # Single worker processing
            if args.headless:
                print("Using headless mode (ProductionLinkedInScraper)...")
                scraper = ProductionLinkedInScraper(headless=True, conservative_mode=True)
            else:
                print("Using standard mode (LinkedInScraper) - manual login required...")
                scraper = LinkedInScraper()
            
            try:
                # Create temporary CSV if limit is applied
                if args.limit:
                    temp_csv = 'temp_limited_companies.csv'
                    df_limited = pd.DataFrame(companies, columns=['Název firmy'])
                    df_limited.to_csv(temp_csv, index=False, encoding='utf-8')
                    csv_to_process = temp_csv
                else:
                    csv_to_process = merk_csv_path
                
                # Process companies
                scraper.process_companies(csv_to_process)
                
                # Save results
                output_filename = f'merk_linkedin_results{"_headless" if args.headless else ""}.xlsx'
                scraper.save_results(output_filename)
                
                print(f"\nResults saved to: {output_filename}")
                
                # Clean up temp file
                if args.limit and os.path.exists('temp_limited_companies.csv'):
                    os.remove('temp_limited_companies.csv')
                    
            finally:
                scraper.close()
        
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()