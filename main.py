# main.py
import argparse
import asyncio
import logging
import sys
from datetime import date
from typing import Optional

from config import get_settings
from notifier import EmailNotifier
from scraper import VisaScraper, AppointmentInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def check_and_notify() -> bool:
    """
    Check for visa appointments and send notification if earlier date found.
    Returns True if notification was sent, False otherwise.
    """
    settings = get_settings()

    logger.info(
        f"Checking for {settings.city} {settings.visa_type} ({settings.visa_category}) "
        f"appointments before {settings.target_date}"
    )

    # Fetch appointment data
    scraper = VisaScraper(settings)
    appointment: Optional[AppointmentInfo] = await scraper.fetch_appointment()

    if not appointment:
        logger.warning("Could not fetch appointment data")
        return False

    logger.info(f"Found earliest appointment: {appointment.available_date}")

    # Check if this is earlier than target date
    if appointment.is_earlier_than(settings.target_date):
        logger.info(
            f"Appointment date {appointment.available_date} is earlier than "
            f"target {settings.target_date} - sending notification"
        )

        notifier = EmailNotifier(settings)
        success = notifier.send_notification(appointment.available_date)

        if success:
            logger.info("Notification sent successfully")
        else:
            logger.error("Failed to send notification")

        return success
    else:
        logger.info(
            f"Appointment date {appointment.available_date} is not earlier than "
            f"target {settings.target_date} - no notification needed"
        )
        return False


async def run_loop():
    """Run the check in a continuous loop."""
    settings = get_settings()
    interval = settings.check_interval_minutes * 60  # Convert to seconds

    logger.info(f"Starting continuous check loop (interval: {settings.check_interval_minutes} minutes)")

    while True:
        try:
            await check_and_notify()
        except Exception as e:
            logger.error(f"Error in check loop: {e}")

        logger.info(f"Sleeping for {settings.check_interval_minutes} minutes...")
        await asyncio.sleep(interval)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor US visa appointment availability on qmq.app"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run in continuous loop mode",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (default behavior)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.loop:
            asyncio.run(run_loop())
        else:
            success = asyncio.run(check_and_notify())
            sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
