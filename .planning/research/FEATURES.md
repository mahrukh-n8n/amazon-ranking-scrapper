# Feature Landscape

**Domain:** Amazon Ranking Scraper Desktop App
**Researched:** 2026-01-30
**Confidence:** HIGH

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Geo-Location Configuration** | Core value prop. Users need to check ranks as if they are in NY, CA, or TX. | High | Requires robust automation to interact with Amazon's "Deliver to" modal and verify persistence. |
| **ASIN & Keyword Management** | Basic input requirement. "Check where ASIN X ranks for Keyword Y". | Low | CRUD interface for input data. |
| **Manual Captcha Handover** | Desktop apps are expected to handle what bots can't. If a robot dog appears, the app must pause and alert the user. | Medium | Requires UI state management (Pause -> Waiting for User -> Resume). |
| **Rank Reporting / Export** | Data is useless if locked in the app. Users need CSV/Excel for analysis. | Low | Standard file I/O. |
| **Browser Preview / Headed Mode** | Trust. Users want to *see* the bot working or verify the location themselves. | Low | Playwright `headless=False` makes this native. |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Visual Proof (Screenshots)** | "Trust but verify." Saves a screenshot of the search result page highlighting the product. | Medium | Playwright makes this easy; storage management is the complexity. |
| **Session Persistence** | Speed & Stealth. Reusing cookies means not having to set the Zip Code on every single run, reducing suspicion. | Medium | Cookie storage in SQLite/JSON and loading into BrowserContext. |
| **"Human" Behavior Modeling** | Anti-detection. Random mouse movements, scrolls, and delays to mimic a real shopper. | High | Custom logic on top of Playwright. |
| **Notifications/System Tray** | Convenience. "Scrape finished" alert allows user to work on other things. | Low | Native PyQt capability. |

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **High Concurrency (Multi-tab)** | Freezes desktop UI, flags IP addresses instantly on Amazon. | **Queue-based Serial Scraping** (1-2 concurrent contexts max). |
| **Automatic Captcha Solving (OCR/2Captcha)** | Reliability is low on Amazon's new challenges; adds maintenance overhead/cost. | **User Notification** (Play a sound, bring window to front). |
| **Full Amazon Account Login** | High risk of getting the user's actual Amazon account banned. | **Guest Mode** (Cookies only for location, no login). |
| **Cloud/Headless Defaults** | Almost guaranteed detection by Amazon's WAF. | **Headed (Visible) Browser** as default. |

## Feature Dependencies

```
[Configuration] -> [Browser Context Creation] -> [Zip Code Setting] -> [Search/Scrape]
       ^                                                 |
       |----------------(Cookies/Session)----------------|
```
*Zip Code Setting is the critical gatekeeper. Scrape must not proceed if Zip verification fails.*

## MVP Recommendation

For MVP, prioritize:
1. **Geo-Location Logic** (The hardest part, fail fast here).
2. **Single ASIN/Keyword Search** (End-to-end flow).
3. **Manual Captcha Pause** (The "Human in the loop" requirement).

Defer to post-MVP:
- **Bulk Import/Export**: Manual entry is fine for v0.1 testing.
- **Visual Proof**: nice to have, but text rank is sufficient for data validation.
- **Scheduling**: Manual start button is enough for now.

## Sources

- **Playwright Docs**: Capabilities for screenshots and context persistence.
- **Amazon Scraping Best Practices**: Community consensus on avoiding login and concurrency.
