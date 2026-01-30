# Amazon Geo-Rank Scraper

A Python desktop application that checks Amazon product rankings from specific geographic locations. It automates browser interaction to set delivery zip codes before scraping, ensuring rank data reflects what real customers see in those regions.

**Version:** 1.0.0
**Developed by:** [Consologist.com](https://consologist.com) - Amazon Services Agency

---

## Features

### Core Scraping
- **Geo-Location Simulation** - Set any US/UK zip/postal code to check rankings from that location
- **Multi-ASIN Support** - Check multiple product ASINs in a single job
- **Keyword Search** - Find where your products rank for specific search terms
- **Three Rank Types**:
  - **Sequential Rank** - Position counting all items (sponsored + organic)
  - **Organic Rank** - Position among non-sponsored products only
  - **Sponsored Rank** - Position among sponsored/ad products only
- **Sponsored Detection** - Identifies if your product appears as a paid ad
- **Session Persistence** - Reuses cookies to avoid repeated location setting

### User Interface
- **Desktop GUI** - Easy-to-use PyQt6 interface
- **Real-time Logging** - See exactly what the scraper is doing
- **Start/Pause/Stop Controls** - Full control over scraping jobs
- **Progress Tracking** - Visual feedback on job completion
- **Status Indicators** - Color-coded status (Idle, Running, Paused, Captcha)

### Captcha Handling
- **Auto-Detection** - Recognizes when Amazon shows a captcha
- **Sound Alert** - Plays Windows notification sound when human intervention needed
- **Window Focus** - Brings app to foreground and flashes taskbar
- **Pause & Resume** - Automatically pauses, waits for you to solve, then continues

### Scheduling & Automation
- **Scheduled Runs** - Set daily or weekly scraping schedules
- **System Tray** - Minimize to tray for background operation
- **Tray Notifications** - Get notified when scheduled jobs start/complete
- **Settings Persistence** - All preferences saved between sessions

### Data Export
- **CSV Export** - Automatic timestamped CSV files in `results/` folder
- **Webhook Integration** - Optional HTTP POST to external services (n8n, Zapier, etc.)
- **Desktop Notifications** - Alert when jobs complete

## Requirements

- Windows 10/11
- Python 3.11 or higher
- Internet connection

## Installation

### Quick Install (Recommended)

1. Double-click `install.bat`
2. Wait for installation to complete (downloads ~150MB for browser)
3. Double-click `run.bat` to start the application

### Manual Install

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python -

# Install dependencies
poetry install

# Install Playwright browsers
poetry run playwright install chromium

# Run the application
poetry run python main_ui.py
```

### First Run

On first run, the application will:
1. Open a Chromium browser window
2. Navigate to Amazon
3. You may need to accept cookies or dismiss popups manually the first time

## Usage

### 1. Prepare a Job File

Create a CSV or Excel file with the following columns:

| Marketplace | Zip Code | ASIN | Keyword |
|-------------|----------|------|---------|
| amazon.com | 10001 | B08N5WRWNW | wireless mouse |
| amazon.co.uk | SW1A 1AA | B092T8N7T3,B0CQLWJ6X3 | velcro cable ties,cable organizer |
| amazon.de | 10115 | B09XYZ1234 | kabellose maus,wireless maus |

**Column Details:**
- **Marketplace**: Amazon domain (`amazon.com`, `amazon.co.uk`, `amazon.de`, etc.)
- **Zip Code**: US zip code (10001) or UK/EU postal code (SW1A 1AA, 10115)
- **ASIN**: Single ASIN or comma-separated list for multiple products
- **Keyword**: Single keyword or comma-separated list for multiple keywords

**Multiple Values:**
- **ASINs**: Separate with commas, spaces, or newlines: `B08N5WRWNW,B09XYZ1234` or `B08N5WRWNW B09XYZ1234`
- **Keywords**: Separate with commas or newlines only (keywords can contain spaces): `wireless mouse,gaming mouse,bluetooth mouse`

Each keyword will be searched separately and all ASINs checked for each keyword.

See `test_job.csv` for an example.

### 2. Load and Run

1. Click **Load Job File** and select your CSV/Excel file
2. Verify the task count shows correctly
3. Click **Start** to begin scraping
4. Watch the real-time log for progress
5. If a captcha appears:
   - The app will pause and play a sound
   - Solve the captcha in the browser window
   - Click **Resume** to continue
6. Results are saved automatically to `results/` folder when complete

### 3. Configure Options

| Option | Description |
|--------|-------------|
| **Webhook URL** | URL to POST results as JSON (optional) |
| **Enable Webhook** | Toggle webhook integration on/off |
| **Enable Notifications** | Toggle desktop alerts on completion |
| **Minimize to Tray** | App stays in system tray when closed |
| **Headless Mode** | Run browser invisibly (faster, but can't solve captchas) |
| **Schedule Enabled** | Enable automatic scheduled runs |
| **Recurrence** | Daily or Weekly (Mondays) |
| **Time** | What time to run the scheduled job |

### Headless Mode

When enabled, the browser runs invisibly in the background. This is:
- **Faster** - No rendering overhead
- **Less resource intensive** - Uses less CPU/memory

However, headless mode has limitations:
- **Cannot solve captchas** - You won't see captchas when they appear
- **No visual verification** - You can't see what the scraper is doing
- **Higher detection risk** - Some anti-bot systems detect headless browsers

**Recommendation:** Use headed mode (default) for interactive sessions and when captchas are expected. Use headless mode only for scheduled background runs on sites with low captcha frequency.

## Output

Results are saved as timestamped CSV files in the `results/` folder.

### Output Columns

| Column | Description |
|--------|-------------|
| Timestamp | When the check was performed |
| Marketplace | Amazon domain used |
| Zip Code | Location simulated |
| Keyword | Search term |
| ASIN | Product identifier |
| Found | Whether product was found (True/False) |
| Sequential Rank | Position counting ALL items (sponsored + organic) |
| Organic Rank | Position among non-sponsored products only |
| Sponsored Rank | Position among sponsored/ad products only |
| Is Sponsored | Whether the product appeared as a sponsored listing |
| Page | Which page the product was found on |

### Understanding Rank Types

**Sequential Rank**
Counts every product on the page in order (1, 2, 3...) regardless of whether it's sponsored or organic. This is exactly what the customer sees when they search.

**Organic Rank**
Only counts non-sponsored products. If your product is organic and shows as Sequential #5 but there were 2 sponsored products above it, your Organic Rank would be #3. Shows "N/A" for sponsored products.

**Sponsored Rank**
Only counts sponsored/ad products. If your product is a sponsored ad at Sequential #2, and there was 1 sponsored product before it, your Sponsored Rank would be #2. Shows "N/A" for organic products.

**Is Sponsored**
Boolean (True/False) indicating if your product appeared as a paid advertisement.

### Example Output

```csv
Timestamp,Marketplace,Zip Code,Keyword,ASIN,Sequential Rank,Organic Rank,Sponsored Rank,Is Sponsored,Found,Page
2026-01-30 14:30:00,amazon.com,10001,wireless mouse,B08N5WRWNW,7,5,N/A,False,True,1
2026-01-30 14:30:00,amazon.com,10001,wireless mouse,B09XYZ1234,3,N/A,2,True,True,1
```

## Webhook Integration

When enabled, results are POSTed as JSON to your webhook URL:

```json
{
  "timestamp": "2026-01-30T14:30:00",
  "total_results": 2,
  "results": [
    {
      "Timestamp": "2026-01-30 14:30:00",
      "Marketplace": "amazon.com",
      "Zip Code": "10001",
      "Keyword": "wireless mouse",
      "ASIN": "B08N5WRWNW",
      "Sequential Rank": 7,
      "Organic Rank": 5,
      "Sponsored Rank": "N/A",
      "Is Sponsored": false,
      "Found": true,
      "Page": 1
    }
  ]
}
```

Compatible with n8n, Zapier, Make, or any service that accepts HTTP POST.

## Project Structure

```
amz-geo-rank-scraper/
├── src/
│   ├── browser_manager.py    # Playwright browser lifecycle & persistence
│   ├── location_handler.py   # Zip code injection & verification
│   ├── scraper.py            # Search & rank extraction (3 rank types)
│   ├── scraper_controller.py # Job orchestration & scheduling
│   ├── data_loader.py        # CSV/Excel parsing
│   ├── notification_manager.py # Sound alerts & notifications
│   ├── exceptions.py         # Custom exceptions
│   └── ui/
│       ├── main_window.py    # PyQt6 main window
│       └── log_handler.py    # Log display handler
├── results/                  # Output CSV files (auto-created)
├── user_data/                # Browser session data/cookies (auto-created)
├── main_ui.py                # Application entry point
├── install.bat               # One-click installer
├── run.bat                   # Quick launcher
├── pyproject.toml            # Dependencies
├── settings.json             # User preferences (auto-created, gitignored)
├── SELECTORS.md              # Amazon CSS selectors reference
├── LICENSE                   # Proprietary license
└── README.md                 # This file
```

## Troubleshooting

### Application won't start

**"No running event loop" error**
This was fixed in version 1.0.0. Make sure you have the latest code.

**"Module not found" error**
Run `poetry install` to ensure all dependencies are installed.

**Browser doesn't open**
Run `poetry run playwright install chromium` to install the browser.

### Captcha appears frequently

Amazon may be detecting automation. Try:
- Waiting longer between runs (use scheduling for daily checks)
- Running fewer ASINs per job
- Solving captchas promptly when they appear
- Using the browser normally for a few minutes before starting jobs

### Location not setting correctly

Amazon A/B tests different UI layouts. If location setting fails:
1. The app will retry automatically (up to 5 attempts)
2. You can manually set the location in the browser window
3. The app will detect your manual change and continue

### Page refreshes cause errors

Amazon sometimes delays page refreshes after location changes. Version 1.0.0 includes improved handling for this. If issues persist:
1. Let the app retry the task
2. If it keeps failing, pause and manually verify the location is set

### Results show "N/A" for all ranks

The product was not found on page 1 of search results. The app currently only checks the first page.

### All products showing as Sponsored (incorrect)

If organic products are incorrectly detected as sponsored, Amazon may have changed their HTML. See "Updating Amazon Selectors" below.

## Updating Amazon Selectors

Amazon frequently changes their website HTML structure. When this happens, the scraper may fail to:
- Set the delivery location
- Detect sponsored vs organic products
- Find search results

### How to Update Selectors

**Step 1: Identify the Problem**
- Check the log for errors like "selector not found" or "timeout"
- Note which action is failing (location, search, sponsored detection)

**Step 2: Find the New Selector**

1. Open Amazon in Chrome or Edge
2. Navigate to the page with the element (search results, location modal, etc.)
3. Press `F12` to open Developer Tools
4. Click the "Select element" tool (arrow icon) or press `Ctrl+Shift+C`
5. Click on the element you need to interact with
6. In the Elements panel, examine the highlighted HTML

**Step 3: Choose a Stable Selector**

Best to worst (in order of stability):
1. **IDs** - `#nav-global-location-popover-link` (most stable)
2. **Data attributes** - `[data-component-type="s-search-result"]` (fairly stable)
3. **Specific classes** - `.puis-sponsored-label-text` (moderately stable)
4. **Nested selectors** - `div.a-section span.a-text` (least stable)

**Step 4: Test the Selector**

In the browser's Developer Tools Console, type:
```javascript
document.querySelector('YOUR_SELECTOR')
```
If it returns the element, the selector works. If it returns `null`, try a different selector.

**Step 5: Update the Code**

| File | What It Controls |
|------|------------------|
| `src/location_handler.py` | Location modal, zip code input, verification |
| `src/scraper.py` | Search box, search results, sponsored detection |

### Selector Reference

See `SELECTORS.md` for a complete list of all selectors used and their locations.

**Key selectors to check:**

| Selector | Purpose | File |
|----------|---------|------|
| `#glow-ingress-line2` | Current location display | location_handler.py |
| `#nav-global-location-popover-link` | Location button | location_handler.py |
| `#GLUXZipUpdateInput` | Zip code input | location_handler.py |
| `#twotabsearchtextbox` | Search box | scraper.py |
| `div[data-component-type="s-search-result"]` | Search results | scraper.py |
| `.puis-sponsored-label-text` | Sponsored label | scraper.py |

### Sponsored Detection

The sponsored detection checks for:
1. **CSS selectors** - `.puis-sponsored-label-text`, `.s-sponsored-label-info-icon`
2. **Data attributes** - `data-asin-ad-id`, `data-ad-type`
3. **Text content** - "Sponsored", "Gesponsert" (German), "Sponsorisé" (French)

If sponsored detection is wrong, inspect a sponsored product's label to find the new CSS class.

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Core language |
| Playwright | Browser automation |
| PyQt6 | Desktop GUI framework |
| qasync | Async/Qt event loop integration |
| APScheduler | Job scheduling |
| pandas | Data handling & CSV export |
| httpx | Async HTTP client for webhooks |
| openpyxl | Excel file support |

## Changelog

### Version 1.0.0
- Initial release
- Geo-location simulation for US/UK postal codes
- Three rank types: Sequential, Organic, Sponsored
- Sponsored product detection
- PyQt6 desktop interface
- Captcha detection with sound alerts
- Daily/Weekly scheduling
- System tray integration
- Settings persistence
- CSV export with timestamps
- Optional webhook integration
- Robust page refresh handling

## License

Copyright (c) 2026 Consologist.com - Amazon Services Agency. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use of this software is strictly prohibited.

For licensing inquiries, contact: [consologist.com](https://consologist.com)

## Disclaimer

This tool is for personal use to check your own product rankings. Use responsibly and in accordance with Amazon's Terms of Service. The authors are not responsible for any account restrictions or bans resulting from misuse.

---

**Amazon Geo-Rank Scraper** - Developed by [Consologist.com](https://consologist.com)

*Your trusted Amazon Services Agency*
