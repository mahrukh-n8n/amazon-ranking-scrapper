import pytest
from unittest.mock import AsyncMock, MagicMock
from src.scraper import AmazonScraper

@pytest.fixture
def mock_browser_manager():
    manager = MagicMock()
    manager.page = AsyncMock()
    manager.start = AsyncMock()
    manager.close = AsyncMock()
    return manager

@pytest.mark.asyncio
async def test_search_keyword(mock_browser_manager):
    scraper = AmazonScraper(mock_browser_manager)
    await scraper.initialize()

    # Mock search box interactions
    scraper.page.wait_for_selector = AsyncMock()
    scraper.page.fill = AsyncMock()
    scraper.page.type = AsyncMock()
    scraper.page.press = AsyncMock()
    scraper.page.click = AsyncMock()
    scraper.page.wait_for_load_state = AsyncMock()
    scraper.page.title = AsyncMock(return_value="Amazon.com : keyword")
    scraper.page.is_visible = AsyncMock(return_value=False) # No captcha

    await scraper.search_keyword("test keyword")

    # Verify calls matching new implementation
    scraper.page.fill.assert_called_with("#twotabsearchtextbox", "")
    scraper.page.type.assert_called_with("#twotabsearchtextbox", "test keyword", delay=50)
    scraper.page.press.assert_called_with("#twotabsearchtextbox", "Enter")

@pytest.mark.asyncio
async def test_find_asins_ranks_found(mock_browser_manager):
    scraper = AmazonScraper(mock_browser_manager)
    await scraper.initialize()

    # Mock elements
    result_1 = AsyncMock()
    result_1.get_attribute.return_value = "ASIN1"

    result_2 = AsyncMock()
    result_2.get_attribute.return_value = "ASIN2" # Target

    result_3 = AsyncMock()
    result_3.get_attribute.return_value = "ASIN3"

    scraper.page.wait_for_selector = AsyncMock()
    scraper.page.query_selector_all = AsyncMock(return_value=[result_1, result_2, result_3])

    results = await scraper.find_asins_ranks(["ASIN2"])
    result = results[0]

    assert result["found"] is True
    assert result["rank"] == 2
    assert result["page"] == 1

@pytest.mark.asyncio
async def test_find_asins_ranks_not_found(mock_browser_manager):
    scraper = AmazonScraper(mock_browser_manager)
    await scraper.initialize()

    # Mock elements
    result_1 = AsyncMock()
    result_1.get_attribute.return_value = "ASIN1"

    scraper.page.wait_for_selector = AsyncMock()
    scraper.page.query_selector_all = AsyncMock(return_value=[result_1])

    results = await scraper.find_asins_ranks(["ASIN99"])
    result = results[0]

    assert result["found"] is False
    assert result["rank"] == -1
