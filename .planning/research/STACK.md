# Stack Research

**Domain:** Amazon Ranking Scraper Desktop App
**Researched:** 2026-01-30
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.12+ | Runtime Environment | Standard for scraping/automation. 3.12 offers performance improvements over older versions. |
| **Playwright** | 1.57.0+ | Browser Automation | Superior to Selenium for desktop apps due to self-contained browser binaries (easier distribution), better async support (keeps UI responsive), and robust selector engine. Handles "waiting" automatically, reducing flakiness. |
| **PyQt6** | 6.10.2+ | GUI Framework | Industry standard for professional Python desktop tools. Offers sophisticated threading (`QThread`) to keep the scraper from freezing the UI, and rich widgets for displaying ranking tables. |
| **SQLite** | 3.x | Local Database | Zero-configuration, serverless storage ideal for desktop apps. Stores rank history and settings without requiring user setup. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **browser-forge** | Latest | Fingerprint Management | Use to inject realistic headers and TLS fingerprints into Playwright to avoid immediate bot detection (better maintained than `playwright-stealth`). |
| **SQLAlchemy** | 2.0+ | ORM | Use for database interactions. Modern 2.0 style allows strict typing and cleaner data models for ranking results. |
| **Pydantic** | 2.x | Data Validation | Use for validating configuration (zip codes, ASINs) and parsing scraping results. |
| **Loguru** | 0.7+ | Logging | superior DX to standard `logging`; crucial for debugging scraper issues on user machines. |
| **Appdirs** | 1.4+ | OS Paths | Essential for correctly locating user data/config directories across Windows/macOS/Linux. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **PyInstaller** | Packaging | Standard for freezing Python apps. Has excellent hooks for PyQt6 and Playwright. |
| **Black/Ruff** | Linting/Formatting | Enforce code quality, especially for the complex logic of scraper state machines. |
| **Poetry** | Dependency Management | Better than pip/venv for reproducible builds and separating dev-only tools. |

## Installation

```bash
# Core & Supporting
pip install playwright PyQt6 browser-forge sqlalchemy pydantic loguru appdirs

# Install Playwright browsers (critical step)
playwright install chromium

# Dev dependencies
pip install -D pyinstaller black ruff
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **Playwright** | **Selenium + undetected-chromedriver** | Use if Playwright is consistently blocked by Amazon's WAF even with manual intervention. Selenium has a longer history of specific "anti-detect" patches, but is harder to bundle/distribute cleanly. |
| **PyQt6** | **Tkinter / CustomTkinter** | Use for extremely simple "script wrappers" with < 3 input fields. PyQt is overkill for a 1-button app, but required for a "Ranking Scraper" that likely needs data grids and tabs. |
| **SQLite** | **CSV / JSON Files** | Use for MVP if data persistence requirements are minimal. However, SQLite is safer against corruption if the app crashes during a scrape. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Selenium (Vanilla)** | Easily detected, slower, blocking I/O freezes GUIs without complex threading. | **Playwright** (Async) or **SeleniumBase** |
| **PySide6** | While similar to PyQt6, PyQt has a slightly larger community and clearer licensing for GPL apps (though check commercial requirements). | **PyQt6** |
| **Requests/BeautifulSoup** | Cannot execute JavaScript, handle location delivery cookies, or solve Captchas visually. | **Playwright** |
| **Pickle** | Security risk and brittle for long-term storage of user data. | **SQLite** or **JSON** |

## Stack Patterns by Variant

**If "Headless" Scraping is required (Background Mode):**
- Use `browser-forge` heavily to manage fingerprints.
- Because Amazon detects headless browsers aggressively (checking GPU, window size, user-agent).

**If "Interactive" Mode (User solves Captcha):**
- Use `headless=False` in Playwright.
- This is the primary requirement for this project to ensure Captcha survival.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| **PyQt6** | **PyInstaller** | Requires careful handling of hidden imports and asset paths in the spec file. |
| **Playwright** | **PyInstaller** | You must set `PLAYWRIGHT_BROWSERS_PATH=0` during build or handle browser binary paths explicitly in the frozen app. |

## Sources

- **PyQt6**: Verified version 6.10.2 on PyPI (Jan 2026).
- **Playwright**: Verified version 1.57.0 on PyPI (Dec 2025).
- **undetected-chromedriver**: Verified version 3.5.5 (Feb 2024) - noted as potential alternative but aging.
- **browser-forge**: Emerging standard for Playwright fingerprinting in 2025.

---
*Stack research for: Amazon Ranking Scraper Desktop App*
*Researched: 2026-01-30*
