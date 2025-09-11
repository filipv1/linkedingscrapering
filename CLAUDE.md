# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of web scraping tools primarily focused on LinkedIn and CKAIT (Czech Chamber of Authorized Engineers and Technicians) data extraction. The project uses Selenium WebDriver for browser automation and includes various scraper implementations for different use cases.

## Core Architecture

### Main Scraper Classes

- **ProductionLinkedInScraper** (`production_scraper.py`): Production-ready LinkedIn scraper with comprehensive error handling, rate limiting, and logging
- **SmartLinkedInScraper** (`smart_scraper.py`): Enhanced LinkedIn scraper with anti-detection features
- **LinkedInScraper** (`linkedin_scraper.py`): Basic LinkedIn scraping functionality
- **CkaitPhoneExtractor** (`ckait_phone_extractor.py`): Parallel phone number extraction from CKAIT profiles
- **UltraPhoneExtractorExtended** (`ultra_phone_parallel_extended.py`): Advanced parallel extractor with enhanced field extraction capabilities

### Scraper Evolution Pattern

The codebase follows a progressive enhancement pattern:
- **Base scrapers** (simple, debug): Basic functionality for development and testing
- **Smart scrapers**: Enhanced anti-detection capabilities
- **Production scrapers**: Full error handling, logging, and conservative rate limiting
- **Ultra/Extended scrapers**: Advanced parallel processing with comprehensive data extraction

### Key Features

- **Anti-detection mechanisms**: All scrapers implement browser fingerprint masking, realistic user agents, and human-like behavior simulation
- **Rate limiting**: Production scrapers include conservative delays (20-30s between companies) to avoid detection
- **Parallel processing**: Phone extraction tools use ThreadPoolExecutor for concurrent processing (typically 3 workers)
- **Data export**: Results are saved to both Excel (.xlsx) and CSV formats with proper formatting
- **Logging**: Production scrapers include comprehensive logging to `scraper_production.log`
- **Thread safety**: Parallel scrapers use threading locks for safe result collection

## Dependencies

The project uses Python 3.13+ with the following key packages:
- `selenium==4.35.0` - Web browser automation
- `pandas==2.3.1` - Data manipulation and export
- `openpyxl==3.1.5` - Excel file handling

Install dependencies with:
```bash
pip install selenium pandas openpyxl
```

## Running the Scrapers

### Production LinkedIn Scraper
```bash
python production_scraper.py
```
- Runs in headless mode with conservative rate limiting
- Searches for "stavbyvedoucí" (construction managers) at specified companies
- Saves intermediate results every 10 companies
- Requires `firmy.csv` input file at `C:\Users\vaclavik\Downloads\firmy.csv`

### CKAIT Phone Extractors
```bash
# Standard parallel phone extractor
python ckait_phone_extractor.py

# Extended parallel extractor with additional fields
python ultra_phone_parallel_extended.py

# Simple single-threaded extractor
python ultra_simple_phone.py
```
- Parallel processing with configurable worker threads (typically 3)
- Extract phone numbers, addresses, and other contact information from CKAIT profiles
- Uses thread-safe result collection with progress tracking

### Development and Testing
```bash
# Quick testing with small datasets
python quick_test.py

# Test specific extraction functionality
python test_extended_extraction.py

# Debug specific features
python debug_*.py  # Various debug scripts for different components
```

### Manual Testing
Use `test_scraper.py` or `quick_test.py` for development and testing with smaller datasets.

## Data Flow

1. **Input**: CSV files with company names or member data
2. **Processing**: Selenium automation searches and extracts data
3. **Output**: Excel files with formatted results, CSV backups, and log files

## Common Patterns

- All scrapers use manual login prompts for session setup
- Conservative rate limiting is implemented to avoid detection
- Results include fallback entries ("nenalezeno") for failed searches
- Excel exports include clickable LinkedIn profile links
- Thread-safe operations for parallel scrapers

## File Naming Conventions

- `production_*.py` - Production-ready scrapers with full error handling
- `debug_*.py` - Development/debugging versions  
- `test_*.py` - Testing and validation scripts
- `ultra_*.py` - Advanced/enhanced scraper implementations
- `*_manual*.csv` - Manually curated datasets
- `*_parallel*.xlsx` - Results from parallel processing
- `*_extended*.py` - Enhanced extractors with additional field collection

## Development Workflow

### Testing Strategy
1. **Development**: Start with `debug_*.py` scripts for initial development and troubleshooting
2. **Validation**: Use `test_*.py` scripts to validate functionality with small datasets
3. **Enhancement**: Progress to `smart_*.py` or `ultra_*.py` for advanced features
4. **Production**: Deploy `production_*.py` for large-scale, reliable operations

### Data Processing Pipeline
1. **Input preparation**: CSV files with target URLs or company lists
2. **Extraction**: Run appropriate scraper based on data volume and requirements
3. **Output handling**: Results automatically saved to both CSV and Excel formats
4. **Quality assurance**: Check logs and fallback entries for processing issues

### Chrome Driver Management
All scrapers implement standardized Chrome setup with:
- Headless mode support for production environments
- Anti-detection headers and options
- WebDriver property masking
- Consistent user agent strings