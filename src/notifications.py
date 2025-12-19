"""
Notification system for sending flight deal alerts
"""
import smtplib
import logging
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Handles email and SMS notifications"""

    def __init__(
        self,
        email_config: Optional[Dict] = None,
        sms_config: Optional[Dict] = None
    ):
        self.email_config = email_config or {}
        self.sms_config = sms_config or {}
        self.twilio_client = None

        # Initialize Twilio if configured
        if sms_config and sms_config.get('enabled'):
            try:
                from twilio.rest import Client
                self.twilio_client = Client(
                    sms_config['account_sid'],
                    sms_config['auth_token']
                )
            except ImportError:
                logger.warning("Twilio not installed. SMS notifications disabled.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")

    def send_flight_alert(self, flights: List[Dict], alert_type: str = 'deal'):
        """
        Send alert for flight deals

        Args:
            flights: List of flight data dictionaries
            alert_type: Type of alert ('deal', 'price_drop', 'new_low')
        """
        if not flights:
            return

        # Send email if configured
        if self.email_config.get('enabled'):
            try:
                self._send_email_alert(flights, alert_type)
                logger.info(f"Email alert sent for {len(flights)} flight(s)")
            except Exception as e:
                logger.error(f"Failed to send email: {e}")

        # Send SMS if configured
        if self.twilio_client and self.sms_config.get('enabled'):
            try:
                self._send_sms_alert(flights, alert_type)
                logger.info(f"SMS alert sent for {len(flights)} flight(s)")
            except Exception as e:
                logger.error(f"Failed to send SMS: {e}")

    def _send_email_alert(self, flights: List[Dict], alert_type: str):
        """Send email notification"""
        subject = self._get_email_subject(flights, alert_type)
        body = self._format_email_body(flights, alert_type)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_config['from']
        msg['To'] = self.email_config['to']

        # Plain text version
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)

        # HTML version
        html_body = self._format_html_email(flights, alert_type)
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(
            self.email_config['smtp_server'],
            self.email_config['smtp_port']
        ) as server:
            server.starttls()
            server.login(
                self.email_config['from'],
                self.email_config['password']
            )
            server.send_message(msg)

    def _send_sms_alert(self, flights: List[Dict], alert_type: str):
        """Send SMS notification"""
        # SMS messages need to be concise
        best_flight = min(flights, key=lambda x: x['price'])

        message = (
            f"✈️ Flight Deal Alert!\n"
            f"{best_flight['origin']} → {best_flight['destination']}\n"
            f"${best_flight['price']:.0f} on {best_flight['departure_date']}\n"
            f"{len(flights)} option(s) found!"
        )

        self.twilio_client.messages.create(
            body=message,
            from_=self.sms_config['from_number'],
            to=self.sms_config['to_number']
        )

    def _get_email_subject(self, flights: List[Dict], alert_type: str) -> str:
        """Generate email subject line"""
        best_flight = min(flights, key=lambda x: x['price'])
        price = best_flight['price']
        route = f"{best_flight['origin']} → {best_flight['destination']}"

        if alert_type == 'deal':
            return f"✈️ Flight Deal: {route} for ${price:.0f}!"
        elif alert_type == 'price_drop':
            return f"📉 Price Drop: {route} now ${price:.0f}!"
        elif alert_type == 'new_low':
            return f"🎯 New Low Price: {route} at ${price:.0f}!"
        else:
            return f"Flight Alert: {route} - ${price:.0f}"

    def _format_email_body(self, flights: List[Dict], alert_type: str) -> str:
        """Format plain text email body"""
        lines = [
            "Flight Price Alert",
            "=" * 50,
            ""
        ]

        if alert_type == 'deal':
            lines.append("Great news! We found flights within your budget:")
        elif alert_type == 'price_drop':
            lines.append("Price drop detected on your route!")
        elif alert_type == 'new_low':
            lines.append("New lowest price found!")

        lines.append("")

        for i, flight in enumerate(sorted(flights, key=lambda x: x['price']), 1):
            lines.extend([
                f"Option {i}:",
                f"  Route: {flight['origin']} → {flight['destination']}",
                f"  Price: ${flight['price']:.2f} {flight['currency']}",
                f"  Departure: {flight['departure_date']}",
            ])

            if flight.get('return_date'):
                lines.append(f"  Return: {flight['return_date']}")

            if flight.get('airline'):
                lines.append(f"  Airline: {flight['airline']}")

            if flight.get('stops') is not None:
                stops_text = "Direct" if flight['stops'] == 0 else f"{flight['stops']} stop(s)"
                lines.append(f"  Stops: {stops_text}")

            if flight.get('is_multi_leg'):
                lines.append(f"  Multi-leg: {flight.get('leg_details', 'Yes')}")

            # Add booking URLs
            if flight.get('url'):
                lines.append(f"  Google Flights: {flight['url']}")

            # Parse booking_urls if it's a JSON string
            booking_urls = flight.get('booking_urls')
            if isinstance(booking_urls, str):
                try:
                    booking_urls = json.loads(booking_urls)
                except:
                    booking_urls = None

            if booking_urls and isinstance(booking_urls, dict):
                if 'skyscanner' in booking_urls:
                    lines.append(f"  Skyscanner: {booking_urls['skyscanner']}")
                if 'kayak' in booking_urls:
                    lines.append(f"  Kayak: {booking_urls['kayak']}")

            lines.append("")

        lines.extend([
            "-" * 50,
            f"Alert sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Happy travels! 🌍"
        ])

        return "\n".join(lines)

    def _format_html_email(self, flights: List[Dict], alert_type: str) -> str:
        """Format HTML email body"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                .flight-card {{ background-color: #f9f9f9; border-left: 4px solid #4CAF50; padding: 15px; margin: 15px 0; border-radius: 3px; }}
                .price {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
                .route {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .detail {{ margin: 5px 0; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
                .badge {{ background-color: #ff9800; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }}
                .booking-buttons {{ margin-top: 15px; }}
                .booking-btn {{ display: inline-block; padding: 10px 20px; margin: 5px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .booking-btn:hover {{ background-color: #0b7dda; }}
                .booking-btn.google {{ background-color: #4285F4; }}
                .booking-btn.skyscanner {{ background-color: #00B2D6; }}
                .booking-btn.kayak {{ background-color: #FF6600; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✈️ Flight Deal Alert!</h1>
                    <p>We found great deals for your trip</p>
                </div>
        """

        for i, flight in enumerate(sorted(flights, key=lambda x: x['price']), 1):
            stops_text = "Direct Flight" if flight.get('stops', 0) == 0 else f"{flight['stops']} Stop(s)"
            multi_leg_badge = '<span class="badge">Multi-Leg</span>' if flight.get('is_multi_leg') else ''

            html += f"""
                <div class="flight-card">
                    <div class="route">{flight['origin']} → {flight['destination']} {multi_leg_badge}</div>
                    <div class="price">${flight['price']:.2f} {flight['currency']}</div>
                    <div class="detail">📅 Departure: {flight['departure_date']}</div>
            """

            if flight.get('return_date'):
                html += f'<div class="detail">📅 Return: {flight["return_date"]}</div>'

            if flight.get('airline'):
                html += f'<div class="detail">🛫 Airline: {flight["airline"]}</div>'

            html += f'<div class="detail">🔄 {stops_text}</div>'

            if flight.get('is_multi_leg') and flight.get('leg_details'):
                html += f'<div class="detail">📍 {flight["leg_details"]}</div>'

            # Add booking buttons
            html += '<div class="booking-buttons">'

            # Parse booking_urls if it's a JSON string
            booking_urls = flight.get('booking_urls')
            if isinstance(booking_urls, str):
                try:
                    booking_urls = json.loads(booking_urls)
                except:
                    booking_urls = None

            if booking_urls and isinstance(booking_urls, dict):
                if 'google_flights' in booking_urls:
                    html += f'<a href="{booking_urls["google_flights"]}" class="booking-btn google" target="_blank">Book on Google Flights</a>'
                if 'skyscanner' in booking_urls:
                    html += f'<a href="{booking_urls["skyscanner"]}" class="booking-btn skyscanner" target="_blank">Check Skyscanner</a>'
                if 'kayak' in booking_urls:
                    html += f'<a href="{booking_urls["kayak"]}" class="booking-btn kayak" target="_blank">Check Kayak</a>'
            elif flight.get('url'):
                # Fallback to single URL
                html += f'<a href="{flight["url"]}" class="booking-btn google" target="_blank">Book This Flight</a>'

            html += '</div></div>'

        html += f"""
                <div class="footer">
                    <p>Alert sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Happy travels! 🌍</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def send_test_notification(self):
        """Send a test notification to verify configuration"""
        test_flight = {
            'origin': 'ATL',
            'destination': 'MAD',
            'departure_date': '2025-03-20',
            'return_date': '2025-03-29',
            'price': 550.00,
            'currency': 'USD',
            'airline': 'Test Airlines',
            'stops': 0,
            'url': 'https://example.com',
            'is_multi_leg': False
        }

        self.send_flight_alert([test_flight], 'deal')
        logger.info("Test notification sent")

    def send_multimodal_journey_alert(self, journeys: List[Dict], alert_type: str = 'deal'):
        """
        Send alert for multi-modal journey deals (flight + train combinations)

        Args:
            journeys: List of multi-modal journey dictionaries
            alert_type: Type of alert ('deal', 'price_drop', 'new_low')
        """
        if not journeys:
            return

        # Send email if configured
        if self.email_config.get('enabled'):
            try:
                self._send_multimodal_email_alert(journeys, alert_type)
                logger.info(f"Multi-modal email alert sent for {len(journeys)} journey(s)")
            except Exception as e:
                logger.error(f"Failed to send multi-modal email: {e}")

        # Send SMS if configured
        if self.twilio_client and self.sms_config.get('enabled'):
            try:
                self._send_multimodal_sms_alert(journeys, alert_type)
                logger.info(f"Multi-modal SMS alert sent for {len(journeys)} journey(s)")
            except Exception as e:
                logger.error(f"Failed to send multi-modal SMS: {e}")

    def _send_multimodal_email_alert(self, journeys: List[Dict], alert_type: str):
        """Send email notification for multi-modal journeys"""
        subject = self._get_multimodal_email_subject(journeys, alert_type)
        body = self._format_multimodal_email_body(journeys, alert_type)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_config['from']
        msg['To'] = self.email_config['to']

        # Plain text version
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)

        # HTML version
        html_body = self._format_multimodal_html_email(journeys, alert_type)
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(
            self.email_config['smtp_server'],
            self.email_config['smtp_port']
        ) as server:
            server.starttls()
            server.login(
                self.email_config['from'],
                self.email_config['password']
            )
            server.send_message(msg)

    def _send_multimodal_sms_alert(self, journeys: List[Dict], alert_type: str):
        """Send SMS notification for multi-modal journeys"""
        best_journey = min(journeys, key=lambda x: x.get('total_price', float('inf')))

        message = (
            f"✈️🚄 Multi-Modal Deal Alert!\n"
            f"{best_journey.get('journey_summary', 'Journey found')}\n"
            f"Total: ${best_journey.get('total_price', 0):.0f}\n"
            f"{len(journeys)} option(s) found!"
        )

        self.twilio_client.messages.create(
            body=message,
            from_=self.sms_config['from_number'],
            to=self.sms_config['to_number']
        )

    def _get_multimodal_email_subject(self, journeys: List[Dict], alert_type: str) -> str:
        """Generate email subject for multi-modal journeys"""
        best_journey = min(journeys, key=lambda x: x.get('total_price', float('inf')))
        price = best_journey.get('total_price', 0)
        summary = best_journey.get('journey_summary', 'Journey')

        if alert_type == 'deal':
            return f"✈️🚄 Multi-Modal Deal: {summary} for ${price:.0f}!"
        elif alert_type == 'price_drop':
            return f"📉 Price Drop: {summary} now ${price:.0f}!"
        elif alert_type == 'new_low':
            return f"🎯 New Low: {summary} at ${price:.0f}!"
        else:
            return f"Multi-Modal Journey Alert: ${price:.0f}"

    def _format_multimodal_email_body(self, journeys: List[Dict], alert_type: str) -> str:
        """Format plain text email body for multi-modal journeys"""
        lines = [
            "Multi-Modal Journey Alert (Flight + Train)",
            "=" * 60,
            ""
        ]

        if alert_type == 'deal':
            lines.append("Great news! We found complete journey options within your budget:")
        elif alert_type == 'price_drop':
            lines.append("Price drop detected on multi-modal routes!")
        elif alert_type == 'new_low':
            lines.append("New lowest price for complete journeys!")

        lines.append("")

        for i, journey in enumerate(sorted(journeys, key=lambda x: x.get('total_price', 0)), 1):
            journey_type = journey.get('type', 'unknown')
            lines.extend([
                f"Option {i}: {journey.get('journey_summary', 'Journey')}",
                f"  Total Price: ${journey.get('total_price', 0):.2f} {journey.get('currency', 'USD')}",
                ""
            ])

            # Flight segment
            if journey.get('flight'):
                flight = journey['flight']
                lines.extend([
                    "  ✈️ FLIGHT SEGMENT:",
                    f"     {flight.get('origin')} → {flight.get('destination')}",
                    f"     Price: ${flight.get('price', 0):.2f}",
                    f"     Airline: {flight.get('airline', 'Unknown')}",
                    f"     Date: {flight.get('departure_date', 'N/A')}"
                ])

                # Add booking URLs
                if flight.get('url'):
                    lines.append(f"     Book: {flight['url']}")

                lines.append("")

            # Train segment
            if journey.get('train'):
                train = journey['train']
                lines.extend([
                    "  🚄 TRAIN SEGMENT:",
                    f"     {train.get('from_city', train.get('from_airport'))} → {train.get('to_city', train.get('to_airport'))}",
                    f"     Price: €{train.get('price_estimate', 0):.2f} (${train.get('price_estimate', 0) * 1.1:.2f})",
                    f"     Operator: {train.get('operator', 'Unknown')}",
                    f"     Duration: {train.get('duration_hours', 0):.1f} hours"
                ])

                # Add train booking URLs
                if train.get('trainline_url'):
                    lines.append(f"     Trainline: {train['trainline_url']}")
                if train.get('booking_url'):
                    lines.append(f"     RENFE: {train['booking_url']}")

                lines.append("")

            lines.append("-" * 60)
            lines.append("")

        lines.extend([
            f"Alert sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Happy travels! 🌍"
        ])

        return "\n".join(lines)

    def _format_multimodal_html_email(self, journeys: List[Dict], alert_type: str) -> str:
        """Format HTML email body for multi-modal journeys"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #2196F3 100%); color: white; padding: 25px; text-align: center; border-radius: 5px; }}
                .journey-card {{ background-color: #f9f9f9; border-left: 5px solid #4CAF50; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .segment {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 3px; border: 1px solid #e0e0e0; }}
                .segment-icon {{ font-size: 24px; display: inline-block; margin-right: 10px; }}
                .total-price {{ font-size: 28px; font-weight: bold; color: #4CAF50; margin: 10px 0; }}
                .price {{ font-size: 20px; font-weight: bold; color: #2196F3; }}
                .route {{ font-size: 18px; font-weight: bold; margin: 10px 0; }}
                .detail {{ margin: 5px 0; }}
                .booking-buttons {{ margin-top: 15px; }}
                .booking-btn {{ display: inline-block; padding: 10px 20px; margin: 5px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .booking-btn.google {{ background-color: #4285F4; }}
                .booking-btn.train {{ background-color: #FF9800; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
                .arrow {{ color: #4CAF50; font-size: 20px; margin: 0 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✈️🚄 Multi-Modal Journey Alert!</h1>
                    <p>Complete travel solutions with flights and trains</p>
                </div>
        """

        for i, journey in enumerate(sorted(journeys, key=lambda x: x.get('total_price', 0)), 1):
            html += f"""
                <div class="journey-card">
                    <h2>Option {i}: {journey.get('journey_summary', 'Complete Journey')}</h2>
                    <div class="total-price">Total: ${journey.get('total_price', 0):.2f}</div>
            """

            # Flight segment
            if journey.get('flight'):
                flight = journey['flight']
                html += f"""
                    <div class="segment">
                        <div class="segment-icon">✈️</div><strong>FLIGHT</strong>
                        <div class="route">{flight.get('origin')} <span class="arrow">→</span> {flight.get('destination')}</div>
                        <div class="price">${flight.get('price', 0):.2f}</div>
                        <div class="detail">🛫 {flight.get('airline', 'Unknown')}</div>
                        <div class="detail">📅 {flight.get('departure_date', 'N/A')}</div>
                        <div class="booking-buttons">
                """

                # Parse booking URLs
                booking_urls = flight.get('booking_urls')
                if isinstance(booking_urls, str):
                    try:
                        booking_urls = json.loads(booking_urls)
                    except:
                        booking_urls = None

                if booking_urls and isinstance(booking_urls, dict):
                    if 'google_flights' in booking_urls:
                        html += f'<a href="{booking_urls["google_flights"]}" class="booking-btn google" target="_blank">Book Flight</a>'
                    if 'skyscanner' in booking_urls:
                        html += f'<a href="{booking_urls["skyscanner"]}" class="booking-btn" target="_blank">Skyscanner</a>'
                elif flight.get('url'):
                    html += f'<a href="{flight["url"]}" class="booking-btn google" target="_blank">Book Flight</a>'

                html += """
                        </div>
                    </div>
                """

            # Train segment
            if journey.get('train'):
                train = journey['train']
                from_city = train.get('from_city', train.get('from_airport', 'N/A'))
                to_city = train.get('to_city', train.get('to_airport', 'N/A'))

                html += f"""
                    <div class="segment">
                        <div class="segment-icon">🚄</div><strong>TRAIN</strong>
                        <div class="route">{from_city} <span class="arrow">→</span> {to_city}</div>
                        <div class="price">€{train.get('price_estimate', 0):.2f} (${train.get('price_estimate', 0) * 1.1:.2f})</div>
                        <div class="detail">🚂 {train.get('operator', 'Unknown')}</div>
                        <div class="detail">⏱️ {train.get('duration_hours', 0):.1f} hours</div>
                        <div class="booking-buttons">
                """

                if train.get('trainline_url'):
                    html += f'<a href="{train["trainline_url"]}" class="booking-btn train" target="_blank">Book on Trainline</a>'
                if train.get('booking_url'):
                    html += f'<a href="{train["booking_url"]}" class="booking-btn train" target="_blank">Book on RENFE</a>'

                html += """
                        </div>
                    </div>
                """

            html += "</div>"

        html += f"""
                <div class="footer">
                    <p>Alert sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Book each segment separately for best results 🌍</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html
