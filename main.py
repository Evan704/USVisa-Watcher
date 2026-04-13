# main.py
import argparse
import asyncio
import logging
import os
import sys
from datetime import date
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import get_settings
from notifier import EmailNotifier
from scraper import VisaScraper, AppointmentInfo


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging with both console and file handlers."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler with rotation (10MB per file, keep 5 backups)
            RotatingFileHandler(
                logs_dir / "usvisa-watcher.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            ),
        ],
    )

    return logging.getLogger(__name__)


# Will be configured in main()
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
        description="USVisa-Watcher: Monitor US visa appointment availability on qmq.app"
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

    # Setup logging with file output
    global logger
    logger = setup_logging(verbose=args.verbose)

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
