# Setup Instructions for Scraper Project

## Prerequisites
- Python 3.9+ (tested with 3.13)
- Google Chrome browser
- ChromeDriver matching your Chrome version

## Installation Steps

### 1. Clone/Copy the project
Copy all `.py` files to your working directory

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install ChromeDriver

#### Option A: Manual Installation
1. Check your Chrome version: chrome://settings/help
2. Download matching ChromeDriver from: https://chromedriver.chromium.org/
3. Extract and add to PATH or place in project directory

#### Option B: Automatic Installation (using webdriver-manager)
```bash
pip install webdriver-manager
```

Then modify scraper files to use:
```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
```

## Required Files

### For LinkedIn Scraping:
- `linkedin_scraper.py` - Base LinkedIn scraper
- `production_scraper.py` - Production version with headless support
- `resilient_linkedin_fixed.py` - Main resilient scraper with autosave

### For CKAIT Scraping:
- `ckait_phone_extractor.py` - Phone number extractor
- `ultra_phone_parallel_extended.py` - Extended parallel extractor

### For Merk.cz Testing:
- `merk_pentest_scraper.py` - Merk.cz company extractor

## Input Files Required

### LinkedIn Scraping:
Create a CSV file with company names in the first column:
```csv
Název firmy
Metrostav a.s.
SWIETELSKY stavební s.r.o.
```

Default location: `C:\Users\[username]\scrpr\merk_companies_*.csv`

### CKAIT Scraping:
CSV file with CKAIT member data and URLs

## Running the Scrapers

### LinkedIn Scraper with Resilience:
```bash
# Basic run with 100 companies
python resilient_linkedin_fixed.py --max 100

# With autosave every 25 companies
python resilient_linkedin_fixed.py --max 200 --autosave 25

# Resume after crash
python resilient_linkedin_fixed.py --resume

# Headless mode (if supported)
python resilient_linkedin_fixed.py --headless --max 50
```

### CKAIT Phone Extractor:
```bash
python ckait_phone_extractor.py
```

### Merk.cz Company Extractor:
```bash
python merk_pentest_scraper.py
```

## Troubleshooting

### ChromeDriver Issues:
- Error: "chromedriver executable needs to be in PATH"
  - Solution: Add ChromeDriver to system PATH or place in project directory

### Session Timeout:
- The scraper includes automatic session recovery
- Use `--resume` flag to continue from last checkpoint

### Memory Issues:
- Use smaller batches with `--max` parameter
- Enable autosave with smaller intervals

### LinkedIn Rate Limiting:
- The scraper includes built-in delays
- If blocked, wait 24 hours before resuming

## Output Files

### LinkedIn Scraper:
- `merk_linkedin_results_[timestamp].xlsx` - Final results
- `checkpoint_[timestamp].xlsx` - Autosave checkpoints
- `scraper_state.json` - Resume state file

### CKAIT Scraper:
- `ckait_stavbyvedouci_manual_phones_parallel.xlsx`
- CSV backup files

### Merk.cz Scraper:
- `merk_companies_[timestamp].csv`

## Important Notes

1. **LinkedIn Login**: You'll need to manually log in when prompted
2. **Rate Limiting**: Scrapers include delays to avoid detection
3. **Data Privacy**: Use responsibly and in compliance with terms of service
4. **Backup**: Autosave creates checkpoints to prevent data loss

## Support

For issues, check:
1. Chrome and ChromeDriver versions match
2. All required Python packages are installed
3. Input CSV files are properly formatted
4. Sufficient disk space for output files