"""
Train ticket search integration for multi-modal journey planning
Integrates with Rome2rio and Trainline APIs for European train connections
"""
import requests
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class TrainTicketSearcher:
    """
    Searches for train tickets between European cities
    Supports multiple providers: Rome2rio, Trainline, and direct booking links
    """

    def __init__(self):
        self.rome2rio_key = os.getenv('ROME2RIO_API_KEY')
        self.trainline_key = os.getenv('TRAINLINE_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Spanish train operators and their websites
        self.train_providers = {
            'RENFE': 'https://www.renfe.com',  # Spain's main rail operator
            'AVE': 'https://www.renfe.com',     # High-speed trains in Spain
            'Trainline': 'https://www.thetrainline.com'
        }

        # Common train routes in Spain with approximate prices (EUR)
        self.spanish_train_routes = {
            ('BCN', 'MAD'): {'duration_hours': 2.5, 'price_low': 25, 'price_high': 80, 'operator': 'AVE'},
            ('MAD', 'BCN'): {'duration_hours': 2.5, 'price_low': 25, 'price_high': 80, 'operator': 'AVE'},
            ('VLC', 'MAD'): {'duration_hours': 1.7, 'price_low': 20, 'price_high': 60, 'operator': 'AVE'},
            ('MAD', 'VLC'): {'duration_hours': 1.7, 'price_low': 20, 'price_high': 60, 'operator': 'AVE'},
            ('SVQ', 'MAD'): {'duration_hours': 2.5, 'price_low': 20, 'price_high': 70, 'operator': 'AVE'},
            ('MAD', 'SVQ'): {'duration_hours': 2.5, 'price_low': 20, 'price_high': 70, 'operator': 'AVE'},
            ('AGP', 'MAD'): {'duration_hours': 2.5, 'price_low': 25, 'price_high': 75, 'operator': 'AVE'},
            ('MAD', 'AGP'): {'duration_hours': 2.5, 'price_low': 25, 'price_high': 75, 'operator': 'AVE'},
            ('BCN', 'VLC'): {'duration_hours': 3, 'price_low': 15, 'price_high': 50, 'operator': 'RENFE'},
            ('VLC', 'BCN'): {'duration_hours': 3, 'price_low': 15, 'price_high': 50, 'operator': 'RENFE'},
            ('BCN', 'SVQ'): {'duration_hours': 5.5, 'price_low': 30, 'price_high': 100, 'operator': 'AVE'},
            ('SVQ', 'BCN'): {'duration_hours': 5.5, 'price_low': 30, 'price_high': 100, 'operator': 'AVE'},
            ('BCN', 'AGP'): {'duration_hours': 5.5, 'price_low': 30, 'price_high': 100, 'operator': 'AVE'},
            ('AGP', 'BCN'): {'duration_hours': 5.5, 'price_low': 30, 'price_high': 100, 'operator': 'AVE'},
            ('VLC', 'SVQ'): {'duration_hours': 6, 'price_low': 25, 'price_high': 80, 'operator': 'RENFE'},
            ('SVQ', 'VLC'): {'duration_hours': 6, 'price_low': 25, 'price_high': 80, 'operator': 'RENFE'},
        }

        # Airport to city center mappings for Spanish cities
        self.airport_to_city = {
            'MAD': 'Madrid',
            'BCN': 'Barcelona',
            'VLC': 'Valencia',
            'SVQ': 'Seville',
            'AGP': 'Malaga',
            'BIO': 'Bilbao',
            'PMI': 'Palma de Mallorca',
            'GRX': 'Granada',
            'ZAZ': 'Zaragoza',
            'GRO': 'Girona',
            'ALC': 'Alicante',
        }

    def search_train_connections(
        self,
        from_airport: str,
        to_airport: str,
        departure_date: str,
        return_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for train connections between two airports/cities

        Args:
            from_airport: Origin airport code (e.g., 'BCN')
            to_airport: Destination airport code (e.g., 'MAD')
            departure_date: Date in YYYY-MM-DD format
            return_date: Optional return date

        Returns:
            List of train options with pricing and booking info
        """
        trains = []

        # Check if direct train route exists
        route_key = (from_airport, to_airport)
        if route_key in self.spanish_train_routes:
            route_info = self.spanish_train_routes[route_key]

            # Create train option
            train_option = {
                'from_airport': from_airport,
                'to_airport': to_airport,
                'from_city': self.airport_to_city.get(from_airport, from_airport),
                'to_city': self.airport_to_city.get(to_airport, to_airport),
                'departure_date': departure_date,
                'return_date': return_date,
                'price_low': route_info['price_low'],
                'price_high': route_info['price_high'],
                'price_estimate': (route_info['price_low'] + route_info['price_high']) / 2,
                'duration_hours': route_info['duration_hours'],
                'operator': route_info['operator'],
                'currency': 'EUR',
                'booking_url': self._generate_train_booking_url(from_airport, to_airport, departure_date),
                'trainline_url': self._generate_trainline_url(from_airport, to_airport, departure_date),
            }

            trains.append(train_option)
            logger.info(f"Found train route: {from_airport} → {to_airport} (~€{train_option['price_estimate']:.0f})")
        else:
            logger.info(f"No direct train route found between {from_airport} and {to_airport}")

        # Try Rome2rio API if available
        if self.rome2rio_key:
            try:
                rome2rio_results = self._search_rome2rio(from_airport, to_airport, departure_date)
                trains.extend(rome2rio_results)
            except Exception as e:
                logger.error(f"Rome2rio search failed: {e}")

        return trains

    def _search_rome2rio(
        self,
        from_airport: str,
        to_airport: str,
        departure_date: str
    ) -> List[Dict]:
        """
        Search using Rome2rio API for multi-modal transport options
        """
        try:
            from_city = self.airport_to_city.get(from_airport, from_airport)
            to_city = self.airport_to_city.get(to_airport, to_airport)

            params = {
                'key': self.rome2rio_key,
                'oName': f"{from_city}, Spain",
                'dName': f"{to_city}, Spain",
                'currencyCode': 'EUR'
            }

            response = requests.get(
                'http://free.rome2rio.com/api/1.4/json/Search',
                params=params,
                timeout=15
            )

            if response.status_code != 200:
                logger.error(f"Rome2rio API error: {response.status_code}")
                return []

            data = response.json()
            return self._parse_rome2rio_results(data, from_airport, to_airport, departure_date)

        except Exception as e:
            logger.error(f"Rome2rio error: {e}")
            return []

    def _parse_rome2rio_results(
        self,
        data: Dict,
        from_airport: str,
        to_airport: str,
        departure_date: str
    ) -> List[Dict]:
        """Parse Rome2rio API response"""
        trains = []

        try:
            routes = data.get('routes', [])

            for route in routes:
                # Look for train segments
                segments = route.get('segments', [])

                for segment in segments:
                    if segment.get('kind') == 'train':
                        price_low = segment.get('indicativePrices', [{}])[0].get('priceLow', 0)
                        price_high = segment.get('indicativePrices', [{}])[0].get('priceHigh', 0)
                        duration = segment.get('transitDuration', 0)

                        if price_low or price_high:
                            trains.append({
                                'from_airport': from_airport,
                                'to_airport': to_airport,
                                'from_city': self.airport_to_city.get(from_airport, from_airport),
                                'to_city': self.airport_to_city.get(to_airport, to_airport),
                                'departure_date': departure_date,
                                'return_date': None,
                                'price_low': price_low,
                                'price_high': price_high,
                                'price_estimate': (price_low + price_high) / 2 if price_low and price_high else price_low or price_high,
                                'duration_hours': duration / 3600,  # Convert seconds to hours
                                'operator': segment.get('operator', 'Train'),
                                'currency': 'EUR',
                                'booking_url': segment.get('url', ''),
                                'trainline_url': self._generate_trainline_url(from_airport, to_airport, departure_date),
                            })
        except Exception as e:
            logger.error(f"Error parsing Rome2rio results: {e}")

        return trains

    def _generate_train_booking_url(self, from_code: str, to_code: str, date: str) -> str:
        """Generate RENFE booking URL"""
        from_city = self.airport_to_city.get(from_code, from_code)
        to_city = self.airport_to_city.get(to_code, to_code)

        # Format date for RENFE (DD/MM/YYYY)
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_date = date

        # RENFE search URL
        base_url = "https://www.renfe.com/es/en/train-tickets"

        return f"{base_url}?origin={from_city}&destination={to_city}&date={formatted_date}"

    def _generate_trainline_url(self, from_code: str, to_code: str, date: str) -> str:
        """Generate Trainline booking URL"""
        from_city = self.airport_to_city.get(from_code, from_code)
        to_city = self.airport_to_city.get(to_code, to_code)

        # Format date for Trainline (YYYY-MM-DD)
        # Trainline URL format
        from_slug = from_city.lower().replace(' ', '-')
        to_slug = to_city.lower().replace(' ', '-')

        return f"https://www.thetrainline.com/book/results?origin={from_slug}&destination={to_slug}&outwardDate={date}&outwardDateType=departAfter"


class MultiModalJourneyPlanner:
    """
    Combines flight and train searches to create complete journey options
    """

    def __init__(self, train_searcher: Optional[TrainTicketSearcher] = None):
        self.train_searcher = train_searcher or TrainTicketSearcher()
        # Exchange rate EUR to USD (approximate - should be updated with real API)
        self.eur_to_usd = float(os.getenv('EUR_TO_USD_RATE', '1.10'))

    def create_multimodal_journeys(
        self,
        flights: List[Dict],
        final_destination: str,
        currency: str = 'USD'
    ) -> List[Dict]:
        """
        Create multi-modal journey options combining flights and trains

        Args:
            flights: List of flight options
            final_destination: Final destination airport code (e.g., 'MAD')
            currency: Currency for total pricing

        Returns:
            List of complete journey options with flight + train combinations
        """
        multimodal_journeys = []

        for flight in flights:
            flight_dest = flight['destination']

            # If flight goes directly to final destination, add it as-is
            if flight_dest == final_destination:
                journey = {
                    'type': 'direct_flight',
                    'origin': flight['origin'],
                    'destination': final_destination,
                    'flight': flight,
                    'train': None,
                    'total_price': flight['price'],
                    'currency': currency,
                    'journey_summary': f"{flight['origin']} → {final_destination} (Direct Flight)",
                    'segments': [
                        {
                            'type': 'flight',
                            'from': flight['origin'],
                            'to': final_destination,
                            'price': flight['price'],
                            'details': flight
                        }
                    ]
                }
                multimodal_journeys.append(journey)

            # If flight goes to a different Spanish city, search for train connections
            else:
                # Search for train from flight destination to final destination
                trains = self.train_searcher.search_train_connections(
                    flight_dest,
                    final_destination,
                    flight['departure_date']
                )

                if trains:
                    for train in trains:
                        # Convert train price from EUR to USD if needed
                        train_price_usd = train['price_estimate'] * self.eur_to_usd
                        total_price = flight['price'] + train_price_usd

                        journey = {
                            'type': 'flight_plus_train',
                            'origin': flight['origin'],
                            'destination': final_destination,
                            'flight': flight,
                            'train': train,
                            'total_price': total_price,
                            'currency': currency,
                            'journey_summary': f"{flight['origin']} ✈️ {flight_dest} 🚄 {final_destination}",
                            'segments': [
                                {
                                    'type': 'flight',
                                    'from': flight['origin'],
                                    'to': flight_dest,
                                    'price': flight['price'],
                                    'details': flight
                                },
                                {
                                    'type': 'train',
                                    'from': flight_dest,
                                    'to': final_destination,
                                    'price': train_price_usd,
                                    'price_eur': train['price_estimate'],
                                    'duration_hours': train['duration_hours'],
                                    'details': train
                                }
                            ]
                        }
                        multimodal_journeys.append(journey)
                else:
                    # No train connection found, still include flight option
                    journey = {
                        'type': 'flight_only',
                        'origin': flight['origin'],
                        'destination': flight_dest,
                        'flight': flight,
                        'train': None,
                        'total_price': flight['price'],
                        'currency': currency,
                        'journey_summary': f"{flight['origin']} → {flight_dest} (Flight Only)",
                        'note': f"No direct train to {final_destination}. Consider local transport or additional flights.",
                        'segments': [
                            {
                                'type': 'flight',
                                'from': flight['origin'],
                                'to': flight_dest,
                                'price': flight['price'],
                                'details': flight
                            }
                        ]
                    }
                    multimodal_journeys.append(journey)

        # Sort by total price
        multimodal_journeys.sort(key=lambda x: x['total_price'])

        logger.info(f"Created {len(multimodal_journeys)} multi-modal journey options")
        return multimodal_journeys

    def format_journey_display(self, journey: Dict) -> str:
        """
        Format a journey for display with detailed segment information

        Returns formatted string like:
        ATL ✈️ BCN (€450) 🚄 MAD (€35) = Total: $534
        """
        segments = journey['segments']
        parts = []

        for i, segment in enumerate(segments):
            if segment['type'] == 'flight':
                icon = '✈️'
                price_str = f"${segment['price']:.0f}"
            else:  # train
                icon = '🚄'
                price_eur = segment.get('price_eur', segment['price'] / self.eur_to_usd)
                price_str = f"€{price_eur:.0f} (${segment['price']:.0f})"

            if i == 0:
                parts.append(f"{segment['from']} {icon} {segment['to']} ({price_str})")
            else:
                parts.append(f"{icon} {segment['to']} ({price_str})")

        journey_str = " ".join(parts)
        total_str = f"Total: ${journey['total_price']:.0f}"

        return f"{journey_str} = {total_str}"
