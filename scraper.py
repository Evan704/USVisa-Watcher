# scraper.py
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from playwright.async_api import async_playwright, Response

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

            # Store API response data
            api_responses: list[Response] = []

            def handle_response(response: Response):
                """Intercept Supabase slot_data API responses."""
                if "slot_data" in response.url or self.SUPABASE_URL in response.url:
                    logger.debug(f"Intercepted Supabase API call: {response.url}")
                    api_responses.append(response)

            page = await context.new_page()
            page.on("response", handle_response)

            try:
                logger.info(f"Navigating to {self.settings.qmq_url}")
                await page.goto(self.settings.qmq_url, wait_until="networkidle")

                # Wait for JavaScript to load and make API calls
                await page.wait_for_timeout(5000)

                # Process intercepted API responses
                api_data = {}
                for response in api_responses:
                    try:
                        # Check if response is OK and has JSON content
                        if response.status == 200:
                            body = await response.body()
                            try:
                                api_data[response.url] = json.loads(body)
                            except json.JSONDecodeError:
                                logger.debug(f"Response body is not JSON: {response.url}")
                    except Exception as e:
                        logger.debug(f"Failed to process API response: {e}")

                # Try to extract data from intercepted Supabase API calls
                appointment_data = self._extract_from_api_data(api_data)

                if appointment_data:
                    self.appointment_info = appointment_data
                    return appointment_data

                # Log fallback and return None instead of doing unreliable page extraction
                logger.warning(
                    "API interception failed; no appointment data extracted. "
                    "Consider retrying or checking if qmq.app structure has changed."
                )
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
        for data in api_data.values():
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
        # Check city_key field (e.g., "cnBEI" for Beijing)
        city_key = item.get("city_key", "").lower()

        # Check visa_class in attrs (e.g., "F-1 Student • Other Student")
        data = item.get("data", {})
        attrs = data.get("attrs", {})
        visa_class = attrs.get("visa_class", "").lower()
        visa_type = attrs.get("visa_type", "").lower()

        # Beijing is "cnBEI", F-1 should be in visa_class
        beijing_codes = ["cnbei", "beijing", "北京"]
        is_beijing = any(code in city_key for code in beijing_codes)
        is_f1 = "f-1" in visa_class or "f-1" in visa_type
        is_other_student = "other" in visa_class

        return is_beijing and is_f1 and is_other_student

    def _extract_from_item(self, item: dict) -> Optional[AppointmentInfo]:
        """Extract earliest appointment date from a matching item."""
        try:
            # Get slots from data
            data = item.get("data", {})
            slots = data.get("slots", {})

            if slots:
                # slots is a dict with date strings as keys
                dates = list(slots.keys())
                if dates:
                    # Parse all dates and find the earliest
                    parsed_dates = []
                    for date_str in dates:
                        parsed = self._parse_date(date_str)
                        if parsed:
                            parsed_dates.append(parsed)

                    if parsed_dates:
                        earliest_date = min(parsed_dates)
                        return AppointmentInfo(
                            city=self.settings.city,
                            visa_type=self.settings.visa_type,
                            visa_category=self.settings.visa_category,
                            available_date=earliest_date,
                            raw_data=item,
                        )

            # Fallback: try direct date fields
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

