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

    async def find_asin_rank(self, target_asin: str) -> dict:
        """
        Finds the rank of a specific ASIN in the current search results.
        Returns a dict with 'rank', 'page', 'found', 'asin', 'keyword'.
        """
        logger.info(f"Looking for ASIN: {target_asin}")

        # Selector for organic search results (excluding sponsored if possible, or just all)
        # data-component-type="s-search-result" is standard for organic and sponsored results mixed in the main list.
        # Sponsored results often have class "AdHolder" or similar, but often users want to know visible rank including ads or organic rank.
        # For now, let's count all results as "rank" on page, but we might want to filter sponsored later.
        # The requirements just say "extract ranks".

        result_selector = 'div[data-component-type="s-search-result"]'

        try:
            await self.page.wait_for_selector(result_selector, timeout=10000)
        except PlaywrightTimeoutError:
             logger.warning("No search results found.")
             return {"found": False, "rank": -1, "page": 1}

        results = await self.page.query_selector_all(result_selector)

        for index, result in enumerate(results):
            asin = await result.get_attribute("data-asin")
            if asin == target_asin:
                rank = index + 1
                logger.info(f"Found ASIN {target_asin} at rank {rank} on page 1")
                return {
                    "found": True,
                    "rank": rank,
                    "page": 1,
                    "asin": target_asin
                }

        logger.info(f"ASIN {target_asin} not found on page 1")
        return {"found": False, "rank": -1, "page": 1, "asin": target_asin}

    async def close(self):
        await self.browser_manager.close()
