"""
Additional API integrations for flight data
Skyscanner and Kayak API clients
"""
import requests
import logging
import time
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SkyscannerAPI:
    """
    Skyscanner Flight Search API Integration
    Uses RapidAPI Skyscanner endpoint
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SKYSCANNER_API_KEY')
        self.base_url = "https://skyscanner-api.p.rapidapi.com/v3"
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': 'skyscanner-api.p.rapidapi.com',
            'Content-Type': 'application/json'
        }

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        currency: str = 'USD',
        adults: int = 1
    ) -> List[Dict]:
        """
        Search for flights using Skyscanner API
        """
        if not self.api_key:
            logger.warning("Skyscanner API key not configured")
            return []

        try:
            # Format dates for Skyscanner (YYYY-MM-DD)
            trip_type = 'return' if return_date else 'oneway'

            # Create search request
            search_params = {
                'query': {
                    'market': 'US',
                    'locale': 'en-US',
                    'currency': currency,
                    'queryLegs': [
                        {
                            'originPlaceId': {'iata': origin},
                            'destinationPlaceId': {'iata': destination},
                            'date': {'year': int(departure_date[:4]), 'month': int(departure_date[5:7]), 'day': int(departure_date[8:10])}
                        }
                    ],
                    'adults': adults,
                    'cabinClass': 'CABIN_CLASS_ECONOMY'
                }
            }

            # Add return leg if round trip
            if return_date:
                search_params['query']['queryLegs'].append({
                    'originPlaceId': {'iata': destination},
                    'destinationPlaceId': {'iata': origin},
                    'date': {'year': int(return_date[:4]), 'month': int(return_date[5:7]), 'day': int(return_date[8:10])}
                })

            # Create search session
            response = requests.post(
                f"{self.base_url}/flights/live/search/create",
                json=search_params,
                headers=self.headers,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"Skyscanner API error: {response.status_code} - {response.text}")
                return []

            data = response.json()
            session_token = data.get('sessionToken')

            if not session_token:
                logger.error("No session token received from Skyscanner")
                return []

            # Poll for results
            time.sleep(2)  # Wait for results to be ready

            poll_response = requests.post(
                f"{self.base_url}/flights/live/search/poll/{session_token}",
                json={},
                headers=self.headers,
                timeout=30
            )

            if poll_response.status_code != 200:
                logger.error(f"Skyscanner poll error: {poll_response.status_code}")
                return []

            results = poll_response.json()
            flights = self._parse_skyscanner_results(results, origin, destination, departure_date, return_date, currency)

            logger.info(f"Skyscanner found {len(flights)} flights from {origin} to {destination}")
            return flights

        except Exception as e:
            logger.error(f"Skyscanner API error: {e}")
            return []

    def _parse_skyscanner_results(
        self,
        results: Dict,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        currency: str
    ) -> List[Dict]:
        """Parse Skyscanner API response into standard format"""
        flights = []

        try:
            content = results.get('content', {})
            itineraries = content.get('results', {}).get('itineraries', {})

            for itinerary_id, itinerary in itineraries.items():
                pricing_options = itinerary.get('pricingOptions', [])

                if pricing_options:
                    # Get cheapest option
                    cheapest = min(pricing_options, key=lambda x: x.get('price', {}).get('amount', float('inf')))
                    price_info = cheapest.get('price', {})
                    price = price_info.get('amount', 0)

                    # Get leg information
                    leg_ids = itinerary.get('legIds', [])
                    legs = content.get('results', {}).get('legs', {})

                    # Extract airline and stops from first leg
                    airline = 'Unknown'
                    stops = 0

                    if leg_ids and legs:
                        first_leg = legs.get(leg_ids[0], {})
                        carriers = first_leg.get('carriers', {}).get('marketing', [])
                        if carriers:
                            carrier_id = carriers[0].get('id')
                            # Get airline name from carriers dict
                            all_carriers = content.get('results', {}).get('carriers', {})
                            if carrier_id and carrier_id in all_carriers:
                                airline = all_carriers[carrier_id].get('name', 'Unknown')

                        stops = first_leg.get('stopCount', 0)

                    flights.append({
                        'origin': origin,
                        'destination': destination,
                        'departure_date': departure_date,
                        'return_date': return_date,
                        'price': float(price),
                        'currency': currency,
                        'airline': airline,
                        'stops': stops,
                        'url': f"https://www.skyscanner.com/",
                        'is_multi_leg': False,
                        'leg_details': None,
                        'data_source': 'skyscanner'
                    })

        except Exception as e:
            logger.error(f"Error parsing Skyscanner results: {e}")

        return flights


class KayakAPI:
    """
    Kayak Flight Search Integration
    Note: Kayak doesn't have a public API, so this uses web scraping via their search URLs
    For production, consider using RapidAPI's Kayak endpoint if available
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('KAYAK_API_KEY')
        # Using RapidAPI Kayak endpoint if API key is provided
        self.use_api = bool(self.api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        currency: str = 'USD',
        adults: int = 1
    ) -> List[Dict]:
        """
        Search for flights using Kayak
        """
        if self.use_api and self.api_key:
            return self._search_kayak_api(origin, destination, departure_date, return_date, currency, adults)
        else:
            return self._search_kayak_scrape(origin, destination, departure_date, return_date)

    def _search_kayak_api(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        currency: str,
        adults: int
    ) -> List[Dict]:
        """Search using Kayak RapidAPI endpoint (if available)"""
        try:
            # RapidAPI Kayak endpoint
            url = "https://kayak-com.p.rapidapi.com/api/v1/flights/search"

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': 'kayak-com.p.rapidapi.com'
            }

            params = {
                'origin': origin,
                'destination': destination,
                'departDate': departure_date,
                'adults': adults,
                'currency': currency
            }

            if return_date:
                params['returnDate'] = return_date

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"Kayak API error: {response.status_code}")
                return []

            data = response.json()
            flights = self._parse_kayak_api_results(data, origin, destination, departure_date, return_date, currency)

            logger.info(f"Kayak API found {len(flights)} flights")
            return flights

        except Exception as e:
            logger.error(f"Kayak API error: {e}")
            return []

    def _parse_kayak_api_results(
        self,
        data: Dict,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        currency: str
    ) -> List[Dict]:
        """Parse Kayak API response"""
        flights = []

        try:
            # This structure depends on the actual Kayak API response format
            # Adjust based on actual API documentation
            results = data.get('results', [])

            for result in results:
                price = result.get('price', 0)
                airline = result.get('airline', 'Unknown')
                stops = result.get('stops', 0)

                flights.append({
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date,
                    'return_date': return_date,
                    'price': float(price),
                    'currency': currency,
                    'airline': airline,
                    'stops': stops,
                    'url': result.get('booking_url', 'https://www.kayak.com'),
                    'is_multi_leg': False,
                    'leg_details': None,
                    'data_source': 'kayak'
                })

        except Exception as e:
            logger.error(f"Error parsing Kayak API results: {e}")

        return flights

    def _search_kayak_scrape(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str]
    ) -> List[Dict]:
        """
        Fallback method using Kayak search URL construction
        Note: This creates the search URL but doesn't actually scrape
        For actual scraping, you'd need Selenium + BeautifulSoup
        """
        try:
            # Build Kayak search URL
            if return_date:
                url = f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}/{return_date}"
            else:
                url = f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}"

            logger.info(f"Kayak search URL (scraping not implemented): {url}")

            # Actual scraping would require:
            # 1. Selenium WebDriver to handle JavaScript
            # 2. BeautifulSoup to parse results
            # 3. Handling CAPTCHA and anti-bot measures
            # 4. Rate limiting

            # For now, return empty list
            # In production, implement Selenium-based scraping here
            return []

        except Exception as e:
            logger.error(f"Kayak scraping error: {e}")
            return []


