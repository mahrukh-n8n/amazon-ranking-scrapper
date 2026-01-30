# Phase 1: Core Geo-Scraper Engine - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend logic for browser automation, location injection, and data extraction.
This phase delivers the *engine* that runs the scrape. It takes inputs (Zip, ASIN, Keyword) and returns data.
It includes the browser automation (Playwright), session management, and parsing logic.
It does NOT include the interactive GUI (Phase 2) or final data export/integration (Phase 3), though it consumes CSV inputs.

</domain>

<decisions>
## Implementation Decisions

### Browser Behavior
- **Auto-close:** Browser closes immediately when the script finishes.
- **Window Position:** Remember and restore the last used window position/size.
- **User Interaction:** Block user interaction with the browser window while the script is running to prevent interference.
- **Headless Mode:** Default to "Headed" (visible) mode, but include a `--headless` flag for testing/background use.

### Retry & Failure Strategy
- **Zip Code Injection:** Retry 2 times if the popup/setting fails, then fail.
- **Captcha Handling:** Wait 5 minutes for the user to manually solve the Captcha. (Phase 1 has no UI alerts, just console/waiting).
- **Page Load Errors:** Retry the specific page/search if it fails (network error/timeout).
- **Error Reporting:** Output clean, human-readable error messages to the console (not full tracebacks unless in debug mode).

### Session Storage
- **Format:** JSON file.
- **Scope:** Per Zip Code. Switching zip codes switches the loaded session.
- **Staleness:** Auto-delete invalid/expired sessions and start fresh.
- **Location:** Store in a local `.sessions/` folder within the project directory.

### Inputs & Ranks
- **Input Source:** CSV file (columns likely: Zip, ASIN, Keyword).
- **Search Depth:** Page 1 only.
- **Identification:** Exact ASIN match only.
- **Ranking Logic:**
  - **Organic Rank:** Sequence ignoring sponsored results.
  - **Sponsored Rank:** Sequence ignoring organic results.
  - **Absolute Position:** Sequence counting everything (1, 2, 3...).
  - **Output:** Separate columns for each of the above.

### Claude's Discretion
- Exact CLI argument structure (though CSV input is fixed).
- Internal architecture of the scraper class (Playwright wrapper details).
- Logging format details (beyond "clean errors").

</decisions>

<specifics>
## Specific Ideas

### Robust Parsing & Selectors
- **Critical:** Amazon frequently changes HTML structure. The system must be designed to make selector updates easy.
- **Reference Pattern:** User provided a specific Python structure (`AmazonSelectors` class) using Regex and configurable classes for `SPONSORED_CLASSES`, `ORGANIC_CLASSES`, etc.
- **Implementation:** Adopt this pattern or a similar configuration-driven approach where selectors are isolated from logic.
- **Code Snippet provided:**
  ```python
  class AmazonSelectors:
      SPONSORED_CLASSES = ['AdHolder', 's-featured-result-item', 'puis-sponsored-label-text', 'AdGridSlot']
      ORGANIC_CLASSES = ['s-result-item', 'sg-col', 's-search-results']
      # ... (see chat history for full snippet)
  ```

</specifics>

<deferred>
## Deferred Ideas

- **Interactive GUI:** Managing sessions via UI buttons (Phase 2).
- **Data Export:** Saving final results to formatted Excel/CSV files (Phase 3 - Phase 1 just outputs raw data or simple logs).
- **Webhooks:** Sending data to n8n (Phase 3).

</deferred>

---

*Phase: 01-core-geo-scraper-engine*
*Context gathered: 2026-01-30*
