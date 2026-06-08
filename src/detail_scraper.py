import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.browser_manager import BrowserManager
from src.location_handler import LocationHandler

logger = logging.getLogger(__name__)


class AmazonDetailScraper:
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

        marketplace = self._normalize_marketplace(marketplace)
        url = f"https://www.{marketplace}"

        logger.info(f"Navigating to {url}...")
        await self.page.goto(url)
        await self.location_handler.check_for_captcha()

    async def set_delivery_zip(self, zip_code: str):
        """Sets the delivery zip code using the existing LocationHandler flow."""
        if not self.location_handler:
            await self.initialize()

        logger.info(f"Setting delivery zip code to {zip_code}...")
        await self.location_handler.set_location(zip_code)

    async def scrape_product(
        self,
        marketplace: str,
        zip_code: str,
        asin: Optional[str] = None,
        product_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Opens a product detail page after setting marketplace location and extracts PDP details.
        Accepts either an ASIN or a full Amazon product URL.
        """
        if not self.page:
            await self.initialize()

        marketplace = self._normalize_marketplace(marketplace)
        product_url = product_url.strip() if product_url else ""
        asin = asin.strip() if asin else ""

        if not product_url:
            if not asin:
                raise ValueError("Either asin or product_url is required.")
            product_url = f"https://www.{marketplace}/dp/{asin}"

        if not asin:
            asin = self._asin_from_url(product_url)

        logger.info(f"Opening product page: {product_url}")
        await self.page.goto(product_url, wait_until="domcontentloaded")

        try:
            await self.page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass

        await self.location_handler.check_for_captcha()
        await self._wait_for_product_shell()

        details = await self.extract_details()

        return {
            "Marketplace": marketplace,
            "Zip Code": zip_code,
            "ASIN": asin,
            "Product URL": self.page.url,
            "Title": details.get("title", ""),
            "Current Price": details.get("current_price", ""),
            "Seller Name": details.get("seller_name", ""),
            "Brand Name": details.get("brand_name", ""),
            "Rating": details.get("rating", ""),
            "Number of Reviews": details.get("number_of_reviews", ""),
            "Primary BSR Rank": details.get("primary_bsr_rank", ""),
            "Primary BSR Category": details.get("primary_bsr_category", ""),
            "All BSR Ranks": json.dumps(details.get("all_bsr_ranks", []), ensure_ascii=False),
        }

    async def extract_details(self) -> Dict[str, Any]:
        """Extracts product detail fields from the current product detail page."""
        title = await self._first_text([
            "#productTitle",
            "#title",
        ])

        current_price = await self._extract_price()
        seller_name = await self._extract_seller()
        brand_name = await self._extract_brand()
        rating = await self._extract_rating()
        number_of_reviews = await self._extract_review_count()
        bsr_ranks = await self._extract_bsr_ranks()

        primary_bsr = bsr_ranks[0] if bsr_ranks else {}

        return {
            "title": title,
            "current_price": current_price,
            "seller_name": seller_name,
            "brand_name": brand_name,
            "rating": rating,
            "number_of_reviews": number_of_reviews,
            "primary_bsr_rank": primary_bsr.get("rank", ""),
            "primary_bsr_category": primary_bsr.get("category", ""),
            "all_bsr_ranks": bsr_ranks,
        }

    async def _wait_for_product_shell(self):
        selectors = [
            "#dp",
            "#centerCol",
            "#productTitle",
            "#ppd",
            "#dp-container",
        ]

        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                return
            except PlaywrightTimeoutError:
                continue

        logger.warning("Product shell selectors were not found; attempting extraction anyway.")

    async def _extract_price(self) -> str:
        price = await self._first_text([
            "#corePrice_feature_div span.a-price span.a-offscreen",
            "#apex_desktop span.a-price span.a-offscreen",
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            "span.a-price span.a-offscreen",
        ])

        if price:
            return price

        whole = await self._first_text([
            "#corePrice_feature_div .a-price-whole",
            "#apex_desktop .a-price-whole",
        ])
        fraction = await self._first_text([
            "#corePrice_feature_div .a-price-fraction",
            "#apex_desktop .a-price-fraction",
        ])
        symbol = await self._first_text([
            "#corePrice_feature_div .a-price-symbol",
            "#apex_desktop .a-price-symbol",
        ])

        if whole:
            return f"{symbol}{whole}.{fraction}".replace("..", ".").strip()

        return ""

    async def _extract_seller(self) -> str:
        seller = await self._first_text([
            "#sellerProfileTriggerId",
            "#merchant-info a",
            "#tabular-buybox [tabular-attribute-name='Sold by'] .tabular-buybox-text",
            "#sellerInfoFeature_feature_div",
            "#offerDisplayFeature_soldBy .offer-display-feature-text",
        ])

        if seller:
            return self._clean_seller_text(seller)

        merchant_info = await self._first_text(["#merchant-info"])
        return self._clean_seller_text(merchant_info)

    async def _extract_brand(self) -> str:
        byline = await self._first_text([
            "#bylineInfo",
            "#brand",
            "#productOverview_feature_div tr:has(.po-brand) .a-span9",
        ])
        brand = self._clean_brand_text(byline)
        if brand:
            return brand

        return await self._table_value(["Brand", "Marque", "Marke", "Marca"])

    async def _extract_rating(self) -> str:
        rating = await self._first_attribute([
            "#acrPopover",
            "span[data-hook='rating-out-of-text']",
        ], "title")

        if not rating:
            rating = await self._first_text([
                "#acrPopover .a-icon-alt",
                "i[data-hook='average-star-rating'] .a-icon-alt",
                "span[data-hook='rating-out-of-text']",
            ])

        match = re.search(r"([0-9]+(?:[.,][0-9]+)?)", rating or "")
        return match.group(1).replace(",", ".") if match else (rating or "")

    async def _extract_review_count(self) -> str:
        text = await self._first_text([
            "#acrCustomerReviewText",
            "#reviewsMedley .a-link-emphasis",
            "span[data-hook='total-review-count']",
        ])

        match = re.search(r"([0-9][0-9,.\s]*)", text or "")
        return match.group(1).strip() if match else (text or "")

    async def _extract_bsr_ranks(self) -> List[Dict[str, str]]:
        texts = []

        product_info_bsr = await self._product_information_value([
            "Best Sellers Rank",
            "Best Seller Rank",
            "Bestsellers Rank",
        ])
        if product_info_bsr:
            texts.append(product_info_bsr)

        detail_bullets = await self._first_text([
            "#detailBulletsWrapper_feature_div",
            "#detailBullets_feature_div",
            "#SalesRank",
        ])
        if detail_bullets:
            texts.append(detail_bullets)

        table_rows = await self._texts_from_selectors([
            "#productDetails_detailBullets_sections1 tr",
            "#productDetails_db_sections tr",
            "#prodDetails tr",
        ])
        texts.extend(row for row in table_rows if "Best Sellers Rank" in row or "#" in row)

        combined = "\n".join(texts)
        return self._parse_bsr_text(combined)

    def _parse_bsr_text(self, text: str) -> List[Dict[str, str]]:
        if not text:
            return []

        normalized = re.sub(r"\s+", " ", text.replace("\u200e", " ")).strip()
        normalized = re.sub(r"\(See\s+Top\s+\d+\s+in\s+[^)]*\)", " ", normalized, flags=re.IGNORECASE)
        if "Best Sellers Rank" in normalized:
            normalized = normalized.split("Best Sellers Rank", 1)[1]

        pattern = re.compile(
            r"#?\s*([0-9][0-9,.\s]*)\s+in\s+([^#(]+?)(?=(?:\s*#?\s*[0-9][0-9,.\s]*\s+in\s+)|(?:\s*\()|$)",
            re.IGNORECASE,
        )

        ranks = []
        for match in pattern.finditer(normalized):
            rank = match.group(1).strip()
            category = match.group(2).strip(" -:;")
            ranks.append({"rank": rank, "category": category})

        return ranks

    async def _product_information_value(self, labels: List[str]) -> str:
        try:
            return await self.page.evaluate(
                """labels => {
                    const wanted = labels.map(label => label.toLowerCase());
                    const normalize = value => (value || '').replace(/\\s+/g, ' ').trim();
                    const nodes = Array.from(document.querySelectorAll('th, td, span, div'));

                    for (const node of nodes) {
                        const text = normalize(node.innerText);
                        if (!text) continue;
                        const lower = text.toLowerCase().replace(/:$/, '');

                        if (!wanted.includes(lower)) continue;

                        const row = node.closest('tr, li, .a-row, .a-section');
                        if (row) {
                            const rowText = normalize(row.innerText);
                            const withoutLabel = rowText.replace(new RegExp('^' + text.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '\\\\s*:?\\\\s*', 'i'), '').trim();
                            if (withoutLabel && withoutLabel !== text) return withoutLabel;

                            const cells = Array.from(row.querySelectorAll('td, th, span, div'))
                                .map(cell => normalize(cell.innerText))
                                .filter(Boolean);
                            const valueCells = cells.filter(cell => cell !== text && !wanted.includes(cell.toLowerCase().replace(/:$/, '')));
                            if (valueCells.length) return valueCells.join(' ');
                        }

                        let sibling = node.nextElementSibling;
                        while (sibling) {
                            const siblingText = normalize(sibling.innerText);
                            if (siblingText) return siblingText;
                            sibling = sibling.nextElementSibling;
                        }
                    }

                    return '';
                }""",
                labels,
            )
        except Exception:
            return ""

    async def _table_value(self, labels: List[str]) -> str:
        label_json = json.dumps([label.lower() for label in labels])
        try:
            return await self.page.evaluate(
                """labels => {
                    const wanted = new Set(labels);
                    const rows = Array.from(document.querySelectorAll('tr'));
                    for (const row of rows) {
                        const cells = Array.from(row.querySelectorAll('th, td, span'));
                        if (cells.length < 2) continue;
                        const key = (cells[0].innerText || '').trim().toLowerCase().replace(/:$/, '');
                        if (wanted.has(key)) {
                            return (cells[cells.length - 1].innerText || '').trim();
                        }
                    }
                    return '';
                }""",
                json.loads(label_json),
            )
        except Exception:
            return ""

    async def _first_text(self, selectors: List[str]) -> str:
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if not element:
                    continue
                text = await element.inner_text()
                text = self._clean_text(text)
                if text:
                    return text
            except Exception:
                continue
        return ""

    async def _first_attribute(self, selectors: List[str], attr_name: str) -> str:
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if not element:
                    continue
                value = await element.get_attribute(attr_name)
                value = self._clean_text(value or "")
                if value:
                    return value
            except Exception:
                continue
        return ""

    async def _texts_from_selectors(self, selectors: List[str]) -> List[str]:
        texts = []
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = self._clean_text(await element.inner_text())
                    if text:
                        texts.append(text)
            except Exception:
                continue
        return texts

    def _clean_seller_text(self, text: str) -> str:
        text = self._clean_text(text)
        if not text:
            return ""

        text = re.sub(r"^sold by\s+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+and\s+fulfilled\s+by\s+amazon.*$", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+ships\s+from.*$", "", text, flags=re.IGNORECASE)
        return text.strip(" .")

    def _clean_brand_text(self, text: str) -> str:
        text = self._clean_text(text)
        if not text:
            return ""

        replacements = [
            r"^visit the\s+",
            r"\s+store$",
            r"^brand:\s*",
            r"^by\s+",
        ]
        for pattern in replacements:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

        return text

    def _asin_from_url(self, product_url: str) -> str:
        path = urlparse(product_url).path
        match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", path, re.IGNORECASE)
        return match.group(1).upper() if match else ""

    def _normalize_marketplace(self, marketplace: str) -> str:
        marketplace = (marketplace or "amazon.com").lower().strip()
        marketplace = marketplace.replace("https://", "").replace("http://", "")
        marketplace = marketplace.replace("www.", "").strip("/")

        if not marketplace.startswith("amazon."):
            marketplace = f"amazon.{marketplace}"

        return marketplace

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    async def close(self):
        await self.browser_manager.close()
