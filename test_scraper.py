from linkedin_scraper import LinkedInScraper
import csv

def main():
    # Initialize scraper
    scraper = LinkedInScraper()
    
    try:
        print("Starting production scrape with all companies...")
        
        # Process ALL companies from the original CSV
        scraper.process_companies(r'C:\Users\vaclavik\Downloads\firmy.csv')
        
        # Save results
        scraper.save_results('test_results.xlsx')
        
        print("\nTest completed! Check test_results.xlsx for results")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()