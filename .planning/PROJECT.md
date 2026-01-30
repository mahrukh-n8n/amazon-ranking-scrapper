# Amazon Geo-Rank Scraper

## What This Is

A Python-based desktop GUI application that accurately checks Amazon product rankings by simulating specific geographic locations. It automates the browser to set delivery zip codes before scraping, ensuring rank data reflects what real customers see in those regions, while allowing manual user intervention for Captcha solving.

## Core Value

Accurate Geo-Rank extraction validation. The system must verify the Amazon delivery location is correctly set to the target Zip Code before recording any ranking data.

## Current State (v1.0 MVP)

**Shipped:** 2026-01-30
**Capabilities:**
- Playwright-based scraper with US/UK zip code injection
- PyQt6 Desktop GUI with real-time logs and job control
- Auto-pause on Captcha detection with sound alerts
- CSV export with Sequential, Organic, and Sponsored ranks
- Daily/Weekly scheduling and system tray background mode
- Settings persistence and session cookie reuse

## Next Milestone Goals

**v2.0 Focus:** Enhanced Data & Visualization
- Screenshot evidence capture for rank verification
- Historical rank tracking dashboard
- Proxy rotation integration
- Expanded marketplace support (DE, FR, ES, IT)

## Requirements


### Validated

(None yet — ship to validate)

### Active

- [ ] **Input Management**: User can load job files (Excel/CSV) defining Marketplace, Zip Code, ASINs, and Keywords.
- [ ] **Geo-Location**: Automation to interact with Amazon's "Deliver to" widget and successfully change the session zip code.
- [ ] **Scraping Engine**: Search for keywords and identify the rank position of specific ASINs on the results page.
- [ ] **Human-in-the-Loop**: Detect Captchas or blocking pages and pause automation to allow manual user resolution.
- [ ] **GUI**: Desktop interface (PyQt/Tkinter) to load files, view progress, and handle manual interventions.
- [ ] **Export**: Save results (Rank Position, Page Number, etc.) to CSV/Excel.

### Out of Scope

- **Headless Execution**: The tool is designed for "Desktop App" usage with visible browser interaction.
- **Automated Captcha Solving**: Explicitly excluded in favor of manual user control to reduce costs and complexity.
- **Server/Cloud Deployment**: Designed for local execution.

## Context

- **Migration**: Porting logic from an existing Browser Automation Studio (BAS) XML script.
- **Anti-Bot**: Amazon aggressively defends against scrapers. The strategy is "browser stealth" + "human backup" rather than API/Proxy rotation heavy approaches.
- **Environment**: Windows Desktop (implied by "C:\Users...").

## Constraints

- **Type**: Tech Stack — Python (Selenium/Playwright + PyQt/Tkinter).
- **Type**: Performance — Speed is secondary to accuracy and evasion (must act like a human).
- **Type**: Human Interaction — Must not crash on Captcha; must wait for user.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **Manual Captcha Handling** | Simplifies dev and avoids cat-and-mouse with solvers; user explicitly requested control. | — Pending |
| **GUI vs CLI** | User requested "Desktop App style" for ease of use. | — Pending |
| **Python Port** | User requested migration from proprietary BAS tool to standard Python stack. | — Pending |

---
*Last updated: 2026-01-30 after initialization*
