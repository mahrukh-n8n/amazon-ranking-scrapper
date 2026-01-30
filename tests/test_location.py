import pytest
import os
from src.location_handler import LocationHandler, LocationVerificationError
from src.browser_manager import BrowserManager

# Mock file path
MOCK_HTML_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "amazon_mock.html")
MOCK_URL = f"file://{MOCK_HTML_PATH}"

@pytest.fixture(scope="function")
async def browser_page():
    manager = BrowserManager(headless=True)
    await manager.start()
    yield manager.page
    await manager.close()

@pytest.mark.asyncio
async def test_verify_location_match(browser_page):
    await browser_page.goto(MOCK_URL)

    # Manually set the text to simulate a correct state
    await browser_page.evaluate("document.getElementById('glow-ingress-line2').innerText = 'Deliver to New York 10001'")

    handler = LocationHandler(browser_page)
    result = await handler.verify_location("10001")
    assert result is True

@pytest.mark.asyncio
async def test_verify_location_mismatch(browser_page):
    await browser_page.goto(MOCK_URL)

    # Text is "Deliver to Philippines" by default in mock
    handler = LocationHandler(browser_page)
    result = await handler.verify_location("10001")
    assert result is False

@pytest.mark.asyncio
async def test_set_location_success(browser_page):
    await browser_page.goto(MOCK_URL)
    handler = LocationHandler(browser_page)

    # We need to mock the reload behavior or ensure the script handles it without actual reload
    # In our mock HTML, clicking "Apply" changes the text directly.
    # The real LocationHandler waits for reload.
    # We might need to adjust the test or the handler to be testable with mocks that don't reload.
    # For this test, let's override the wait_for_load_state in the handler's page object temporarily?
    # Or just let it timeout if it doesn't reload?
    # Actually, the mock HTML doesn't trigger a reload, so `wait_for_load_state` might return immediately or timeout depending on state.
    # Let's try running it.

    await handler.set_location("10001")

    # Verify the DOM changed
    assert await handler.verify_location("10001") is True

@pytest.mark.asyncio
async def test_set_location_failure(browser_page):
    await browser_page.goto(MOCK_URL)
    handler = LocationHandler(browser_page)

    # 99999 triggers error in our mock
    with pytest.raises(LocationVerificationError) as excinfo:
        await handler.set_location("99999")

    assert "Invalid Zip Code" in str(excinfo.value)
