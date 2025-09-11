# LinkedIn & Business Data Scraper Suite

A comprehensive collection of web scraping tools for LinkedIn and Czech business databases, built with Selenium WebDriver for authorized testing and research purposes.

## ⚠️ Legal Notice

This tool is intended for:
- Authorized penetration testing
- Security research with proper permissions
- Personal research within terms of service
- Educational purposes

**Always comply with website terms of service and applicable laws. Use responsibly.**

## 🚀 Features

### LinkedIn Scraper
- **Resilient scraping** with automatic session recovery
- **Autosave functionality** to prevent data loss
- **Resume capability** after interruptions
- **Rate limiting** to avoid detection
- **Headless mode** support for automation

### CKAIT Scraper
- **Parallel processing** for efficiency
- **Phone number extraction** from profiles
- **Extended field extraction** (addresses, emails, etc.)
- **Thread-safe** result collection

### Merk.cz Scraper
- **Company data extraction**
- **Pagination support**
- **Anti-detection measures**
- **CSV export** functionality

## 📋 Prerequisites

- Python 3.9+
- Google Chrome browser
- ChromeDriver matching your Chrome version
- Valid login credentials for target platforms

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/filipv1/linkedingscrapering.git
cd linkedingscrapering
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download ChromeDriver:
   - Check Chrome version: `chrome://settings/help`
   - Download from: https://chromedriver.chromium.org/
   - Add to PATH or place in project directory

## 💻 Usage

### LinkedIn Scraper with Resilience

```bash
# Basic usage with 100 companies
python resilient_linkedin_fixed.py --max 100

# With autosave every 25 companies
python resilient_linkedin_fixed.py --max 200 --autosave 25

# Resume after interruption
python resilient_linkedin_fixed.py --resume

# Headless mode
python resilient_linkedin_fixed.py --headless --max 50
```

### Parameters:
- `--input` - Input CSV file path
- `--max` - Maximum number of companies to process
- `--autosave` - Autosave interval (default: 50)
- `--resume` - Resume from previous state
- `--headless` - Run without browser GUI

### CKAIT Phone Extractor

```bash
python ckait_phone_extractor.py
```

### Merk.cz Company Scraper

```bash
python merk_pentest_scraper.py
```

## 📁 Project Structure

```
linkedingscrapering/
├── resilient_linkedin_fixed.py    # Main LinkedIn scraper with resilience
├── linkedin_scraper.py            # Base LinkedIn scraper class
├── production_scraper.py          # Production LinkedIn scraper
├── ckait_phone_extractor.py       # CKAIT phone extraction
├── ultra_phone_parallel_extended.py # Extended CKAIT scraper
├── merk_pentest_scraper.py        # Merk.cz scraper
├── requirements.txt                # Python dependencies
├── setup_instructions.md           # Detailed setup guide
└── CLAUDE.md                      # Codebase documentation
```

## 📊 Output Files

- **LinkedIn**: `merk_linkedin_results_[timestamp].xlsx`
- **Checkpoints**: `checkpoint_[timestamp].xlsx`
- **State file**: `scraper_state.json` (for resume)
- **CKAIT**: `ckait_stavbyvedouci_phones.xlsx`
- **Merk**: `merk_companies_[timestamp].csv`

## 🔧 Configuration

### Input CSV Format
```csv
Název firmy
Company Name 1
Company Name 2
```

### Anti-Detection Features
- Random delays between requests
- User-agent rotation
- WebDriver property masking
- Human-like interaction patterns

## 🐛 Troubleshooting

### Common Issues:

1. **ChromeDriver version mismatch**
   - Ensure ChromeDriver matches Chrome version

2. **Session timeout**
   - Use `--resume` flag to continue
   - Adjust `--autosave` interval

3. **Rate limiting**
   - Increase delays in code
   - Use smaller batches with `--max`

4. **Memory issues**
   - Process smaller batches
   - Enable more frequent autosaves

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚖️ Disclaimer

This software is provided for educational and research purposes only. Users are responsible for complying with all applicable laws and website terms of service. The authors assume no liability for misuse of this software.

## 🙏 Acknowledgments

- Selenium WebDriver community
- Czech engineering community (CKAIT)
- Contributors and testers

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review setup_instructions.md for detailed setup help

---

**Remember**: Always use web scraping tools responsibly and ethically.