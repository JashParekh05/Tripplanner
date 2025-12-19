"""
Flight data collection service with multiple data sources
"""
import requests
import logging
import time
import os
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlencode
from .api_integrations import SkyscannerAPI, KayakAPI, MultiSourceFlightSearcher

logger = logging.getLogger(__name__)

class FlightScraper:
    """Collects flight price data from multiple sources"""

    def __init__(self, serpapi_key: Optional[str] = None):
        self.serpapi_key = serpapi_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Initialize multi-source searcher
        self.multi_source = MultiSourceFlightSearcher(
            serpapi_key=serpapi_key,
            skyscanner_key=os.getenv('SKYSCANNER_API_KEY'),
            kayak_key=os.getenv('KAYAK_API_KEY')
        )

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Search for flights using available data sources
        Returns list of flight options with prices
        """
        flights = []

        # Try SerpAPI first (most reliable)
        if self.serpapi_key:
            try:
                flights.extend(self._search_serpapi(
                    origin, destination, departure_date, return_date, currency
                ))
                logger.info(f"SerpAPI found {len(flights)} flights")
            except Exception as e:
                logger.error(f"SerpAPI search failed: {e}")

        # Use multi-source searcher to get results from Skyscanner and Kayak
        try:
            additional_flights = self.multi_source.search_all_sources(
                origin, destination, departure_date, return_date, currency
            )
            flights.extend(additional_flights)
            logger.info(f"Multi-source search found {len(additional_flights)} additional flights")
        except Exception as e:
            logger.error(f"Multi-source search failed: {e}")

        # Mark data source for SerpAPI flights
        for flight in flights:
            if 'data_source' not in flight:
                flight['data_source'] = 'serpapi'

        return flights

    def _search_serpapi(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        currency: str
    ) -> List[Dict]:
        """Search using SerpAPI (Google Flights)"""
        params = {
            'engine': 'google_flights',
            'departure_id': origin,
            'arrival_id': destination,
            'outbound_date': departure_date,
            'currency': currency,
            'hl': 'en',
            'api_key': self.serpapi_key
        }

        if return_date:
            params['return_date'] = return_date
            params['type'] = '1'  # Round trip
        else:
            params['type'] = '2'  # One way

        try:
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            flights = []

            # Parse best flights
            if 'best_flights' in data:
                for flight in data['best_flights']:
                    flights.append(self._parse_serpapi_flight(
                        flight, origin, destination, departure_date, return_date, currency
                    ))

            # Parse other flights
            if 'other_flights' in data:
                for flight in data['other_flights']:
                    flights.append(self._parse_serpapi_flight(
                        flight, origin, destination, departure_date, return_date, currency
                    ))

            return flights

        except Exception as e:
            logger.error(f"SerpAPI error: {e}")
            return []

    def _parse_serpapi_flight(
        self,
        flight_data: Dict,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        currency: str
    ) -> Dict:
        """Parse SerpAPI flight data into standard format"""
        # Extract price
        price = flight_data.get('price', 0)
        if isinstance(price, dict):
            price = price.get('value', 0)

        # Extract airline
        flights_info = flight_data.get('flights', [])
        airline = flights_info[0].get('airline') if flights_info else 'Unknown'

        # Count stops
        stops = len(flights_info) - 1 if flights_info else 0

        return {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'return_date': return_date,
            'price': float(price),
            'currency': currency,
            'airline': airline,
            'stops': stops,
            'url': flight_data.get('booking_token', ''),
            'is_multi_leg': False,
            'leg_details': None
        }

    def _search_kayak(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str]
    ) -> List[Dict]:
        """
        Search Kayak for flight prices
        Note: This is a simplified implementation. Real scraping would need more robust handling.
        """
        # Build Kayak search URL
        trip_type = 'roundtrip' if return_date else 'oneway'

        # Convert date format from YYYY-MM-DD to YYYY-MM-DD
        dep_date = departure_date.replace('-', '')
        ret_date = return_date.replace('-', '') if return_date else ''

        if return_date:
            url = f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}/{return_date}"
        else:
            url = f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}"

        try:
            # Note: This is a placeholder. Real implementation would need:
            # 1. Selenium for JavaScript rendering
            # 2. BeautifulSoup for parsing
            # 3. Handling of anti-bot measures

            logger.info(f"Would scrape Kayak URL: {url}")

            # For now, return empty list
            # In production, you'd use Selenium here
            return []

        except Exception as e:
            logger.error(f"Kayak scraping error: {e}")
            return []

    def _search_google_flights_api(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str]
    ) -> List[Dict]:
        """
        Alternative Google Flights search method
        This is a placeholder for direct API access or advanced scraping
        """
        logger.info("Google Flights direct search not implemented yet")
        return []

    def search_multi_leg(
        self,
        origin: str,
        hub_airports: List[str],
        final_destination: str,
        departure_date: str,
        return_date: Optional[str],
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Search for multi-leg journeys (e.g., ATL -> London -> Madrid)
        This can find cheaper combinations
        """
        multi_leg_options = []

        for hub in hub_airports:
            try:
                # Search first leg: origin to hub
                leg1_flights = self.search_flights(
                    origin, hub, departure_date, None, currency
                )

                if not leg1_flights:
                    continue

                # Get cheapest first leg
                leg1_cheapest = min(leg1_flights, key=lambda x: x['price'])

                # Search second leg: hub to final destination
                # Add a day for connection time
                from datetime import datetime, timedelta
                dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
                leg2_date = (dep_date + timedelta(days=1)).strftime('%Y-%m-%d')

                leg2_flights = self.search_flights(
                    hub, final_destination, leg2_date, None, currency
                )

                if not leg2_flights:
                    continue

                leg2_cheapest = min(leg2_flights, key=lambda x: x['price'])

                # Combine the legs
                total_price = leg1_cheapest['price'] + leg2_cheapest['price']

                multi_leg_options.append({
                    'origin': origin,
                    'destination': final_destination,
                    'departure_date': departure_date,
                    'return_date': return_date,
                    'price': total_price,
                    'currency': currency,
                    'airline': f"{leg1_cheapest['airline']} + {leg2_cheapest['airline']}",
                    'stops': leg1_cheapest['stops'] + leg2_cheapest['stops'] + 1,
                    'url': f"Multi-leg via {hub}",
                    'is_multi_leg': True,
                    'leg_details': f"Leg 1: {origin}-{hub} ${leg1_cheapest['price']}, Leg 2: {hub}-{final_destination} ${leg2_cheapest['price']}"
                })

                logger.info(f"Multi-leg option via {hub}: ${total_price}")

            except Exception as e:
                logger.error(f"Multi-leg search via {hub} failed: {e}")
                continue

        return multi_leg_options


class AlternativeFlightSearcher:
    """
    Additional flight search strategies for finding the cheapest options
    """

    @staticmethod
    def search_nearby_airports(
        scraper: FlightScraper,
        origin: str,
        destination_airports: List[str],
        departure_date: str,
        return_date: Optional[str],
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Search multiple destination airports to find cheapest option
        """
        all_flights = []

        for dest in destination_airports:
            try:
                flights = scraper.search_flights(
                    origin, dest, departure_date, return_date, currency
                )
                all_flights.extend(flights)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Search to {dest} failed: {e}")

        return all_flights

    @staticmethod
    def search_flexible_dates(
        scraper: FlightScraper,
        origin: str,
        destination: str,
        departure_dates: List[str],
        return_dates: List[str],
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Search across multiple date combinations
        """
        all_flights = []

        for dep_date in departure_dates:
            for ret_date in return_dates:
                try:
                    flights = scraper.search_flights(
                        origin, destination, dep_date, ret_date, currency
                    )
                    all_flights.extend(flights)
                    time.sleep(2)  # Rate limiting
                except Exception as e:
                    logger.error(f"Search for {dep_date}-{ret_date} failed: {e}")

        return all_flights