class MultiSourceFlightSearcher:
    """
    Unified flight searcher that queries multiple data sources
    and combines results
    """

    def __init__(self, serpapi_key=None, skyscanner_key=None, kayak_key=None):
        self.sources = []

        # Initialize available sources
        if skyscanner_key:
            self.sources.append(('skyscanner', SkyscannerAPI(skyscanner_key)))

        if kayak_key:
            self.sources.append(('kayak', KayakAPI(kayak_key)))

        logger.info(f"Initialized {len(self.sources)} additional data sources")

    def search_all_sources(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Search all available data sources and combine results
        """
        all_flights = []

        for source_name, source_api in self.sources:
            try:
                logger.info(f"Searching {source_name}...")
                flights = source_api.search_flights(
                    origin, destination, departure_date, return_date, currency
                )
                all_flights.extend(flights)
                logger.info(f"{source_name} returned {len(flights)} flights")

                # Rate limiting between sources
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error searching {source_name}: {e}")

        # Remove duplicates based on price and airline
        unique_flights = self._deduplicate_flights(all_flights)

        logger.info(f"Total unique flights from all sources: {len(unique_flights)}")
        return unique_flights

    def _deduplicate_flights(self, flights: List[Dict]) -> List[Dict]:
        """Remove duplicate flights based on price, airline, and stops"""
        seen = set()
        unique = []

        for flight in flights:
            key = (
                flight['origin'],
                flight['destination'],
                flight['departure_date'],
                flight['price'],
                flight['airline'],
                flight['stops']
            )

            if key not in seen:
                seen.add(key)
                unique.append(flight)

        return unique
