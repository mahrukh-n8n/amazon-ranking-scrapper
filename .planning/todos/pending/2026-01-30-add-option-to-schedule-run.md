---
created: 2026-01-30T10:30
title: Add option to schedule run
area: ui
files:
  - src/ui/main_window.py
---

## Problem

Users currently have to manually start scraping jobs. There is a need to automate periodic runs (e.g., daily at a specific time) to track rankings consistently over time without manual intervention.

## Solution

1. Add a scheduling section to the "Settings" group box in `src/ui/main_window.py`.
2. Provide inputs for:
   - Recurrence (e.g., Daily, Weekly)
   - Start Time (e.g., 11:00 AM)
3. Implement a background timer or task scheduler (e.g., using `QTimer` or a dedicated library) that triggers `on_start_clicked` or the controller's `start_job` at the scheduled time.
4. Ensure the application can remain open or has a "run in background" mode for the scheduler to function.
