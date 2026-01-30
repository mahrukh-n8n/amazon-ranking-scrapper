import asyncio
import logging
import re
import os
import httpx
from datetime import datetime
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.browser_manager import BrowserManager
from src.scraper import AmazonScraper
from src.exceptions import CaptchaDetectedError, LocationVerificationError

logger = logging.getLogger(__name__)

class ScraperController(QObject):
    captcha_detected = pyqtSignal()
    paused = pyqtSignal()
    resumed = pyqtSignal()
    task_started = pyqtSignal(int, int)  # (current_task, total_tasks)
    job_started = pyqtSignal()
    job_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.browser_manager = None
        self.scraper = None
        self.is_running = False
        self.should_stop = False
        self.is_paused = False
        self.tasks = []
        self.current_task_index = 0
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Not paused initially
        self.current_marketplace = None  # Track current marketplace for navigation
        self.all_results = []
        self.webhook_url = ""
        self.webhook_enabled = False
        self.headless = False  # Run browser in headless mode

        self.scheduler = AsyncIOScheduler()
        # Defer scheduler start until event loop is running
        self._scheduler_started = False

    def set_tasks(self, tasks: list):
        """Sets the list of tasks to process."""
        self.tasks = tasks
        self.current_task_index = 0

    def _ensure_scheduler_started(self):
        """Start the scheduler if not already running (requires event loop)."""
        if not self._scheduler_started:
            try:
                self.scheduler.start()
                self._scheduler_started = True
            except Exception as e:
                logger.warning(f"Could not start scheduler: {e}")

    def schedule_job(self, recurrence: str, time_str: str):
        """
        Schedules a scraping job.
        recurrence: 'Daily' or 'Weekly'
        time_str: HH:MM
        """
        self._ensure_scheduler_started()
        # Clear existing scheduled jobs for scraping
        self.scheduler.remove_all_jobs()

        if not recurrence or not time_str:
            logger.info("Scheduling disabled or incomplete config provided.")
            return

        try:
            hour, minute = map(int, time_str.split(':'))

            if recurrence == 'Daily':
                trigger = CronTrigger(hour=hour, minute=minute)
            elif recurrence == 'Weekly':
                # Default to Monday for weekly if not specified, or just same time every week from now?
                # Plan says "Weekly (cron: day_of_week, hour, minute)".
                # I'll default to day_of_week=0 (Monday) for now as a simple implementation.
                trigger = CronTrigger(day_of_week=0, hour=hour, minute=minute)
            else:
                logger.error(f"Unsupported recurrence: {recurrence}")
                return

            self.scheduler.add_job(
                self.start_job,
                trigger=trigger,
                id='amazon_scraping_job',
                replace_existing=True
            )
            logger.info(f"Job scheduled: {recurrence} at {time_str}")
        except Exception as e:
            logger.error(f"Failed to schedule job: {e}")

    def get_next_run(self):
        """Returns the timestamp of the next scheduled run or None."""
        self._ensure_scheduler_started()
        job = self.scheduler.get_job('amazon_scraping_job')
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def pause_job(self):
        """Pauses the job."""
        self.is_paused = True
        self.pause_event.clear()  # Blocks execution
        self.paused.emit()
        logger.info("Job paused")

    def resume_job(self):
        """Resumes the job after a pause."""
        self.is_paused = False
        self.pause_event.set()  # Unblocks execution
        self.resumed.emit()
        logger.info("Job resumed")

    async def handle_captcha(self):
        """Handles captcha detection by pausing and waiting for user resume."""
        logger.warning("Captcha detected! Pausing job.")
        self.captcha_detected.emit()
        self.pause_job()

        # Wait until pause_event is set (via resume_job)
        await self.pause_event.wait()
        logger.info("Job resumed after captcha.")

    async def start_job(self):
        """Starts the scraping job."""
        if self.is_running:
            return

        if not self.tasks:
            logger.warning("No tasks loaded.")
            return

        self.is_running = True
        self.should_stop = False
        self.pause_event.set()  # Ensure not paused at start
        self.current_marketplace = None  # Reset marketplace tracking
        self.all_results = []
        self.job_started.emit()

        logger.info(f"Starting job with {len(self.tasks)} tasks...")

        try:
            # Initialize Browser
            self.browser_manager = BrowserManager(user_data_dir="user_data", headless=self.headless)
            self.scraper = AmazonScraper(self.browser_manager)

            await self.scraper.initialize()

            if self.check_stop(): return

            for i, task in enumerate(self.tasks):
                if self.check_stop(): break
                self.current_task_index = i
                self.task_started.emit(i + 1, len(self.tasks))

                task_marketplace = task.get('marketplace', 'amazon.com')
                # Split ASINs if multiple are provided (comma, space, tab, newline separated)
                asins = [a.strip() for a in re.split(r'[,\s\t\n]+', task['asin']) if a.strip()]
                # Split Keywords if multiple are provided (comma or newline separated, NOT space - keywords can have spaces)
                keywords = [k.strip() for k in re.split(r'[,\n]+', task['keyword']) if k.strip()]

                logger.info(f"Processing Task {i+1}/{len(self.tasks)}: {len(keywords)} keyword(s), {len(asins)} ASIN(s) in {task['zip_code']} on {task_marketplace}")

                # Navigate to marketplace if changed or first task
                if self.current_marketplace != task_marketplace:
                    logger.info(f"Switching marketplace to {task_marketplace}")
                    await self.scraper.go_to_home(task_marketplace)
                    self.current_marketplace = task_marketplace

                    await self.pause_event.wait()
                    if self.check_stop(): break

                # Process each keyword separately
                for keyword in keywords:
                    if self.check_stop(): break

                    logger.info(f"Searching keyword: '{keyword}' for ASINs: {', '.join(asins)}")

                    # Retry loop for the keyword search
                    keyword_complete = False
                    while not keyword_complete and not self.check_stop():
                        try:
                            # 1. Set Location
                            # Optimization: We could check if location is already set, but set_location handles verification.
                            await self.scraper.set_delivery_zip(task['zip_code'])

                            await self.pause_event.wait()  # Blocks if paused
                            if self.check_stop(): break

                            # 2. Search
                            await self.scraper.search_keyword(keyword)

                            await self.pause_event.wait()  # Blocks if paused
                            if self.check_stop(): break

                            # 3. Find ASINs
                            results = await self.scraper.find_asins_ranks(asins)

                            await self.pause_event.wait()  # Blocks if paused

                            for res in results:
                                # Add task metadata to results
                                full_result = {
                                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "Marketplace": task_marketplace,
                                    "Zip Code": task['zip_code'],
                                    "Keyword": keyword,
                                    "ASIN": res['asin'],
                                    "Sequential Rank": res['sequential_rank'] if res['found'] else "N/A",
                                    "Organic Rank": res['organic_rank'] if res['found'] and res['organic_rank'] > 0 else "N/A",
                                    "Sponsored Rank": res['sponsored_rank'] if res['found'] and res['sponsored_rank'] > 0 else "N/A",
                                    "Is Sponsored": res.get('is_sponsored', False),
                                    "Found": res['found'],
                                    "Page": res['page']
                                }
                                self.all_results.append(full_result)

                                if res['found']:
                                    rank_info = f"Sequential: {res['sequential_rank']}"
                                    if res.get('is_sponsored'):
                                        rank_info += f", Sponsored: {res['sponsored_rank']}"
                                    else:
                                        rank_info += f", Organic: {res['organic_rank']}"
                                    logger.info(f"Result for {res['asin']}: {rank_info}")
                                else:
                                    logger.info(f"Result for {res['asin']}: Not found")

                            keyword_complete = True # Success

                        except CaptchaDetectedError:
                            await self.handle_captcha()
                            # Loop continues to retry the keyword
                        except LocationVerificationError as e:
                            logger.error(f"Location error: {e}")
                            # Move to next keyword to avoid infinite loops if zip is bad
                            break
                        except Exception as e:
                            logger.error(f"Keyword search failed with unexpected error: {e}", exc_info=True)
                            break

                    # Small delay between keywords
                    await asyncio.sleep(1)

                # Small delay between tasks
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Job failed: {e}", exc_info=True)
        finally:
            await self.cleanup()
            self.is_running = False
            self.job_finished.emit()
            logger.info("Job finished or stopped.")

    def stop_job(self):
        """Signals the job to stop."""
        logger.info("Stopping job...")
        self.should_stop = True

    def check_stop(self):
        """Checks if stop was requested."""
        if self.should_stop:
            logger.info("Stop requested, aborting operation.")
            return True
        return False

    async def cleanup(self):
        """Cleans up resources and saves results."""
        if self.all_results:
            self.save_results()
            if self.webhook_enabled and self.webhook_url:
                await self._send_webhook()

        if self.scraper:
            await self.scraper.close()
        self.scraper = None
        self.browser_manager = None

    async def _send_webhook(self):
        """Sends results to the configured webhook URL."""
        if not self.webhook_url:
            return

        logger.info(f"Sending results to webhook: {self.webhook_url}")
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "timestamp": datetime.now().isoformat(),
                    "total_results": len(self.all_results),
                    "results": self.all_results
                }
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                logger.info("Webhook sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")

    def save_results(self):
        """Saves accumulated results to a CSV file."""
        if not self.all_results:
            return

        try:
            # Ensure results directory exists
            os.makedirs("results", exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results/results_{timestamp}.csv"

            df = pd.DataFrame(self.all_results)
            df.to_csv(filename, index=False)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
