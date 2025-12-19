"""
Main flight monitoring orchestrator
"""
import logging
import sys
import os
from typing import List, Dict
from datetime import datetime

from config import Config
from database import FlightDatabase
from flight_scraper import FlightScraper, AlternativeFlightSearcher
from notifications import NotificationService

# Ensure logs directory exists
os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class FlightMonitor:
    """Main flight price monitoring system"""

    def __init__(self):
        """Initialize the flight monitor"""
        # Validate configuration
        errors = Config.validate_config()
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            raise ValueError("Invalid configuration. Check .env file.")

        # Initialize components
        self.db = FlightDatabase(Config.DATABASE_PATH)
        self.scraper = FlightScraper(Config.SERPAPI_KEY)
        self.searcher = AlternativeFlightSearcher()

        # Initialize notification service
        email_config = {
            'enabled': Config.EMAIL_ENABLED,
            'from': Config.EMAIL_FROM,
            'to': Config.EMAIL_TO,
            'password': Config.EMAIL_PASSWORD,
            'smtp_server': Config.SMTP_SERVER,
            'smtp_port': Config.SMTP_PORT
        } if Config.EMAIL_ENABLED else None

        sms_config = {
            'enabled': Config.SMS_ENABLED,
            'account_sid': Config.TWILIO_ACCOUNT_SID,
            'auth_token': Config.TWILIO_AUTH_TOKEN,
            'from_number': Config.TWILIO_FROM_NUMBER,
            'to_number': Config.TWILIO_TO_NUMBER
        } if Config.SMS_ENABLED else None

        self.notifier = NotificationService(email_config, sms_config)

        logger.info("Flight Monitor initialized successfully")

    def run_search(self) -> List[Dict]:
        """
        Execute a complete flight search cycle
        Returns list of all flights found
        """
        logger.info("=" * 60)
        logger.info("Starting flight search cycle")
        logger.info("=" * 60)

        all_flights = []

        # Get date ranges for flexible search
        departure_dates = Config.get_date_range(
            Config.DEPARTURE_DATE,
            Config.DATE_FLEXIBILITY
        )
        return_dates = Config.get_date_range(
            Config.RETURN_DATE,
            Config.DATE_FLEXIBILITY
        )

        logger.info(f"Searching {len(departure_dates)} departure dates and {len(return_dates)} return dates")
        logger.info(f"Destinations: {', '.join(Config.DESTINATION_AIRPORTS)}")

        # 1. Search direct flights to all destination airports
        logger.info("\n--- Direct Flight Search ---")
        direct_flights = self.searcher.search_nearby_airports(
            self.scraper,
            Config.ORIGIN_AIRPORT,
            Config.DESTINATION_AIRPORTS,
            Config.DEPARTURE_DATE,
            Config.RETURN_DATE,
            Config.CURRENCY
        )

        if direct_flights:
            logger.info(f"Found {len(direct_flights)} direct flight options")
            all_flights.extend(direct_flights)
        else:
            logger.warning("No direct flights found")

        # 2. Search flexible dates (if we have direct flights, focus on best routes)
        if direct_flights:
            logger.info("\n--- Flexible Date Search ---")
            # Get the cheapest destination
            best_dest = min(direct_flights, key=lambda x: x['price'])['destination']
            logger.info(f"Searching flexible dates for best destination: {best_dest}")

            flexible_flights = self.searcher.search_flexible_dates(
                self.scraper,
                Config.ORIGIN_AIRPORT,
                best_dest,
                departure_dates[:3],  # Limit to avoid too many requests
                return_dates[:3],
                Config.CURRENCY
            )

            if flexible_flights:
                logger.info(f"Found {len(flexible_flights)} flights with flexible dates")
                all_flights.extend(flexible_flights)

        # 3. Search multi-leg options if enabled
        if Config.ENABLE_MULTI_LEG_SEARCH:
            logger.info("\n--- Multi-Leg Search ---")
            for destination in Config.DESTINATION_AIRPORTS:
                multi_leg_flights = self.scraper.search_multi_leg(
                    Config.ORIGIN_AIRPORT,
                    Config.EU_HUB_AIRPORTS,
                    destination,
                    Config.DEPARTURE_DATE,
                    Config.RETURN_DATE,
                    Config.CURRENCY
                )

                if multi_leg_flights:
                    logger.info(f"Found {len(multi_leg_flights)} multi-leg options to {destination}")
                    all_flights.extend(multi_leg_flights)

        logger.info(f"\n{'=' * 60}")
        logger.info(f"Total flights found: {len(all_flights)}")
        logger.info(f"{'=' * 60}\n")

        return all_flights

    def process_flights(self, flights: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Process found flights and categorize them

        Returns:
            Dictionary with categories: 'deals', 'price_drops', 'new_lows'
        """
        deals = []
        price_drops = []
        new_lows = []

        for flight in flights:
            # Save to database
            try:
                flight_id = self.db.save_flight_price(flight)
                flight['id'] = flight_id
            except Exception as e:
                logger.error(f"Failed to save flight: {e}")
                continue

            # Check if it's a deal (below max price)
            if flight['price'] <= Config.MAX_PRICE:
                deals.append(flight)

                # Check if it's a new low price for this route
                previous_low = self.db.get_lowest_price(
                    flight['origin'],
                    flight['destination'],
                    flight['departure_date']
                )

                if previous_low and flight['price'] < previous_low - Config.PRICE_DROP_THRESHOLD:
                    price_drops.append(flight)

                if previous_low is None or flight['price'] < previous_low:
                    new_lows.append(flight)

        logger.info(f"Categorized flights:")
        logger.info(f"  - Deals (≤${Config.MAX_PRICE}): {len(deals)}")
        logger.info(f"  - Significant price drops: {len(price_drops)}")
        logger.info(f"  - New low prices: {len(new_lows)}")

        return {
            'deals': deals,
            'price_drops': price_drops,
            'new_lows': new_lows
        }

    def send_alerts(self, categorized_flights: Dict[str, List[Dict]]):
        """Send notifications for flight deals"""
        # Get unnotified deals
        unnotified = self.db.get_unnotified_deals(Config.MAX_PRICE)

        if not unnotified:
            logger.info("No new deals to notify")
            return

        logger.info(f"Sending alerts for {len(unnotified)} new deals")

        # Determine alert type
        if categorized_flights['new_lows']:
            alert_type = 'new_low'
        elif categorized_flights['price_drops']:
            alert_type = 'price_drop'
        else:
            alert_type = 'deal'

        # Send notification
        try:
            self.notifier.send_flight_alert(unnotified, alert_type)

            # Mark flights as notified
            for flight in unnotified:
                self.db.mark_as_notified(flight['id'])

            logger.info("Alerts sent successfully")

        except Exception as e:
            logger.error(f"Failed to send alerts: {e}")

    def run_monitoring_cycle(self):
        """Execute one complete monitoring cycle"""
        try:
            logger.info(f"\n{'#' * 60}")
            logger.info(f"# Flight Monitoring Cycle - {datetime.now()}")
            logger.info(f"{'#' * 60}\n")

            # Search for flights
            flights = self.run_search()

            if not flights:
                logger.warning("No flights found in this cycle")
                return

            # Process and categorize flights
            categorized = self.process_flights(flights)

            # Display summary
            if categorized['deals']:
                logger.info("\n🎉 DEALS FOUND!")
                for flight in sorted(categorized['deals'], key=lambda x: x['price'])[:5]:
                    logger.info(
                        f"  ${flight['price']:.0f} - {flight['origin']} → {flight['destination']} "
                        f"({flight['departure_date']})"
                    )

            # Send alerts
            self.send_alerts(categorized)

            # Cleanup old data (keep last 30 days)
            self.db.cleanup_old_data(30)

            logger.info("\n✅ Monitoring cycle completed successfully\n")

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}", exc_info=True)

    def get_best_current_deals(self, limit: int = 10) -> List[Dict]:
        """Get the best current deals from database"""
        return self.db.get_recent_deals(Config.MAX_PRICE, limit)

    def print_summary(self):
        """Print a summary of current deals"""
        deals = self.get_best_current_deals()

        if not deals:
            print("\n📭 No deals found yet. Keep monitoring!")
            return

        print("\n" + "=" * 70)
        print("✈️  BEST CURRENT DEALS")
        print("=" * 70)

        for i, deal in enumerate(deals, 1):
            route = f"{deal['origin']} → {deal['destination']}"
            price = f"${deal['price']:.0f}"
            date = deal['departure_date']
            airline = deal.get('airline', 'Unknown')
            stops = deal.get('stops', 0)
            stops_text = "Direct" if stops == 0 else f"{stops} stop(s)"

            print(f"\n{i}. {route}")
            print(f"   Price: {price} | Date: {date}")
            print(f"   Airline: {airline} | {stops_text}")

            if deal.get('is_multi_leg'):
                print(f"   Multi-leg: {deal.get('leg_details', 'Yes')}")

        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point"""
    try:
        monitor = FlightMonitor()

        # Run one monitoring cycle
        monitor.run_monitoring_cycle()

        # Print summary
        monitor.print_summary()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
