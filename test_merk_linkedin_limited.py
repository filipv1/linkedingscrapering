from linkedin_scraper import LinkedInScraper
import csv
import os
import pandas as pd

def main():
    # Path to merk companies CSV
    merk_csv_path = r'C:\Users\vaclavik\scrpr\merk_companies_20250910_153225.csv'
    
    # Check if file exists
    if not os.path.exists(merk_csv_path):
        print(f"ERROR: CSV file not found at {merk_csv_path}")
        print("Please make sure the merk_companies CSV file exists.")
        return
    
    print("=" * 60)
    print("LINKEDIN SCRAPER - MERK COMPANIES LIMITED TEST")
    print("=" * 60)
    print(f"\nSource file: {merk_csv_path}")
    
    # Read the CSV to see how many companies we have
    try:
        df = pd.read_csv(merk_csv_path, encoding='utf-8')
        total_companies = len(df)
        print(f"Total companies in file: {total_companies}")
        
        # Ask user how many to process
        print("\nHow many companies would you like to test?")
        print(f"Enter a number (1-{total_companies}) or press ENTER for all:")
        user_input = input().strip()
        
        if user_input:
            try:
                limit = int(user_input)
                if limit < 1 or limit > total_companies:
                    print(f"Invalid number. Using all {total_companies} companies.")
                    limit = total_companies
            except ValueError:
                print(f"Invalid input. Using all {total_companies} companies.")
                limit = total_companies
        else:
            limit = total_companies
        
        # Create temporary CSV with limited companies if needed
        if limit < total_companies:
            temp_csv_path = 'temp_merk_companies_limited.csv'
            df_limited = df.head(limit)
            df_limited.to_csv(temp_csv_path, index=False, encoding='utf-8')
            csv_to_process = temp_csv_path
            print(f"\nProcessing first {limit} companies...")
            
            # Show which companies will be processed
            print("\nCompanies to be processed:")
            for idx, row in df_limited.iterrows():
                print(f"  {idx+1}. {row.iloc[0]}")
        else:
            csv_to_process = merk_csv_path
            print(f"\nProcessing all {total_companies} companies...")
        
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Initialize scraper
    scraper = LinkedInScraper()
    
    try:
        print("\n" + "-" * 60)
        print("Starting LinkedIn scraping...")
        print("-" * 60)
        
        # Process companies
        scraper.process_companies(csv_to_process)
        
        # Save results with descriptive filename
        if limit < total_companies:
            output_filename = f'merk_companies_linkedin_results_first_{limit}.xlsx'
        else:
            output_filename = 'merk_companies_linkedin_results_all.xlsx'
            
        scraper.save_results(output_filename)
        
        print("\n" + "=" * 60)
        print(f"SCRAPING COMPLETED!")
        print(f"Companies processed: {limit}")
        print(f"Results saved to: {output_filename}")
        print("=" * 60)
        
        # Clean up temp file if created
        if limit < total_companies and os.path.exists('temp_merk_companies_limited.csv'):
            os.remove('temp_merk_companies_limited.csv')
            
    except FileNotFoundError as e:
        print(f"\nERROR: File not found - {e}")
    except Exception as e:
        print(f"\nERROR during scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nClosing browser...")
        scraper.close()
        print("Done.")

if __name__ == "__main__":
    main()