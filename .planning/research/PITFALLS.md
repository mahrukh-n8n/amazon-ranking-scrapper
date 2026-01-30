# Domain Pitfalls

**Domain:** Amazon Ranking Scraper Desktop App
**Researched:** 2026-01-30
**Confidence:** HIGH

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: The "Delivery Location" Reset
**What goes wrong:** Amazon frequently ignores the requested zip code or resets it to the IP-based location during navigation, especially if the session looks suspicious.
**Why it happens:** Amazon prioritizes "real" user experience (IP geo-location) over cookie values if there's a discrepancy or if the `session-id` cookie expires.
**Consequences:** You scrape data for "New York" while Amazon is showing you rankings for "Texas". Data is invalid.
**Prevention:**
1.  **Double Verification:** Read the "Deliver to" element *after* every search query, not just at session start.
2.  **Cookie Persistence:** Capture and freeze the `session-id`, `session-id-time`, and `ubid-main` cookies after a successful zip change. Reuse them.

### Pitfall 2: PyInstaller + Playwright Bloat & Paths
**What goes wrong:** The compiled `.exe` fails to run because it can't find the browser binaries, or the installer is 500MB+.
**Why it happens:** Playwright stores browsers in a global OS folder by default, which PyInstaller doesn't capture.
**Prevention:**
1.  Set `PLAYWRIGHT_BROWSERS_PATH` environment variable to a local folder (e.g., `./browsers`) during development and build.
2.  Include that folder in PyInstaller's `datas`.
3.  Accept that the installer will be large; do not try to download browsers on the fly (fragile for end-users).

### Pitfall 3: The "Headless" Trap
**What goes wrong:** Developer builds and tests in `headless=True` (background). It works. Users run it, and immediately get blocked or see dog pages.
**Why it happens:** Amazon has highly sophisticated fingerprinting for headless Chrome (lack of GPU, specific navigator properties).
**Prevention:** default to `headless=False` (Headed mode). It consumes more RAM but is 100x safer for "simulating a human".

## Moderate Pitfalls

### Pitfall 1: CSS Selector Fragility
**What goes wrong:** Scraper breaks when Amazon changes a class name (e.g., from `.s-result-item` to `.puis-card-container`).
**Prevention:** Use **Playwright's "User-Visible" Locators** (e.g., `get_by_role`, `get_by_text`) or stable ID prefixes rather than long CSS chains. Use `aria-label` attributes which are often essential for accessibility and thus more stable.

### Pitfall 2: UI Freezing
**What goes wrong:** The "Stop/Pause" button doesn't work while the scraper is running.
**Prevention:** As detailed in Architecture, strictly use `qasync` or proper threading. Never run blocking scraper code in the main UI thread.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **Core Scraping Logic** | Focusing on parsing before location setting works. | **Milestone 1 must be "Location Reliability"**. If you can't set the zip code 100% of the time, the parser is useless. |
| **Packaging/Distribution** | Waiting until the end to test PyInstaller. | **Build a "Hello World" EXE immediately** that just opens a browser. Debugging Playwright packaging takes time. |

## Sources

- **GitHub Issues (pyinstaller/pyinstaller, microsoft/playwright-python)**: Documented struggles with bundling.
- **Scraping Communities**: Consensus on Amazon's headless detection and location resetting behavior.
