# Amazon Ranking and Detail Page Scraper

Amazon browser automation toolkit for geo-specific ranking checks and product detail page extraction. It uses Playwright with a persistent browser profile so Amazon cookies, location settings, and manual captcha recovery can be reused between runs.

Developed by Consologist.com.

## What this project does

- Checks Amazon search rankings for one or more ASINs from a selected marketplace and postal code.
- Separates ranking into sequential, organic, and sponsored positions.
- Scrapes Amazon product detail pages with price, seller, brand, reviews, BSR, product information, bullets, delivery date, and images.
- Runs either from the desktop GUI or from command line scripts.
- Saves timestamped CSV files under `results/`.
- Supports optional webhook POST for ranking CLI results.

## Requirements

- Windows 10/11
- Python 3.11 or newer
- Poetry
- Playwright Chromium browser
- Internet access

Install dependencies:

```powershell
poetry install
poetry run playwright install chromium
```

## Quick start

Run the GUI:

```powershell
poetry run python main_ui.py
```

Run ranking scraper from CSV:

```powershell
poetry run python main_rank_cli.py --input scrapper_test_job.csv
```

Run detail page scraper for one ASIN:

```powershell
poetry run python main_detail_page.py --marketplace amazon.co.uk --zip-code "SW1A 1AA" --asin B0CQLWJ6X3
```

## Ranking scraper

The ranking scraper sets the delivery location, searches a keyword, and checks where target ASINs appear on page 1.

### Ranking input file

CSV or Excel files must contain:

```csv
Marketplace,Zip Code,ASIN,Keyword
amazon.com,10001,B08N5WRWNW,wireless mouse
amazon.co.uk,SW1A 1AA,"B092T8N7T3,B0CQLWJ6X3","velcro cable ties,cable organizer"
```

Column meanings:

- `Marketplace`: Amazon domain such as `amazon.com`, `amazon.co.uk`, `amazon.de`, `amazon.ca`.
- `Zip Code`: delivery zip/postal code used before scraping.
- `ASIN`: one ASIN or multiple ASINs separated by comma, space, tab, or newline.
- `Keyword`: one keyword or multiple keywords separated by comma or newline.

### Ranking CLI

Batch mode:

```powershell
poetry run python main_rank_cli.py --input jobs.csv
```

Single task mode:

```powershell
poetry run python main_rank_cli.py --marketplace amazon.com --zip-code 10001 --asin B08N5WRWNW --keyword "wireless mouse"
```

Useful options:

```powershell
--headless
--webhook-url "https://example.com/webhook"
--keyword-delay 1
--task-delay 2
--stop-on-error
--user-data-dir user_data
```

### Ranking output

Ranking results are saved as:

```text
results/rank_results_YYYYMMDD_HHMMSS.csv
```

Output columns:

```text
Timestamp
Marketplace
Zip Code
Keyword
ASIN
Sequential Rank
Organic Rank
Sponsored Rank
Is Sponsored
Found
Page
```

Rank types:

- `Sequential Rank`: position counting every visible product result.
- `Organic Rank`: position among non-sponsored products only.
- `Sponsored Rank`: position among sponsored products only.

## Detail page scraper

The detail page scraper opens a product detail page after setting marketplace and delivery location. It accepts either an ASIN or a full Amazon product URL.

### Detail page CLI

Single ASIN:

```powershell
poetry run python main_detail_page.py --marketplace amazon.co.uk --zip-code "SW1A 1AA" --asin B0CQLWJ6X3
```

Single URL:

```powershell
poetry run python main_detail_page.py --marketplace amazon.co.uk --zip-code "SW1A 1AA" --url "https://www.amazon.co.uk/dp/B0CQLWJ6X3"
```

Batch mode:

```powershell
poetry run python main_detail_page.py --input products.csv
```

### Detail page input file

CSV or Excel files must contain `Marketplace`, `Zip Code`, and either `ASIN` or `Product URL`.

