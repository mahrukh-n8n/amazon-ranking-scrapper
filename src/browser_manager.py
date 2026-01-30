import os
from playwright.async_api import async_playwright, BrowserContext, Page

class BrowserManager:
    def __init__(self, user_data_dir: str = "user_data", headless: bool = False):
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.headless = headless
        self.playwright = None
        self.context: BrowserContext = None
        self.page: Page = None

    async def start(self):
        """Starts the browser with a persistent context."""
        self.playwright = await async_playwright().start()

        # Ensure user data directory exists
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

        # Launch persistent context
        # SCRAPE-04: System persists session cookies to reuse location settings across runs.
        # SCRAPE-05: System runs in "Headed" mode (visible browser) by default.
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            viewport={"width": 1280, "height": 720},
            # Using a standard user agent to look like a normal desktop browser
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )

        # Get the first page or create one
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

    async def close(self):
        """Closes the browser context and playwright instance."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
