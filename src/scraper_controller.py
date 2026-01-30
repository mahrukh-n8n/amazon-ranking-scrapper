import asyncio
import logging
import re
import os
from datetime import datetime
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal
from src.browser_manager import BrowserManager
from src.scraper import AmazonScraper
from src.exceptions import CaptchaDetectedError, LocationVerificationError

logger = logging.getLogger(__name__)

class ScraperController(QObject):
    captcha_detected = pyqtSignal()
    paused = pyqtSignal()
    resumed = pyqtSignal()
    task_started = pyqtSignal(int, int)  # (current_task, total_tasks)
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

    def set_tasks(self, tasks: list):
        """Sets the list of tasks to process."""
        self.tasks = tasks
        self.current_task_index = 0

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

        logger.info(f"Starting job with {len(self.tasks)} tasks...")

        try:
            # Initialize Browser
            self.browser_manager = BrowserManager(user_data_dir="user_data", headless=False)
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

                logger.info(f"Processing Task {i+1}/{len(self.tasks)}: {task['keyword']} (ASINs: {', '.join(asins)}) in {task['zip_code']} on {task_marketplace}")

                # Navigate to marketplace if changed or first task
                if self.current_marketplace != task_marketplace:
                    logger.info(f"Switching marketplace to {task_marketplace}")
                    await self.scraper.go_to_home(task_marketplace)
                    self.current_marketplace = task_marketplace

                    await self.pause_event.wait()
                    if self.check_stop(): break

                # Retry loop for the task
                task_complete = False
                while not task_complete and not self.check_stop():
                    try:
                        # 1. Set Location
                        # Optimization: We could check if location is already set, but set_location handles verification.
                        await self.scraper.set_delivery_zip(task['zip_code'])

                        await self.pause_event.wait()  # Blocks if paused
                        if self.check_stop(): break

                        # 2. Search
                        await self.scraper.search_keyword(task['keyword'])

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
                                "Keyword": task['keyword'],
                                "ASIN": res['asin'],
                                "Rank": res['rank'] if res['found'] else "N/A",
                                "Found": res['found'],
                                "Page": res['page']
                            }
                            self.all_results.append(full_result)

                            if res['found']:
                                logger.info(f"Result for {res['asin']}: Found at Rank {res['rank']}")
                            else:
                                logger.info(f"Result for {res['asin']}: Not found")

                        task_complete = True # Success

                    except CaptchaDetectedError:
                        await self.handle_captcha()
                        # Loop continues to retry the task
                    except LocationVerificationError as e:
                        logger.error(f"Location error: {e}")
                        # Move to next task or retry? For now, move to next task to avoid infinite loops if zip is bad.
                        break
                    except Exception as e:
                        logger.error(f"Task failed with unexpected error: {e}", exc_info=True)
                        break

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

        if self.scraper:
            await self.scraper.close()
        self.scraper = None
        self.browser_manager = None

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
