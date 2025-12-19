"""
Scheduling system for continuous flight monitoring
"""
import schedule
import time
import logging
import sys
from datetime import datetime

from flight_monitor import FlightMonitor
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class FlightScheduler:
    """Schedules and runs periodic flight monitoring"""

    def __init__(self):
        self.monitor = FlightMonitor()
        self.running = False

    def run_scheduled_check(self):
        """Execute scheduled monitoring cycle"""
        try:
            logger.info("⏰ Scheduled check triggered")
            self.monitor.run_monitoring_cycle()
        except Exception as e:
            logger.error(f"Scheduled check failed: {e}", exc_info=True)

    def start_continuous_monitoring(self):
        """Start continuous monitoring with scheduled checks"""
        logger.info("=" * 70)
        logger.info("🚀 Starting Flight Price Monitor")
        logger.info("=" * 70)
        logger.info(f"Check interval: Every {Config.CHECK_INTERVAL_HOURS} hour(s)")
        logger.info(f"Origin: {Config.ORIGIN_AIRPORT}")
        logger.info(f"Destinations: {', '.join(Config.DESTINATION_AIRPORTS)}")
        logger.info(f"Departure: {Config.DEPARTURE_DATE} (±{Config.DATE_FLEXIBILITY} days)")
        logger.info(f"Return: {Config.RETURN_DATE} (±{Config.DATE_FLEXIBILITY} days)")
        logger.info(f"Max Price: ${Config.MAX_PRICE} {Config.CURRENCY}")
        logger.info(f"Multi-leg search: {'Enabled' if Config.ENABLE_MULTI_LEG_SEARCH else 'Disabled'}")
        logger.info("=" * 70 + "\n")

        # Run initial check immediately
        logger.info("Running initial check...")
        self.run_scheduled_check()

        # Schedule periodic checks
        schedule.every(Config.CHECK_INTERVAL_HOURS).hours.do(self.run_scheduled_check)

        logger.info(f"\n✅ Monitoring started. Next check in {Config.CHECK_INTERVAL_HOURS} hour(s)")
        logger.info("Press Ctrl+C to stop\n")

        # Keep running
        self.running = True
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for scheduled tasks
        except KeyboardInterrupt:
            logger.info("\n\n⏹️  Monitoring stopped by user")
            self.stop()

    def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Flight monitor shutdown complete")


def main():
    """Main entry point for scheduled monitoring"""
    try:
        scheduler = FlightScheduler()
        scheduler.start_continuous_monitoring()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
