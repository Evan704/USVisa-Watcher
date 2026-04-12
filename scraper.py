# scraper.py
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Page, Response

if TYPE_CHECKING:
    from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class AppointmentInfo:
    """Represents a visa appointment slot."""
    city: str
    visa_type: str
    visa_category: str
    available_date: date
    raw_data: Optional[dict] = None

    def is_earlier_than(self, target_date: date) -> bool:
        """Check if this appointment is earlier than the target date."""
        return self.available_date < target_date

    def __str__(self) -> str:
        return f"{self.city} {self.visa_type} ({self.visa_category}): {self.available_date}"


class VisaScraper:
    """Scraper for qmq.app visa appointment information."""

    # Supabase slot_data API endpoint
    SUPABASE_URL = "https://sdetncywjtheyqwfzshc.supabase.co/rest/v1/slot_data"

    def __init__(self, settings: "Settings"):
        self.settings = settings
        self.appointment_info: Optional[AppointmentInfo] = None

    async def fetch_appointment(self) -> Optional[AppointmentInfo]:
        """
        Fetch the latest appointment information from qmq.app.
        Uses Playwright to intercept Supabase API calls for slot_data.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0"
            )

            # Store API responses
            api_data = {}

            def handle_response(response: Response):
                """Intercept and store Supabase slot_data API responses."""
                url = response.url
                if "slot_data" in url or self.SUPABASE_URL in url:
                    logger.debug(f"Intercepted Supabase API call: {url}")
                    try:
                        api_data[url] = response.json()
                    except Exception as e:
                        logger.debug(f"Failed to parse API response: {e}")

            page = await context.new_page()
            page.on("response", handle_response)

            try:
                logger.info(f"Navigating to {self.settings.qmq_url}")
                await page.goto(self.settings.qmq_url, wait_until="networkidle")

                # Wait for JavaScript to load and make API calls
                await page.wait_for_timeout(3000)

                # Try to extract data from intercepted Supabase API calls
                appointment_data = self._extract_from_api_data(api_data)

                if appointment_data:
                    self.appointment_info = appointment_data
                    return appointment_data

                # Fallback: try to extract from page content
                logger.warning("API interception failed, falling back to page extraction")
                appointment_data = await self._extract_from_page(page)
                if appointment_data:
                    self.appointment_info = appointment_data
                    return appointment_data

                logger.warning("Could not extract appointment data")
                return None

            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                return None

            finally:
                await context.close()
                await browser.close()

    def _extract_from_api_data(
        self, api_data: dict
    ) -> Optional[AppointmentInfo]:
        """Extract appointment info from intercepted Supabase API responses."""
        for url, data in api_data.items():
            result = self._parse_appointment_data(data)
            if result:
                return result
        return None

    def _parse_appointment_data(self, data: dict) -> Optional[AppointmentInfo]:
        """Parse Supabase slot_data API response to find Beijing F-1 Other Student appointment."""
        try:
            # Supabase returns a list of slot records
            if isinstance(data, list):
                for item in data:
                    if self._matches_target(item):
                        return self._extract_from_item(item)

            elif isinstance(data, dict):
                # Try common response structures
                if "data" in data:
                    return self._parse_appointment_data(data["data"])
                if "records" in data:
                    return self._parse_appointment_data(data["records"])
                if self._matches_target(data):
                    return self._extract_from_item(data)

        except Exception as e:
            logger.debug(f"Failed to parse data: {e}")

        return None

    def _matches_target(self, item: dict) -> bool:
        """Check if the item matches our target city, type, and category."""
        city = item.get("city", "").lower()
        visa_type = item.get("visa_type", item.get("type", "")).lower()
        category = item.get("category", item.get("visa_category", "")).lower()

        return (
            self.settings.city.lower() in city
            and self.settings.visa_type.lower() in visa_type
            and "student" in category
        )

    def _extract_from_item(self, item: dict) -> Optional[AppointmentInfo]:
        """Extract appointment date from a matching item."""
        try:
            # Try different possible field names for the date
            date_str = (
                item.get("earliest_date")
                or item.get("available_date")
                or item.get("date")
                or item.get("first_available")
                or item.get("appointment_date")
            )

            if date_str:
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return AppointmentInfo(
                        city=self.settings.city,
                        visa_type=self.settings.visa_type,
                        visa_category=self.settings.visa_category,
                        available_date=parsed_date,
                        raw_data=item,
                    )
        except Exception as e:
            logger.debug(f"Failed to extract from item: {e}")

        return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string in various formats."""
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%Y年%m月%d日",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        # Try ISO format as fallback
        try:
            return date.fromisoformat(date_str.strip())
        except ValueError:
            pass

        logger.warning(f"Could not parse date: {date_str}")
        return None

    async def _extract_from_page(self, page: Page) -> Optional[AppointmentInfo]:
        """Fallback: Extract data directly from page DOM using regex."""
        try:
            # Look for date patterns in the page text
            content = await page.content()

            # Look for Beijing F-1 Other Student section
            # This is a heuristic approach - adjust based on actual page structure
            beijing_pattern = re.compile(
                r"北京.*?F-1.*?Other Student.*?(\d{4}-\d{2}-\d{2})",
                re.IGNORECASE | re.DOTALL,
            )
            match = beijing_pattern.search(content)

            if match:
                parsed_date = self._parse_date(match.group(1))
                if parsed_date:
                    return AppointmentInfo(
                        city=self.settings.city,
                        visa_type=self.settings.visa_type,
                        visa_category=self.settings.visa_category,
                        available_date=parsed_date,
                    )

            # Try to find any date on the page
            date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
            dates = date_pattern.findall(content)
            if dates:
                # Use the earliest date found
                parsed_dates = [self._parse_date(d) for d in dates]
                parsed_dates = [d for d in parsed_dates if d]
                if parsed_dates:
                    earliest = min(parsed_dates)
                    return AppointmentInfo(
                        city=self.settings.city,
                        visa_type=self.settings.visa_type,
                        visa_category=self.settings.visa_category,
                        available_date=earliest,
                    )

        except Exception as e:
            logger.debug(f"Failed to extract from page: {e}")

        return None
