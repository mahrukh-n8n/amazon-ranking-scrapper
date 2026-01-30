from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from src.browser_manager import BrowserManager
from src.location_handler import LocationHandler
from src.exceptions import CaptchaDetectedError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonScraper:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.page: Page = None
        self.location_handler: LocationHandler = None

    async def initialize(self):
        """Starts the browser and initializes handlers."""
        if not self.browser_manager.page:
             await self.browser_manager.start()

        self.page = self.browser_manager.page
        self.location_handler = LocationHandler(self.page)

    async def go_to_home(self, marketplace: str = "amazon.com"):
        """Navigates to Amazon homepage for the specified marketplace."""
        if not self.page:
            await self.initialize()

        # Normalize marketplace - ensure it has proper format
        marketplace = marketplace.lower().strip()

        # Handle various input formats
        if not marketplace.startswith("amazon."):
            # If just domain suffix like "co.uk" or "com"
            if "." in marketplace:
                marketplace = f"amazon.{marketplace}"
            else:
                marketplace = f"amazon.{marketplace}"

        # Build the URL
        url = f"https://www.{marketplace}"

        logger.info(f"Navigating to {url}...")
        await self.page.goto(url)
        await self.location_handler.check_for_captcha()

    async def set_delivery_zip(self, zip_code: str):
        """Sets the delivery zip code using LocationHandler."""
        if not self.location_handler:
            await self.initialize()

        logger.info(f"Setting delivery zip code to {zip_code}...")
        await self.location_handler.set_location(zip_code)

    async def search_keyword(self, keyword: str):
        """Searches for a keyword on Amazon."""
        if not self.page:
            await self.initialize()

        logger.info(f"Searching for keyword: {keyword}")

        search_box = "#twotabsearchtextbox"

        try:
            await self.page.wait_for_selector(search_box, state="visible")

            # Click to focus
            await self.page.click(search_box)

            # Clear existing text first just in case
            await self.page.fill(search_box, "")
            # Type slowly to ensure events trigger
            await self.page.type(search_box, keyword, delay=50)

            # Use Enter key
            await self.page.press(search_box, "Enter")

            # Wait for results to load explicitly
            # "domcontentloaded" is not enough if navigation hasn't started.
            # We wait for the result list to appear.
            try:
                 await self.page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=15000)
            except PlaywrightTimeoutError:
                 logger.warning("Search results did not appear via Enter key. Clicking search button...")
                 await self.page.click("#nav-search-submit-button")
                 await self.page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=15000)

            await self.location_handler.check_for_captcha()

        except PlaywrightTimeoutError:
            logger.error("Failed to perform search. Search box not found or results not loaded.")
            raise

    async def find_asins_ranks(self, target_asins: list) -> list:
        """
        Finds the ranks of multiple ASINs in the current search results.
        Returns a list of dicts, each with 'rank', 'page', 'found', 'asin'.
        """
        logger.info(f"Looking for ASINs: {', '.join(target_asins)}")

        result_selector = 'div[data-component-type="s-search-result"]'

        try:
            await self.page.wait_for_selector(result_selector, timeout=10000)
        except PlaywrightTimeoutError:
             logger.warning("No search results found.")
             return [{"found": False, "rank": -1, "page": 1, "asin": asin} for asin in target_asins]

        results = await self.page.query_selector_all(result_selector)

        found_results = {asin: {"found": False, "rank": -1, "page": 1, "asin": asin} for asin in target_asins}

        for index, result in enumerate(results):
            asin = await result.get_attribute("data-asin")
            if asin in target_asins:
                rank = index + 1
                logger.info(f"Found ASIN {asin} at rank {rank} on page 1")
                found_results[asin] = {
                    "found": True,
                    "rank": rank,
                    "page": 1,
                    "asin": asin
                }

        # Check which ASINs were not found and log them
        for asin, res in found_results.items():
            if not res["found"]:
                logger.info(f"ASIN {asin} not found on page 1")

        return list(found_results.values())

    async def close(self):
        await self.browser_manager.close()
