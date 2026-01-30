# Project Roadmap

**Project:** Amazon Geo-Rank Scraper
**Core Value:** Accurate Geo-Rank extraction validation (Zip Code persistence).
**Status:** Active
**Depth:** Quick (3 Phases)

## Overview

This roadmap delivers a Python-based desktop application for checking Amazon product rankings from specific geographic locations. The project moves from the core scraping engine (Phase 1) to the interactive GUI (Phase 2), and finally to data export and integration features (Phase 3).

## Phases

### Phase 1: Core Geo-Scraper Engine
**Goal:** Scraper correctly simulates a localized user and extracts ranks.
**Dependencies:** None
**Plans:** 1 plan

**Requirements:**
- **SCRAPE-01**: System can successfully set Amazon Delivery Zip Code via UI interaction.
- **SCRAPE-02**: System verifies "Deliver to" location matches target Zip Code before scraping.
- **SCRAPE-04**: System persists session cookies to reuse location settings across runs.
- **SCRAPE-05**: System runs in "Headed" mode (visible browser) by default.

**Success Criteria:**
1. Browser session opens with persisted cookies (if available).
2. "Deliver to" location visibly updates to target Zip Code.
3. Script aborts/retries if location verification fails (preventing bad data).
4. Correct rank position is identified for a known ASIN/Keyword pair.

Plans:
- [x] 01-01-PLAN.md - Core scraper engine with browser, location, and search

### Phase 2: Interactive Desktop UI
**Goal:** User can manage the scraping session without touching code.
**Dependencies:** Phase 1
**Plans:** 2 plans

**Requirements:**
- **UI-01**: User can Start, Pause, and Stop the scraping job.
- **UI-02**: User sees real-time activity log (e.g., "Setting Zip to 10001...", "Searching 'shoes'...").
- **SCRAPE-03**: System pauses and alerts user (sound/focus) when Captcha is detected.
- **DATA-01**: User can load job files (Excel/CSV) with columns: Marketplace, Zip Code, ASINs, Keywords. *(Completed in Phase 1 prep - DataLoader exists)*

**Success Criteria:**
1. User can launch the application window.
2. User can load a job file (CSV/Excel) and see loaded task count.
3. User can start the job and see real-time log updates in the window.
4. App automatically pauses and requests attention when a Captcha appears.
5. User can resume the job after solving the Captcha manually.

Plans:
- [ ] 02-01-PLAN.md - Controller enhancements (pause/resume + captcha alerting + progress signals)
- [ ] 02-02-PLAN.md - UI integration (buttons, progress, wire everything)

### Phase 3: Output & Integration
**Goal:** Usable data is delivered at the end of the session.
**Dependencies:** Phase 2

**Requirements:**
- **DATA-02**: System exports results (Rank, Page, ASIN, Keyword, Date) to CSV/Excel.
- **DATA-03**: (Optional) System can push results via HTTP POST to a webhook URL (e.g., n8n).
- **UI-03**: System displays desktop notification when job is complete.

**Success Criteria:**
1. Results file (CSV/Excel) is saved to disk upon completion.
2. Desktop notification triggers when all tasks are finished.
3. Results include verified Rank, Page, and Timestamp.
4. (If configured) JSON payload is received by the test webhook endpoint.

Plans:
- [ ] TBD (created by /gsd:plan-phase)

## Progress

| Phase | Status | Completion |
|-------|--------|------------|
| 1 - Core Geo-Scraper Engine | Complete | 100% |
| 2 - Interactive Desktop UI | **Planned** | 0% |
| 3 - Output & Integration | Pending | 0% |
