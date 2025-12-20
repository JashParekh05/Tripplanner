"""
Generate clickable booking URLs for flights across multiple platforms
"""
from typing import Dict, Optional
from urllib.parse import urlencode
from datetime import datetime


class FlightBookingURLGenerator:
    """
    Generates direct booking URLs for various flight booking platforms
    Supports Google Flights, Skyscanner, Kayak, and airline direct links
    """

    @staticmethod
    def generate_google_flights_url(
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        cabin_class: str = 'economy'
    ) -> str:
        """
        Generate Google Flights search URL

        Args:
            origin: Origin airport code (e.g., 'ATL')
            destination: Destination airport code (e.g., 'MAD')
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (optional)
            adults: Number of adult passengers
            cabin_class: Cabin class (economy, premium_economy, business, first)

        Returns:
            Direct Google Flights search URL
        """
        # Format dates for Google Flights (YYYY-MM-DD)
        base_url = "https://www.google.com/travel/flights"

        # Build the search string
        # Format: /flights?f=0&hl=en&curr=USD&tfs=...
        if return_date:
            # Round trip
            flight_params = f"flights?f=0&hl=en&curr=USD&tfs=CBwQAhooEgoyMDI1LTAzLTIwagcIARIDQVRMcgcIARIDTUFEGgoyMDI1LTAzLTI5agcIARIDTUFEcgcIARIDQVRMcAGCAQsI____________AUABSAGYAQI"
            # Simplified URL format for round trip
            url = f"https://www.google.com/travel/flights/search?tfs=CBwQAhooagcIARID{origin}EgoyMDI1LTAzLTIwcgcIARID{destination}GgpqBwgBEgN{destination}EgoyMDI1LTAzLTI5cgcIARID{origin}cAGCAQsI____________AUABSAGYAQIQARgAKgA"

            # Better format - use the standard Google Flights URL
            url = (f"https://www.google.com/travel/flights?"
                   f"q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}%20through%20{return_date}")
        else:
            # One way
            url = (f"https://www.google.com/travel/flights?"
                   f"q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}%20one%20way")

        return url

    @staticmethod
    def generate_skyscanner_url(
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> str:
        """
        Generate Skyscanner search URL

        Format: https://www.skyscanner.com/transport/flights/atl/mad/250320/250329/
        """
        # Format dates for Skyscanner (YYMMDD)
        try:
            dep_date_obj = datetime.strptime(departure_date, '%Y-%m-%d')
            dep_formatted = dep_date_obj.strftime('%y%m%d')

            if return_date:
                ret_date_obj = datetime.strptime(return_date, '%Y-%m-%d')
                ret_formatted = ret_date_obj.strftime('%y%m%d')
                url = f"https://www.skyscanner.com/transport/flights/{origin.lower()}/{destination.lower()}/{dep_formatted}/{ret_formatted}/"
            else:
                url = f"https://www.skyscanner.com/transport/flights/{origin.lower()}/{destination.lower()}/{dep_formatted}/"

            # Add passenger info
            url += f"?adults={adults}&adultsv2={adults}&cabinclass=economy&children=0&childrenv2=&inboundaltsenabled=false&infants=0&outboundaltsenabled=false&preferdirects=false&ref=home&rtn={1 if return_date else 0}"

            return url
        except:
            # Fallback to simple URL
            return f"https://www.skyscanner.com/transport/flights/{origin.lower()}/{destination.lower()}/"

    @staticmethod
    def generate_kayak_url(
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> str:
        """
        Generate Kayak search URL

        Format: https://www.kayak.com/flights/ATL-MAD/2025-03-20/2025-03-29/1adults
        """
        if return_date:
            url = f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}/{return_date}/{adults}adults"
        else:
            url = f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}/{adults}adults"

        return url

    @staticmethod
    def generate_momondo_url(
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None
    ) -> str:
        """
        Generate Momondo search URL

        Format: https://www.momondo.com/flight-search/ATL-MAD/2025-03-20/2025-03-29
        """
        if return_date:
            url = f"https://www.momondo.com/flight-search/{origin}-{destination}/{departure_date}/{return_date}"
        else:
            url = f"https://www.momondo.com/flight-search/{origin}-{destination}/{departure_date}"

        return url

    @staticmethod
    def generate_booking_urls(
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> Dict[str, str]:
        """
        Generate booking URLs for all major platforms

        Returns:
            Dictionary with platform names as keys and URLs as values
        """
        return {
            'google_flights': FlightBookingURLGenerator.generate_google_flights_url(
                origin, destination, departure_date, return_date, adults
            ),
            'skyscanner': FlightBookingURLGenerator.generate_skyscanner_url(
                origin, destination, departure_date, return_date, adults
            ),
            'kayak': FlightBookingURLGenerator.generate_kayak_url(
                origin, destination, departure_date, return_date, adults
            ),
            'momondo': FlightBookingURLGenerator.generate_momondo_url(
                origin, destination, departure_date, return_date
            )
        }

    @staticmethod
    def get_primary_booking_url(
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        preferred_platform: str = 'google_flights'
    ) -> str:
        """
        Get the primary booking URL for a flight

        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date
            return_date: Return date (optional)
            preferred_platform: Preferred booking platform (default: google_flights)

        Returns:
            Primary booking URL
        """
        urls = FlightBookingURLGenerator.generate_booking_urls(
            origin, destination, departure_date, return_date
        )

        return urls.get(preferred_platform, urls['google_flights'])
