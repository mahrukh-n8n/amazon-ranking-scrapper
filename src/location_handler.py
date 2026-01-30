from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
import asyncio
import re
import logging
from src.exceptions import LocationVerificationError, CaptchaDetectedError

logger = logging.getLogger(__name__)

class LocationHandler:
    def __init__(self, page: Page):
        self.page = page

    async def verify_location(self, target_zip: str) -> bool:
        """
        Verifies if the current 'Deliver to' location matches the target zip/postal code.
        Returns True if matches, False otherwise.
        """
        try:
            # Selector for the 'Deliver to' line in the top nav
            # Usually: "Deliver to New York 10001" or "London SW1A 1"
            selector = "#glow-ingress-line2"
            await self.page.wait_for_selector(selector, timeout=5000)

            location_text = await self.page.inner_text(selector)

            # Normalize both for comparison (uppercase, remove extra spaces)
            location_upper = location_text.upper().strip()
            target_upper = target_zip.upper().strip()

            # Direct match (case-insensitive)
            if target_upper in location_upper:
                return True

            # For UK postal codes: Amazon often shows only outward code (e.g., "SW1A 1" not "SW1A 1AA")
            # Extract the outward code (first part before space) and check
            target_parts = target_upper.split()
            if target_parts:
                # Check if outward code (first part) is in the location
                outward_code = target_parts[0]
                if outward_code in location_upper:
                    return True

                # Also check combined first two parts for UK format (e.g., "SW1A 1")
                if len(target_parts) >= 2:
                    partial_code = f"{target_parts[0]} {target_parts[1][0]}" if len(target_parts[1]) > 0 else target_parts[0]
                    if partial_code in location_upper:
                        return True

            # For US ZIP codes: check just the 5-digit part
            # Extract digits from target and check
            target_digits = ''.join(filter(str.isdigit, target_upper))
            if len(target_digits) >= 5:
                zip5 = target_digits[:5]
                if zip5 in location_upper:
                    return True

            return False

        except PlaywrightTimeoutError:
            # If element not found, we might be on a page without the nav or captcha
            await self.check_for_captcha()
            return False

    async def set_location(self, zip_code: str):
        """
        Sets the Amazon delivery location to the specified zip code.
        """
        await self.check_for_captcha()

        # 1. Open the location modal
        try:
            await self.page.click("#nav-global-location-popover-link", timeout=5000)
        except PlaywrightTimeoutError:
            raise LocationVerificationError("Could not find 'Deliver to' button. Page might not be loaded correctly.")

        # 2. Wait for modal to appear
        zip_input_selector = "#GLUXZipUpdateInput"
        apply_button_selector = "#GLUXZipUpdate"

        # Wait a moment for modal to render
        await asyncio.sleep(0.5)

        # 2a. Check if "Change" link is visible (when location is already set)
        # The modal shows "Deliver to [ZIP] Change" instead of input field directly
        change_link_selectors = [
            "#GLUXChangePostalCodeLink",  # Common ID for Change link
            "a[data-action='GLUXPostalUpdateAction']",  # Action-based selector
            "#GLUXZipInputSection a.a-link-normal",  # Link within zip section
            "text=Change"  # Fallback: find by text
        ]

        for change_selector in change_link_selectors:
            try:
                if await self.page.is_visible(change_selector):
                    logger.info(f"Found 'Change' link, clicking: {change_selector}")
                    await self.page.click(change_selector, timeout=2000)
                    await asyncio.sleep(0.5)  # Wait for input to appear
                    break
            except Exception:
                continue

        # 2b. Wait for zip input field
        try:
            await self.page.wait_for_selector(zip_input_selector, state="visible", timeout=5000)
        except PlaywrightTimeoutError:
             raise LocationVerificationError("Location modal did not open or zip input not found.")

        # 3. Enter Zip Code
        await self.page.fill(zip_input_selector, zip_code)

        # 4. Click Apply
        # Sometimes 'Apply' is an input type=submit or a span.
        apply_selectors = [
            apply_button_selector,  # #GLUXZipUpdate
            "input[aria-labelledby='GLUXZipUpdate-announce']",
            "#GLUXZipUpdate input",
            "span.a-button-inner input[type='submit']"
        ]

        apply_clicked = False
        for selector in apply_selectors:
            try:
                if await self.page.is_visible(selector):
                    logger.info(f"Clicking Apply button: {selector}")
                    await self.page.click(selector, timeout=3000)
                    apply_clicked = True
                    break
            except Exception:
                continue

        if not apply_clicked:
            logger.warning("Could not find Apply button, trying Enter key")
            await self.page.press(zip_input_selector, "Enter")

        # 5. Wait for Amazon to process the location change
        # Amazon may show loading state or refresh partially
        await asyncio.sleep(1)

        # Wait for network to settle (Amazon often makes AJAX calls here)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            # Network didn't settle, continue anyway
            pass

        # Check for error first
        error_msg_selector = "#GLUXZipError"
        if await self.page.is_visible(error_msg_selector):
             error_text = await self.page.inner_text(error_msg_selector)
             if error_text.strip():
                 raise LocationVerificationError(f"Invalid Zip Code detected by Amazon: {error_text}")

        # 6. Click Done button to close modal (NOT generic close which cancels)
        # Be specific - only click actual "Done" or "Continue" buttons
        confirm_selectors = [
            "#GLUXConfirmClose",  # Done/Continue button
            "button[name='glowDoneButton']",  # Standard Done
            ".a-popover-footer button.a-button-primary",  # Primary button in footer
            "input[data-action='GLUXConfirmAction']",  # Confirm action
        ]

        clicked_confirm = False
        for selector in confirm_selectors:
            # Check if visible first to avoid waiting timeout
            if await self.page.is_visible(selector):
                try:
                    logger.info(f"Clicking confirm button with selector: {selector}")
                    await self.page.click(selector)
                    clicked_confirm = True
                    break
                except Exception:
                    continue

        # If still not clicked, try finding by text "Continue" or "Done"
        if not clicked_confirm:
             try:
                 # Look for button with text "Continue"
                 continue_btn = self.page.get_by_role("button", name="Continue")
                 if await continue_btn.is_visible():
                     await continue_btn.click()
                     clicked_confirm = True
                 else:
                     done_btn = self.page.get_by_role("button", name="Done")
                     if await done_btn.is_visible():
                         await done_btn.click()
                         clicked_confirm = True
             except Exception:
                 pass

        if not clicked_confirm:
            # If we didn't find a button, maybe it auto-refreshed?
            pass

        # 6. Wait for page reload with proper navigation handling
        # Amazon often triggers a delayed page refresh after location change
        await self._wait_for_location_update(zip_code)

    async def _wait_for_location_update(self, zip_code: str, max_attempts: int = 5):
        """
        Waits for Amazon to complete the location update, handling delayed refreshes.
        """
        for attempt in range(max_attempts):
            try:
                # First, wait for any pending navigation to complete
                await self.page.wait_for_load_state("domcontentloaded", timeout=3000)
            except PlaywrightTimeoutError:
                pass

            # Check if modal is still visible (location change in progress)
            modal_visible = False
            try:
                modal_visible = await self.page.is_visible(".a-modal-scroller", )
            except Exception:
                pass

            if modal_visible:
                # Modal still open, wait a bit and check if it closes or page refreshes
                logger.info(f"Modal still visible, waiting... (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(1)
                continue

            # Modal closed, now wait for location text to stabilize
            # The page might still be refreshing
            try:
                # Wait for the location element to be present
                await self.page.wait_for_selector("#glow-ingress-line2", timeout=5000)
            except PlaywrightTimeoutError:
                # Page might be mid-refresh, wait and retry
                logger.info(f"Location element not found, page may be refreshing (attempt {attempt + 1})")
                await asyncio.sleep(2)
                continue

            # Check if location matches
            if await self.verify_location(zip_code):
                logger.info(f"Location verified: {zip_code}")
                return

            # Location doesn't match yet - could be stale DOM or refresh pending
            # Wait a moment for potential late refresh
            logger.info(f"Location not yet matching, waiting for potential refresh (attempt {attempt + 1})")

            # Watch for navigation that might happen
            try:
                # Wait briefly to see if a navigation starts
                await self.page.wait_for_load_state("networkidle", timeout=3000)
            except PlaywrightTimeoutError:
                pass

            await asyncio.sleep(1)

        # All attempts exhausted, do final verification
        await self.check_for_captcha()

        if not await self.verify_location(zip_code):
            current_loc = "Unknown"
            try:
                if await self.page.query_selector("#glow-ingress-line2"):
                    current_loc = await self.page.inner_text("#glow-ingress-line2")
            except Exception:
                pass
            raise LocationVerificationError(f"Failed to set location to {zip_code}. Current location: {current_loc}")

    async def check_for_captcha(self):
        """
        Checks if a captcha is present on the page.
        """
        # Common Amazon captcha selectors
        # 1. Title "Amazon.com - Something went wrong" or "Robot Check"
        # 2. Body contains text "Enter the characters you see below"

        title = await self.page.title()
        if "Robot Check" in title or "Something went wrong" in title: # Basic check
             # Verify specific element
             if await self.page.is_visible("input#captchacharacters"):
                 raise CaptchaDetectedError("Amazon Captcha detected.")
