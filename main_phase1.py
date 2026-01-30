import asyncio
from src.browser_manager import BrowserManager
from src.scraper import AmazonScraper
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Phase1Main")

async def main():
    # Initialize Browser Manager (Headed mode by default)
    # Using 'user_data' to persist cookies
    browser_manager = BrowserManager(user_data_dir="user_data", headless=False)

    scraper = AmazonScraper(browser_manager)

    try:
        logger.info("Starting Phase 1 Integration Test...")

        # 1. Initialize and go to Home
        await scraper.initialize()
        await scraper.go_to_home()

        # 2. Set Zip Code
        target_zip = "10001" # New York
        logger.info(f"Setting Zip Code to {target_zip}...")
        try:
            await scraper.set_delivery_zip(target_zip)
            logger.info("Zip Code set successfully.")
        except Exception as e:
            logger.error(f"Failed to set Zip Code: {e}")
            # Capture screenshot for debugging
            screenshot_path = "error_screenshot.png"
            await scraper.page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            # We continue to see if search works anyway, but note the failure

        # 3. Search for a keyword
        keyword = "gaming mouse"
        logger.info(f"Searching for '{keyword}'...")
        await scraper.search_keyword(keyword)

        # 4. Find an ASIN
        # Since we don't know which ASINs are currently ranking, let's grab the first one found
        # and then pretend we were looking for it, to test the finding logic.

        # Just use playwright directly to grab an ASIN from the page for testing purposes
        # Wait a bit longer for results to populate
        try:
            await scraper.page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=10000)
        except Exception:
            logger.warning("Timeout waiting for search results selector.")

        first_result = await scraper.page.query_selector('div[data-component-type="s-search-result"]')
        if first_result:
            target_asin = await first_result.get_attribute("data-asin")
            logger.info(f"Detected top ASIN on page: {target_asin}. Now attempting to 'find' it using scraper logic...")

            # Now use the scraper method to find it
            result = await scraper.find_asin_rank(target_asin)

            if result["found"]:
                logger.info(f"SUCCESS: Found ASIN {result['asin']} at Rank {result['rank']} on Page {result['page']}")
            else:
                logger.error(f"FAILURE: Could not find ASIN {target_asin} even though we just saw it.")
        else:
            logger.warning("No search results found to test against.")
            # Screenshot for debugging search results
            await scraper.page.screenshot(path="search_results_debug.png")
            logger.info("Saved search_results_debug.png")

            # Dump HTML to see what we got
            content = await scraper.page.content()
            with open("search_results_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Saved search_results_debug.html")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

    finally:
        # Keep browser open for a few seconds so user can see
        logger.info("Test finished. Closing in 5 seconds...")
        await asyncio.sleep(5)
        await scraper.close()
        logger.info("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
