# Project State

**Project:** Amazon Geo-Rank Scraper
**Core Value:** Accurate Geo-Rank extraction validation.
**Current Focus:** Phase 1 - Core Geo-Scraper Engine

## Current Position

| Phase | Goal | Status |
|-------|------|--------|
| **1 - Core Geo-Scraper Engine** | **Scraper correctly simulates a localized user and extracts ranks.** | **Planned** |
| 2 - Interactive Desktop UI | User can manage the scraping session without touching code. | Pending |
| 3 - Output & Integration | Usable data is delivered at the end of the session. | Pending |

## Phase 1 Plan (Draft)

**Goal:** Scraper correctly simulates a localized user and extracts ranks.

- [ ] Initialize Python project structure (Poetry/Pipenv)
- [ ] Implement Playwright "Headed" browser setup (SCRAPE-05)
- [ ] Implement Cookie persistence logic (SCRAPE-04)
- [ ] Implement Zip Code injection logic (SCRAPE-01)
- [ ] Implement DOM verification for location (SCRAPE-02)
- [ ] Implement Keyword search and ASIN rank parsing

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Location Success Rate | 100% | - |
| Captcha Detection | 100% | - |

## Context & Decisions

- **Decision:** Using Playwright + PyQt6 + qasync for the stack.
- **Constraint:** Must use visible browser (Headed mode) to avoid detection and allow manual interaction.
- **Context:** Migrating logic from BAS (Browser Automation Studio).

## Session Continuity

**Last Action:** Roadmap creation.
**Next Step:** Initialize Phase 1 execution.
