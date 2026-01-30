---
phase: 02
name: Interactive Desktop UI
depends_on: [01-core-engine]
autonomous: true
---

# Phase 2: Interactive Desktop UI

**Goal:** User can manage the scraping session without touching code.
**Core Value:** Ease of use and manual intervention handling.

## Execution Waves

### Wave 1: UI Foundation & Async Integration
**Focus:** Basic window with Start/Stop controls and Playwright integration.

<task>
<id>1.1</id>
<title>Initialize UI Project Structure & Dependencies</title>
<description>
- Add `PyQt6` and `qasync` to poetry dependencies.
- Create `src/ui/` directory.
- Create basic `MainWindow` class.
- Setup `qasync` loop to handle asyncio alongside Qt event loop.
</description>
<file_paths>
- pyproject.toml
- src/ui/__init__.py
- src/ui/main_window.py
- main_ui.py
</file_paths>
<must_have>
- Application launches a window.
- Window handles close event cleanly.
</must_have>
</task>

<task>
<id>1.2</id>
<title>Integrate Scraper with UI (Start/Stop)</title>
<description>
- Connect `AmazonScraper` to the UI.
- Implement "Start Job" button that triggers the scraping process (async).
- Implement "Stop/Pause" mechanism (cancellation token or flag).
</description>
<file_paths>
- src/ui/main_window.py
- src/scraper_controller.py
</file_paths>
<must_have>
- Clicking Start launches the browser and runs a test scraping sequence.
- Clicking Stop terminates the browser/process gracefully.
</must_have>
</task>

### Wave 2: Feedback & Data Loading
**Focus:** showing the user what is happening and inputting data.

<task>
<id>2.1</id>
<title>Implement Real-time Activity Log</title>
<description>
- Create a UI Logging Handler.
- Redirect `logging` output to a text widget in the UI.
- Ensure log updates do not freeze the UI.
</description>
<file_paths>
- src/ui/log_handler.py
- src/ui/main_window.py
</file_paths>
<must_have>
- Logs appear in the window as they happen (e.g., "Setting Zip...").
</must_have>
</task>

<task>
<id>2.2</id>
<title>Implement Job File Loading (CSV/Excel)</title>
<description>
- Add `pandas` and `openpyxl` dependencies.
- Create "Load Job" button.
- Parse CSV/Excel files to extract Marketplace, Zip Code, ASINs, Keywords.
- Display loaded task count in UI.
</description>
<file_paths>
- src/data_loader.py
- src/ui/main_window.py
</file_paths>
<must_have>
- Can load a sample CSV.
- UI shows "Loaded X tasks".
</must_have>
</task>

### Wave 3: Captcha Handling & Refinement
**Focus:** Handling interruptions.

<task>
<id>3.1</id>
<title>Implement Captcha Pause/Alert</title>
<description>
- Modify `AmazonScraper` or Controller to emit a signal/event when Captcha is detected.
- UI listens for this event.
- UI pauses automation, plays a sound (optional/simple beep), and brings window to front.
- "Resume" button becomes active.
</description>
<file_paths>
- src/scraper.py
- src/scraper_controller.py
- src/ui/main_window.py
</file_paths>
<must_have>
- When `check_for_captcha` raises/detects, the UI shows "Captcha Detected" status.
- User can solve it in the headed browser, then click "Resume" to continue.
</must_have>
</task>

<task>
<id>3.2</id>
<title>Phase 2 Integration Verification</title>
<description>
- Run a full session via UI.
- Load file -> Start -> Watch logs -> (Simulate Captcha) -> Resume -> Finish.
</description>
<file_paths>
- manual_test_plan.md
</file_paths>
<must_have>
- Manual verification of the flow.
</must_have>
</task>

## Verification Criteria
- [ ] UI launches without errors.
- [ ] User can load a CSV file.
- [ ] "Start" button runs the scraping logic in a non-blocking way.
- [ ] Logs are visible in real-time.
- [ ] Captcha detection pauses execution and waits for user input.
