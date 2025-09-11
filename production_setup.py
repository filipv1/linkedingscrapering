from production_scraper import ProductionLinkedInScraper

def setup_session():
    """Setup session with manual login, then test with few companies"""
    print("=== PRODUCTION SETUP & TEST ===")
    print("This will open browser for manual login, then test with 3 companies")
    
    # Non-headless for login
    scraper = ProductionLinkedInScraper(headless=False, conservative_mode=True)
    
    try:
        # Test with 3 companies
        test_companies = [
            "Chládek & Tintěra, a.s.",
            "Metrostav a.s.", 
            "STRABAG a.s."
        ]
        
        print(f"\nTesting with {len(test_companies)} companies...")
        
        for i, company in enumerate(test_companies, 1):
            print(f"\n--- Test {i}/{len(test_companies)}: {company} ---")
            
            company_url, actual_name = scraper.search_company(company)
            
            if company_url and actual_name:
                scraper.get_people_from_company(company_url, actual_name)
            else:
                scraper.results.append({
                    'company': company,
                    'name': 'nenalezeno', 
                    'position': 'nenalezeno',
                    'linkedin_url': 'nenalezeno'
                })
                
            # Rate limit between test companies
            scraper.production_rate_limit(15, 20)
            
        # Save test results
        scraper.save_results('production_test_results.xlsx')
        
        print("\n✅ PRODUCTION TEST COMPLETED")
        print("If results look good, you can run full production with:")
        print("python production_scraper.py")
        
    except Exception as e:
        print(f"Setup/test error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    setup_session()