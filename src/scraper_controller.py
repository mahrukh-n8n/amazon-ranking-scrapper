import asyncio
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from src.browser_manager import BrowserManager
from src.scraper import AmazonScraper
from src.exceptions import CaptchaDetectedError, LocationVerificationError

logger = logging.getLogger(__name__)

class ScraperController(QObject):
    captcha_detected = pyqtSignal()
    paused = pyqtSignal()
    resumed = pyqtSignal()

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

        logger.info(f"Starting job with {len(self.tasks)} tasks...")

        try:
            # Initialize Browser
            self.browser_manager = BrowserManager(user_data_dir="user_data", headless=False)
            self.scraper = AmazonScraper(self.browser_manager)

            await self.scraper.initialize()

            if self.check_stop(): return

            await self.scraper.go_to_home()

            for i, task in enumerate(self.tasks):
                if self.check_stop(): break
                self.current_task_index = i

                logger.info(f"Processing Task {i+1}/{len(self.tasks)}: {task['keyword']} (ASIN: {task['asin']}) in {task['zip_code']}")

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

                        # 3. Find ASIN
                        result = await self.scraper.find_asin_rank(task['asin'])

                        await self.pause_event.wait()  # Blocks if paused

                        if result['found']:
                            logger.info(f"Result: Found at Rank {result['rank']}")
                        else:
                            logger.info("Result: Not found")

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
        """Cleans up resources."""
        if self.scraper:
            await self.scraper.close()
        self.scraper = None
        self.browser_manager = None
