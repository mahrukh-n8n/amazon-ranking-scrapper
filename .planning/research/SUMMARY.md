# Project Research Summary

**Project:** Amazon Ranking Scraper Desktop App
**Domain:** Desktop Automation / Web Scraping
**Researched:** 2026-01-30
**Confidence:** HIGH

## Executive Summary

The Amazon Ranking Scraper is a desktop automation tool designed to check product search rankings across different geographical locations. Experts build this type of tool using robust browser automation (not simple HTTP requests) to handle dynamic JavaScript rendering and strict anti-bot measures. The core value proposition relies on accurately simulating a user in a specific zip code (e.g., seeing New York results while in Texas).

The recommended approach utilizes **Python 3.12** with **Playwright** for automation and **PyQt6** for the graphical user interface. Crucially, the architecture must use **qasync** to bridge the blocking GUI event loop with Playwright's asynchronous nature, preventing "application freeze" during scraping operations. The default mode should be "headed" (visible browser) to minimize detection and allow manual user intervention for Captchas.

Key risks center on Amazon's aggressive WAF (Web Application Firewall) and location resetting behavior. Research indicates that headless browsers are easily detected, and Amazon often defaults delivery location to IP address rather than cookies. Mitigation requires a "human-in-the-loop" design for Captchas and strict DOM verification steps to ensure the delivery location is correctly set before any ranking data is parsed.

## Key Findings

### Recommended Stack

**Core technologies:**
- **Python 3.12+**: Runtime environment offering performance improvements for async operations.
- **Playwright (1.57+)**: Browser automation engine chosen for its self-contained binaries, robust selector engine, and async support (superior to Selenium for this use case).
- **PyQt6 (6.10+)**: Industry-standard GUI framework offering rich widgets and threading capabilities.
- **SQLite**: Serverless local database for storing rank history and configuration without user setup.
- **qasync**: Critical library to run the PyQt event loop as the asyncio event loop, enabling native `await` in UI handlers.

### Expected Features

**Must have (table stakes):**
- **Geo-Location Configuration**: Ability to set and verify "Deliver to" zip codes (critical value prop).
- **ASIN & Keyword Management**: CRUD interface for inputs.
- **Manual Captcha Handover**: Pause automation and alert user when robot checks appear.
- **Rank Reporting**: Export results to CSV/Excel.
- **Headed Mode**: Visible browser for trust and debugging.

**Should have (competitive):**
- **Visual Proof**: Screenshots of the search result page highlighting the found product.
- **Session Persistence**: Reusing cookies to minimize setup time per run.

**Defer (v2+):**
- **Bulk Import/Export**: Manual entry sufficient for MVP.
- **Scheduling**: Manual start is acceptable for v1.
- **Full Amazon Login**: High risk of account bans, avoid for now.

### Architecture Approach

The architecture follows a **Controller-View-Engine** pattern integrated via `qasync`.

**Major components:**
- **Main Window (View)**: Renders UI and displays status; communicates via signals.
- **Scraper Controller**: Manages job queues and state (Running, Paused, Error); orchestrates the engine.
- **Scraper Engine (Playwright)**: Handles browser context, zip code injection, navigation, and DOM parsing.
- **Storage Layer (SQLite)**: Persists jobs, settings, and results.

### Critical Pitfalls

1. **The "Delivery Location" Reset**: Amazon ignores zip cookies if they conflict with IP or session logic. *Avoidance:* Implement strict DOM verification ("Deliver to X") before every scrape.
2. **PyInstaller + Playwright Paths**: Compiled EXEs fail to find browser binaries. *Avoidance:* Explicitly bundle browsers and set `PLAYWRIGHT_BROWSERS_PATH` in the build spec.
3. **Headless Detection**: Amazon blocks headless Chrome aggressively. *Avoidance:* Default to `headless=False` (visible browser).

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Scraper Logic (The Engine)
**Rationale:** The ability to reliably set location and parse ranks is the highest risk. If this fails, the UI doesn't matter.
**Delivers:** A headless/CLI script that takes ASIN/Zip, sets location, verifies it, and returns rank.
**Addresses:** Geo-Location Configuration, Search/Scrape.
**Avoids:** The "Delivery Location" Reset.

### Phase 2: UI Skeleton & Async Integration
**Rationale:** We need the GUI container to run the engine, but correctly integrated so it doesn't freeze.
**Delivers:** PyQt6 application shell with `qasync` loop, basic input forms, and the ability to run the Phase 1 engine without blocking the UI.
**Uses:** PyQt6, qasync.
**Implements:** Scraper Controller pattern.

### Phase 3: State Management & Persistence
**Rationale:** Now that we can scrape and see it, we need to save the data and handle edge cases like Captchas.
**Delivers:** SQLite integration, result grids, "Stop/Pause" functionality, and Manual Captcha Handover flows.
**Addresses:** Manual Captcha Handover, Rank Reporting.
**Avoids:** UI Freezing (by finalizing threaded/async logic).

### Phase 4: Packaging & Distribution
**Rationale:** Converting a Python/Playwright app to an EXE is complex and should be validated before feature creep.
**Delivers:** `setup.py` / PyInstaller spec, functioning .exe installer.
**Avoids:** PyInstaller + Playwright Bloat & Paths.

### Phase Ordering Rationale
- **Logic First:** The location-setting logic is fragile and Amazon changes it often. It needs the most testing time.
- **Async Foundation:** Integrating asyncio with Qt is structurally invasive; better to do it early than refactor later.
- **Packaging Last:** While critical, it depends on the file structure being relatively stable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (Packaging):** Specific PyInstaller hooks for Playwright 1.57+ might need fresh testing.

Phases with standard patterns (skip research-phase):
- **Phase 2 (UI):** `qasync` + PyQt6 is a well-documented pattern.
- **Phase 3 (Persistence):** SQLite + SQLAlchemy is standard.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Validated versions and libraries (Playwright, PyQt6, qasync). |
| Features | HIGH | Clear distinction between table stakes and anti-features. |
| Architecture | HIGH | `qasync` solution specifically addresses the main technical hurdle. |
| Pitfalls | HIGH | Well-documented issues in the scraping community. |

**Overall confidence:** HIGH

### Gaps to Address

- **Amazon's specific DOM for "Deliver To"**: The specific selector for the location verification text might vary by region or A/B test. *Handling:* Build robust fallback selectors during Phase 1.
- **Captcha Types**: Uncertainty on whether Amazon uses simple image captchas or "Arkose Labs" puzzles. *Handling:* The "Manual Handover" feature covers both cases generically.

## Sources

### Primary (HIGH confidence)
- **PyPI / Official Docs**: Playwright 1.57.0, PyQt 6.10.2.
- **qasync Documentation**: Verified integration pattern for asyncio/Qt.

### Secondary (MEDIUM confidence)
- **Scraping Communities**: Consensus on "Headless" detection and "Delivery Location" resetting.

### Tertiary (LOW confidence)
- **browser-forge**: Emerging tool, reliability long-term is less proven than the core stack.

---
*Research completed: 2026-01-30*
*Ready for roadmap: yes*
