---
phase: 01
name: Core Geo-Scraper Engine
depends_on: []
autonomous: true
---

# Phase 1: Core Geo-Scraper Engine

**Goal:** Scraper correctly simulates a localized user and extracts ranks.
**Core Value:** Validated Geo-specific scraping.

## Execution Waves

### Wave 1: Foundation & Browser Control
**Focus:** Environment setup and basic browser persistence.

<task>
<id>1.1</id>
<title>Initialize Python Project Structure</title>
<description>
Set up a new Python project using Poetry.
- Initialize `pyproject.toml`.
- Add dependencies: `playwright`, `pytest`, `pytest-playwright`, `pytest-asyncio`.
- Install playwright browsers (`playwright install chromium`).
- Create `src/` and `tests/` directories.
</description>
<file_paths>
- pyproject.toml
- src/__init__.py
- tests/__init__.py
</file_paths>
<must_have>
- `poetry install` works without errors.
- `playwright` CLI is available.
</must_have>
</task>

<task>
<id>1.2</id>
<title>Implement BrowserManager with Persistence</title>
<description>
Create a `BrowserManager` class wrapping Playwright.
- Configure `launch_persistent_context` to save cookies/session to a local `user_data` folder.
- Enable `headless=False` (Headed mode) as per SCRAPE-05.
- Set distinct viewport and user-agent if necessary (start simple).
</description>
<file_paths>
- src/browser_manager.py
- tests/test_browser.py
</file_paths>
<must_have>
- Browser launches visibly.
- Closing and reopening restores cookies (verified manually or via simple test script).
</must_have>
</task>

### Wave 2: Location Injection
**Focus:** Manipulating Amazon's "Deliver to" settings.

<task>
<id>2.1</id>
<title>Implement LocationHandler</title>
<description>
Create `LocationHandler` class to manage Zip Code injection.
- Logic to click "Deliver to" widget.
- Logic to detect if Zip Code is already set.
- Logic to input new Zip Code and click "Apply/Done".
- Handle the page refresh that occurs after changing location.
</description>
<file_paths>
- src/location_handler.py
- tests/test_location.py
</file_paths>
<must_have>
- Script successfully changes Zip Code from default to a target (e.g., "10001").
</must_have>
</task>

<task>
<id>2.2</id>
<title>Implement Location Verification</title>
<description>
Add verification logic to `LocationHandler`.
- Check the DOM for the "Deliver to [Zip]" text after page reload.
- Raise `LocationVerificationError` if the set Zip doesn't match the target Zip (SCRAPE-02).
</description>
<file_paths>
- src/location_handler.py
</file_paths>
<must_have>
- Returns True if location matches.
- Raises error if location fails to update.
</must_have>
</task>

### Wave 3: Search & Extraction
**Focus:** Performing the search and finding the product.

<task>
<id>3.1</id>
<title>Implement Search & Extraction</title>
<description>
Create `AmazonScraper` class integrating Browser and Location.
- Method `search_keyword(keyword)`: Enters text in search bar, submits.
- Method `find_asin_rank(asin)`: Iterates through search results to find the ASIN. Returns rank (index + 1) and page number.
- Handle basic pagination (look at page 1 for now).
</description>
<file_paths>
- src/scraper.py
- tests/test_scraper.py
</file_paths>
<must_have>
- Can find a known product on the first page of results.
- Returns correct integer rank.
</must_have>
</task>

<task>
<id>3.2</id>
<title>Phase 1 Integration Verification</title>
<description>
Create a main script `main_phase1.py` that runs the full flow:
1. Launch Browser.
2. Set Zip Code (e.g., 10001).
3. Verify Location.
4. Search Keyword (e.g., "notebook").
5. Find ASIN (pick a real one from the page manually for testing or dynamic).
6. Print Result.
</description>
<file_paths>
- main_phase1.py
</file_paths>
<must_have>
- Script runs end-to-end without crashing.
- Output confirms correct location and rank.
</must_have>
</task>

## Verification Criteria
- [ ] Browser opens in Headed mode.
- [ ] Cookies persist between runs.
- [ ] Zip Code is correctly injected and verified in the DOM.
- [ ] Search yields results and specific ASIN rank is identified.
