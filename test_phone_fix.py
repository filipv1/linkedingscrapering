from ckait_phone_extractor import CkaitPhoneExtractor

def test_single_profile():
    """Test single profile to verify phone extraction works"""
    
    extractor = CkaitPhoneExtractor(headless=False, max_workers=1)
    
    # Test with the known working profile
    test_member = {
        'member_number': '0601040',
        'firstname': 'Tomáš',
        'surname': 'Purkrábek'
    }
    
    print("Testing phone extraction on single profile...")
    result = extractor.extract_phone_from_profile(test_member)
    
    if result:
        print(f"✅ Test successful!")
        print(f"Name: {result['name']}")
        print(f"Contact Phone: {result['contact_phone']}")
        print(f"Company Phone: {result['company_phone']}")
        
        if result['contact_phone'] or result['company_phone']:
            print("🎉 Phone extraction is working!")
        else:
            print("❌ Still not extracting phones")
    else:
        print("❌ Test failed")

if __name__ == "__main__":
    test_single_profile()