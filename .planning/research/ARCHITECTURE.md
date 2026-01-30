# Architecture Patterns

**Domain:** Amazon Ranking Scraper Desktop App
**Researched:** 2026-01-30
**Confidence:** HIGH

## Recommended Architecture

**Pattern:** **PyQt + qasync (Asyncio Bridge)**

The fundamental architectural challenge is reconciling PyQt's blocking event loop (GUI) with Playwright's async event loop (Scraper). Standard threading (`QThread`) with asyncio is complex and error-prone. The `qasync` library allows running the PyQt event loop *as* the asyncio event loop, enabling native `async/await` in UI slots.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **Main Window (View)** | UI rendering, user input, status display. | **ViewModel / Controller** |
| **Scraper Controller** | Orchestrates the scraping job queue, manages state (Running, Paused, Error). | **Scraper Engine**, **Main Window** |
| **Scraper Engine (Playwright)** | Browsing logic, DOM interaction, Captcha detection. | **Amazon Website**, **Scraper Controller** |
| **Storage Layer (SQLite/ORM)** | Persistence of settings, jobs, and results. | **Scraper Controller**, **Main Window** |

### Data Flow

1.  **User** enters ASIN, Keyword, Zip in **UI**.
2.  **Controller** adds job to **SQLite** (status: pending).
3.  **Controller** picks up job, launches **Playwright Context**.
4.  **Engine** navigates to Amazon -> Checks Zip Cookie -> (If mismatch) Interactions to change Zip.
5.  **Engine** verifies "Deliver to [Zip]" text.
6.  **Engine** runs search -> parses rank.
7.  **Controller** updates **SQLite** (status: complete).
8.  **UI** refreshes from DB (or via Signal).

## Patterns to Follow

### Pattern 1: The "qasync" Loop Integration
**What:** Replacing the default `app.exec()` with `qasync.QEventLoop(app).run_forever()`.
**Why:** Allows writing `async def on_button_click(): await scraper.run()` directly, keeping the UI responsive without complex worker thread management.

```python
import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

with loop:
    loop.run_forever()
```

### Pattern 2: The "Human Handover" Signal
**What:** When the scraper detects a Captcha, it emits a signal and *awaits* a specialized "Resume" Future.
**Example:**
1. Bot sees Captcha.
2. Bot emits `request_user_help`.
3. UI pops up / flashes.
4. Bot `await user_resolved_event.wait()`.
5. User solves Captcha, clicks "I solved it" in UI.
6. UI sets event.
7. Bot resumes.

### Pattern 3: Explicit Location Verification
**What:** Never assume the Zip code set successfully. Always read the DOM to verify.
**Logic:**
```python
current_location = await page.locator("#glow-ingress-line2").inner_text()
if target_zip not in current_location:
    raise LocationError("Failed to set location")
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Blocking `time.sleep()` in UI Threads
**Why bad:** Freezes the entire application window (gray screen of death) while waiting for the scraper.
**Instead:** Use `await asyncio.sleep()` within the qasync loop.

### Anti-Pattern 2: Global Browser Instance
**Why bad:** Cookies/Context from one scrape leak into another, corrupting location tests.
**Instead:** Create a fresh `BrowserContext` for each distinct location/session, but you can reuse the heavy `Browser` process.

## Scalability Considerations

| Concern | At 1 User | At 100 Users | At 1M Users |
|---------|-----------|--------------|-------------|
| **Browser Binaries** | Bundled with App (Large installer ~300MB) | Same | Same |
| **Data Storage** | SQLite is fine | SQLite is fine | SQLite is fine (Local app) |
| **Updates** | Manual download | Auto-updater (e.g., PyUpdater) | Specialized distribution |

## Sources

- **qasync documentation**: Standard for integrating asyncio with Qt.
- **Playwright Python docs**: Handling BrowserContexts.
