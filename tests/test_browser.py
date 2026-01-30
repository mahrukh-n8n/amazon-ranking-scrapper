import pytest
import os
import shutil
import asyncio
from src.browser_manager import BrowserManager

# Use a temporary directory for user data in tests to avoid polluting the real user_data
TEST_USER_DATA = "test_user_data"

@pytest.fixture(scope="function")
async def browser_manager():
    # Setup
    manager = BrowserManager(user_data_dir=TEST_USER_DATA, headless=True)
    await manager.start()
    yield manager
    # Teardown
    await manager.close()
    # Clean up test user data
    if os.path.exists(TEST_USER_DATA):
        try:
            shutil.rmtree(TEST_USER_DATA)
        except PermissionError:
            pass

@pytest.mark.asyncio
async def test_browser_launches():
    manager = BrowserManager(user_data_dir=TEST_USER_DATA, headless=True)
    await manager.start()
    assert manager.page is not None
    assert await manager.page.evaluate("1 + 1") == 2
    await manager.close()

@pytest.mark.asyncio
async def test_cookies_persistence():
    # 1. Start browser, set a cookie
    abs_user_data = os.path.abspath(TEST_USER_DATA)
    # SCRAPE-05: System runs in "Headed" mode (visible browser) by default.
    # We test in headed mode to ensure persistence works as expected in production configuration.
    manager1 = BrowserManager(user_data_dir=abs_user_data, headless=False)
    await manager1.start()

    # Navigate first to ensure we are on the domain
    await manager1.page.goto("https://example.com")

    # Set a test cookie with expiration (so it persists across sessions)
    # Expiry in seconds since epoch.
    import time
    expiry = int(time.time()) + 3600 # 1 hour from now

    await manager1.context.add_cookies([{
        "name": "test_cookie",
        "value": "persistent_value",
        "domain": "example.com",
        "path": "/",
        "expires": expiry
    }])

    # Verify it's set in current session
    cookies_current = await manager1.context.cookies("https://example.com")
    assert any(c["name"] == "test_cookie" for c in cookies_current), "Cookie not set in initial session"

    # Small delay to ensure flush to disk
    await asyncio.sleep(2.0)

    await manager1.close()

    # Check if directory exists and has content
    assert os.path.exists(abs_user_data)
    assert len(os.listdir(abs_user_data)) > 0, "User data directory is empty"

    # 2. Restart browser with same user_data_dir
    manager2 = BrowserManager(user_data_dir=abs_user_data, headless=False)
    await manager2.start()

    # Navigate again (cookies should be sent)
    await manager2.page.goto("https://example.com")

    # Verify cookie exists
    cookies = await manager2.context.cookies("https://example.com")
    found_cookie = next((c for c in cookies if c["name"] == "test_cookie"), None)

    assert found_cookie is not None, f"Cookie not found. Cookies: {cookies}"
    assert found_cookie["value"] == "persistent_value"

    await manager2.close()

