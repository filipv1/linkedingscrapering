from linkedin_scraper import LinkedInScraper
import csv
import os

def main():
    # Path to merk companies CSV
    merk_csv_path = r'C:\Users\vaclavik\scrpr\merk_companies_20250910_153225.csv'
    
    # Check if file exists
    if not os.path.exists(merk_csv_path):
        print(f"ERROR: CSV file not found at {merk_csv_path}")
        print("Please make sure the merk_companies CSV file exists.")
        return
    
    # Initialize scraper
    print("=" * 60)
    print("LINKEDIN SCRAPER - MERK COMPANIES TEST")
    print("=" * 60)
    print(f"\nUsing companies from: {merk_csv_path}")
    
    scraper = LinkedInScraper()
    
    try:
        print("\nStarting LinkedIn scraping with companies from merk.cz...")
        print("-" * 60)
        
        # Process companies from merk CSV
        scraper.process_companies(merk_csv_path)
        
        # Save results with descriptive filename
        output_filename = 'merk_companies_linkedin_results.xlsx'
        scraper.save_results(output_filename)
        
        print("\n" + "=" * 60)
        print(f"SCRAPING COMPLETED!")
        print(f"Results saved to: {output_filename}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\nERROR: File not found - {e}")
        print("Please check that the CSV file path is correct.")
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