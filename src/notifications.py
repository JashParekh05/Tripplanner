"""
Notification system for sending flight deal alerts
"""
import smtplib
import logging
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

            if flight.get('url'):
                lines.append(f"  Details: {flight['url']}")

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

            html += "</div>"

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