```csv
Marketplace,Zip Code,ASIN
amazon.co.uk,SW1A 1AA,B0CQLWJ6X3
```

or:

```csv
Marketplace,Zip Code,Product URL
amazon.co.uk,SW1A 1AA,https://www.amazon.co.uk/dp/B0CQLWJ6X3
```

### Detail page output

Detail results are saved as:

```text
results/detail_page_results_YYYYMMDD_HHMMSS.csv
```

Output columns include:

```text
Marketplace
Zip Code
ASIN
Product URL
Title
Current Price
Seller Name
Brand Name
Rating
Number of Reviews
Primary BSR Rank
Primary BSR Category
All BSR Ranks
Availability
Delivery
Delivery Location
Dispatches From
Bullet Points
Attributes
Description
A Plus Description
Product Information
Reviews Summary
Rating Breakdown
Reviews
Breadcrumbs
Main Image
Image URLs
```

Structured fields are stored as JSON strings inside the CSV:

- `All BSR Ranks`
- `Bullet Points`
- `Attributes`
- `Product Information`
- `Rating Breakdown`
- `Reviews`
- `Breadcrumbs`
- `Image URLs`

Delivery behavior:

- The `Delivery` column stores only the earliest visible delivery date/promise from the page.
- Example: if Amazon shows standard delivery on Thursday and fastest delivery tomorrow, the scraper stores `Tomorrow, 9 June`.

## GUI application

The GUI is launched with:

```powershell
poetry run python main_ui.py
```

GUI features:

- Load ranking CSV/XLSX files.
- Start, pause, resume, and stop jobs.
- View real-time logs.
- Use headed browser mode for manual captcha solving.
- Configure scheduling and webhook settings.
- Save ranking CSV output automatically.

## Browser profile and captcha handling

The browser runs with a persistent profile by default:

```text
user_data/
```

This helps preserve cookies, region settings, and Amazon session state. If Amazon shows a captcha, solve it in the visible browser and rerun or resume the job depending on the entry point being used.

Headless mode is available, but headed mode is recommended when testing new marketplaces or when captchas are likely.

## Project structure

```text
src/browser_manager.py       Playwright persistent browser lifecycle
src/location_handler.py      Amazon postal-code modal handling and verification
src/scraper.py               Search ranking scraper logic
src/detail_scraper.py        Product detail page extraction logic
src/data_loader.py           CSV/XLSX job loading for ranking jobs
src/scraper_controller.py    GUI ranking orchestration
src/ui/                      PyQt6 GUI
main_ui.py                   GUI entry point
main_rank_cli.py             Command-line ranking scraper
main_detail_page.py          Command-line detail page scraper
main_phase1.py               Legacy integration test script
results/                     Generated CSV outputs
user_data/                   Persistent browser profile
```

## Troubleshooting

### Browser does not open

Install Chromium:

```powershell
poetry run playwright install chromium
```

### Location setting fails

Amazon frequently changes its location modal. The shared location handler tries multiple selectors and verifies the final postal code. If it fails repeatedly, manually set the location in the browser profile and rerun.

### Captcha detected

Use headed mode, solve the captcha manually in the browser, then rerun the job. Avoid high-frequency repeated scraping.

### Results show `N/A`

For ranking jobs, `N/A` means the target ASIN was not found on page 1 for that marketplace, postal code, and keyword.

### Detail page fields are blank

Amazon renders different page layouts by category and marketplace. The detail scraper uses multiple fallbacks, but some fields may not exist on every product page. A+ content is captured separately from the older product description block.

### Price appears in an unexpected currency

Amazon may use account, browser, or region currency preferences from the persistent profile. The scraper records what the page visibly shows.

## Responsible use

Use this tool responsibly and in accordance with Amazon's terms and applicable laws. Prefer low-frequency checks, headed mode for manual review, and your own products or authorized research workflows.
