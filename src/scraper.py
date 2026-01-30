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
        Returns a list of dicts with three rank types:
        - sequential_rank: Position counting ALL items (sponsored + organic)
        - sponsored_rank: Position among sponsored/ad products only (-1 if organic)
        - organic_rank: Position among non-sponsored products only (-1 if sponsored)
        """
        logger.info(f"Looking for ASINs: {', '.join(target_asins)}")

        result_selector = 'div[data-component-type="s-search-result"]'

        try:
            await self.page.wait_for_selector(result_selector, timeout=10000)
        except PlaywrightTimeoutError:
             logger.warning("No search results found.")
             return [{
                 "found": False,
                 "asin": asin,
                 "page": 1,
                 "sequential_rank": -1,
                 "sponsored_rank": -1,
                 "organic_rank": -1,
                 "is_sponsored": False
             } for asin in target_asins]

        results = await self.page.query_selector_all(result_selector)

        # Initialize results for all target ASINs
        found_results = {asin: {
            "found": False,
            "asin": asin,
            "page": 1,
            "sequential_rank": -1,
            "sponsored_rank": -1,
            "organic_rank": -1,
            "is_sponsored": False
        } for asin in target_asins}

        # Counters for each rank type
        sequential_position = 0
        sponsored_position = 0
        organic_position = 0

        for result in results:
            asin = await result.get_attribute("data-asin")
            if not asin:
                continue

            sequential_position += 1

            # Check if this result is sponsored
            # Amazon marks sponsored items with various indicators
            is_sponsored = await self._is_sponsored_result(result)

            if is_sponsored:
                sponsored_position += 1
                current_sponsored_rank = sponsored_position
                current_organic_rank = -1
            else:
                organic_position += 1
                current_organic_rank = organic_position
                current_sponsored_rank = -1

            # Check if this ASIN is one we're looking for
            if asin in target_asins:
                logger.info(
                    f"Found ASIN {asin} - Sequential: {sequential_position}, "
                    f"Sponsored: {current_sponsored_rank}, Organic: {current_organic_rank}, "
                    f"Is Sponsored: {is_sponsored}"
                )
                found_results[asin] = {
                    "found": True,
                    "asin": asin,
                    "page": 1,
                    "sequential_rank": sequential_position,
                    "sponsored_rank": current_sponsored_rank,
                    "organic_rank": current_organic_rank,
                    "is_sponsored": is_sponsored
                }

        # Log ASINs not found
        for asin, res in found_results.items():
            if not res["found"]:
                logger.info(f"ASIN {asin} not found on page 1")

        return list(found_results.values())

    async def _is_sponsored_result(self, result_element) -> bool:
        """
        Determines if a search result is a sponsored/ad product.
        Amazon uses various indicators for sponsored content.

        To update selectors when Amazon changes their layout:
        1. Open Amazon search results in browser
        2. Right-click on a sponsored product's "Sponsored" label
        3. Inspect element to find the CSS class or attribute
        4. Add the new selector to the lists below
        5. Test with a known sponsored product

        Current detection methods:
        - CSS selectors for sponsored label elements
        - HTML class/attribute patterns
        - Text content checks (last resort)
        """
        try:
            # Method 1: Check for specific sponsored label selectors
            # These are the most reliable - update when Amazon changes UI
            # Last updated: 2026-01-30
            sponsored_label_selectors = [
                # Primary sponsored label (most common)
                '.puis-sponsored-label-text',
                '.s-sponsored-label-info-icon',

                # Sponsored label container
                '[data-component-type="sp-sponsored-result"]',

                # Alternative label formats
                '.s-label-popover-default[aria-label*="ponsored"]',
                'span.a-color-secondary:has-text("Sponsored")',
            ]

            for selector in sponsored_label_selectors:
                try:
                    element = await result_element.query_selector(selector)
                    if element:
                        # Verify it's actually visible
                        is_visible = await element.is_visible()
                        if is_visible:
                            return True
                except Exception:
                    continue

            # Method 2: Check data attributes (more reliable than text)
            try:
                # Check if the result div itself has sponsored markers
                data_attrs = await result_element.evaluate("""el => {
                    return {
                        componentType: el.getAttribute('data-component-type') || '',
                        className: el.className || '',
                        adId: el.getAttribute('data-asin-ad-id') || '',
                        adType: el.getAttribute('data-ad-type') || ''
                    }
                }""")

                # Explicit ad identifiers
                if data_attrs.get('adId') or data_attrs.get('adType'):
                    return True

                if 'sp-sponsored' in data_attrs.get('componentType', '').lower():
                    return True

                class_name = data_attrs.get('className', '').lower()
                if 'adholder' in class_name or 'sponsored' in class_name:
                    return True

            except Exception:
                pass

            # Method 3: Look for "Sponsored" text in the FIRST line only
            # This avoids false positives from product descriptions
            try:
                # Get just the top portion of the result
                first_child = await result_element.query_selector('.a-section:first-child')
                if first_child:
                    first_text = await first_child.inner_text()
                    # Only check first 50 chars to avoid false positives
                    first_line = first_text.split('\n')[0][:50] if first_text else ''
                    if 'Sponsored' in first_line or 'Gesponsert' in first_line or 'Sponsorisé' in first_line:
                        return True
            except Exception:
                pass

            return False

        except Exception as e:
            logger.debug(f"Error checking sponsored status: {e}")
            return False

    async def close(self):
        await self.browser_manager.close()
