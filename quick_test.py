from ckait_phone_simple import SimplePhoneExtractor

def quick_test():
    """Quick test with known working member"""
    
    extractor = SimplePhoneExtractor(headless=False, max_workers=1)
    
    # Test with member that worked in original test
    test_member = {
        'member_number': '0601040',  # This worked!
        'firstname': 'Tomáš',
        'surname': 'Purkrábek',
        'profile_url': 'https://www.ckait.cz/expert/form/0601040'
    }
    
    print("=== QUICK TEST WITH KNOWN WORKING MEMBER ===")
    result = extractor.extract_single_phone(test_member)
    
    if result:
        print(f"\n✅ Result:")
        print(f"Name: {result['name']}")
        print(f"Contact: {result['contact_phone']}")
        print(f"Company: {result['company_phone']}")
    
    # Also test first member from CSV
    print("\n=== TESTING FIRST MEMBER FROM CSV ===")
    csv_member = {
        'member_number': '698',  # First from your output
        'firstname': 'Marek', 
        'surname': 'Gasparovič',
        'profile_url': 'https://www.ckait.cz/expert/form/0000698'
    }
    
    result2 = extractor.extract_single_phone(csv_member)
    
    if result2:
        print(f"\n✅ CSV Member Result:")
        print(f"Name: {result2['name']}")  
        print(f"Contact: {result2['contact_phone']}")
        print(f"Company: {result2['company_phone']}")

if __name__ == "__main__":
    quick_test()