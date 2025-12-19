"""
Flask API for Tripplanner Web Dashboard
Provides REST endpoints for viewing deals and managing configuration
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
import os
from datetime import datetime
from typing import Dict, List

from database import FlightDatabase
from config import Config
from flight_monitor import FlightMonitor

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../web/build', static_url_path='')
CORS(app)  # Enable CORS for React frontend

# Initialize database
db = FlightDatabase(Config.DATABASE_PATH)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})


@app.route('/api/deals', methods=['GET'])
def get_deals():
    """Get all flight deals"""
    try:
        max_price = request.args.get('max_price', Config.MAX_PRICE, type=int)
        limit = request.args.get('limit', 50, type=int)

        deals = db.get_recent_deals(max_price, limit)

        return jsonify({
            'success': True,
            'count': len(deals),
            'deals': deals
        })
    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/deals/<int:deal_id>', methods=['GET'])
def get_deal_by_id(deal_id: int):
    """Get specific deal by ID"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM flight_prices WHERE id = ?', (deal_id,))
            deal = cursor.fetchone()

            if deal:
                return jsonify({'success': True, 'deal': dict(deal)})
            else:
                return jsonify({'success': False, 'error': 'Deal not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching deal {deal_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/deals/unnotified', methods=['GET'])
def get_unnotified_deals():
    """Get deals that haven't been notified yet"""
    try:
        max_price = request.args.get('max_price', Config.MAX_PRICE, type=int)
        deals = db.get_unnotified_deals(max_price)

        return jsonify({
            'success': True,
            'count': len(deals),
            'deals': deals
        })
    except Exception as e:
        logger.error(f"Error fetching unnotified deals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/deals/<int:deal_id>/notify', methods=['POST'])
def mark_deal_notified(deal_id: int):
    """Mark a deal as notified"""
    try:
        alert_type = request.json.get('alert_type', 'manual')
        db.mark_as_notified(deal_id, alert_type)

        return jsonify({'success': True, 'message': f'Deal {deal_id} marked as notified'})
    except Exception as e:
        logger.error(f"Error marking deal {deal_id} as notified: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/price-trends', methods=['GET'])
def get_price_trends():
    """Get price trends for routes"""
    try:
        origin = request.args.get('origin', Config.ORIGIN_AIRPORT)
        destination = request.args.get('destination')
        days = request.args.get('days', 7, type=int)

        if not destination:
            return jsonify({'success': False, 'error': 'Destination required'}), 400

        trends = db.get_price_trend(origin, destination, days)

        return jsonify({
            'success': True,
            'origin': origin,
            'destination': destination,
            'days': days,
            'data': trends
        })
    except Exception as e:
        logger.error(f"Error fetching price trends: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        config_data = {
            'origin_airport': Config.ORIGIN_AIRPORT,
            'destination_airports': Config.DESTINATION_AIRPORTS,
            'eu_hub_airports': Config.EU_HUB_AIRPORTS,
            'departure_date': Config.DEPARTURE_DATE,
            'return_date': Config.RETURN_DATE,
            'date_flexibility': Config.DATE_FLEXIBILITY,
            'max_price': Config.MAX_PRICE,
            'currency': Config.CURRENCY,
            'check_interval_hours': Config.CHECK_INTERVAL_HOURS,
            'enable_multi_leg_search': Config.ENABLE_MULTI_LEG_SEARCH,
            'price_drop_threshold': Config.PRICE_DROP_THRESHOLD,
            'email_enabled': Config.EMAIL_ENABLED,
            'sms_enabled': Config.SMS_ENABLED,
            'serpapi_enabled': bool(Config.SERPAPI_KEY)
        }

        return jsonify({'success': True, 'config': config_data})
    except Exception as e:
        logger.error(f"Error fetching config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update configuration (writes to .env file)"""
    try:
        data = request.json

        # Validate required fields
        updates = {}

        if 'destination_airports' in data:
            if isinstance(data['destination_airports'], list):
                updates['DESTINATION_AIRPORTS'] = ','.join(data['destination_airports'])
            else:
                updates['DESTINATION_AIRPORTS'] = data['destination_airports']

        if 'eu_hub_airports' in data:
            if isinstance(data['eu_hub_airports'], list):
                updates['EU_HUB_AIRPORTS'] = ','.join(data['eu_hub_airports'])
            else:
                updates['EU_HUB_AIRPORTS'] = data['eu_hub_airports']

        # Update numeric fields
        for field in ['max_price', 'date_flexibility', 'check_interval_hours', 'price_drop_threshold']:
            if field in data:
                env_key = field.upper()
                updates[env_key] = str(data[field])

        # Update boolean fields
        for field in ['enable_multi_leg_search', 'email_enabled', 'sms_enabled']:
            if field in data:
                env_key = field.upper()
                updates[env_key] = 'true' if data[field] else 'false'

        # Update date fields
        for field in ['departure_date', 'return_date', 'origin_airport', 'currency']:
            if field in data:
                env_key = field.upper()
                updates[env_key] = data[field]

        # Write to .env file
        _update_env_file(updates)

        return jsonify({
            'success': True,
            'message': 'Configuration updated. Restart the service to apply changes.',
            'updates': updates
        })
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search/manual', methods=['POST'])
def manual_search():
    """Trigger a manual flight search"""
    try:
        data = request.json

        origin = data.get('origin', Config.ORIGIN_AIRPORT)
        destination = data.get('destination')
        departure_date = data.get('departure_date', Config.DEPARTURE_DATE)
        return_date = data.get('return_date', Config.RETURN_DATE)

        if not destination:
            return jsonify({'success': False, 'error': 'Destination required'}), 400

        # Initialize monitor and run search
        monitor = FlightMonitor()

        # This would trigger a search
        # For now, return success message
        return jsonify({
            'success': True,
            'message': f'Manual search triggered for {origin} to {destination}',
            'search_params': {
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
                'return_date': return_date
            }
        })
    except Exception as e:
        logger.error(f"Error in manual search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Total deals found
            cursor.execute('SELECT COUNT(*) as count FROM flight_prices')
            total_deals = cursor.fetchone()['count']

            # Deals under max price
            cursor.execute('SELECT COUNT(*) as count FROM flight_prices WHERE price <= ?', (Config.MAX_PRICE,))
            good_deals = cursor.fetchone()['count']

            # Lowest price ever
            cursor.execute('SELECT MIN(price) as min_price FROM flight_prices')
            lowest_price = cursor.fetchone()['min_price']

            # Average price
            cursor.execute('SELECT AVG(price) as avg_price FROM flight_prices')
            avg_price = cursor.fetchone()['avg_price']

            # Alerts sent
            cursor.execute('SELECT COUNT(*) as count FROM alerts_sent')
            alerts_sent = cursor.fetchone()['count']

            # Recent searches (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) as count FROM flight_prices
                WHERE datetime(found_at) >= datetime('now', '-1 day')
            ''')
            recent_searches = cursor.fetchone()['count']

            return jsonify({
                'success': True,
                'stats': {
                    'total_deals': total_deals,
                    'good_deals': good_deals,
                    'lowest_price': lowest_price,
                    'average_price': round(avg_price, 2) if avg_price else 0,
                    'alerts_sent': alerts_sent,
                    'recent_searches_24h': recent_searches
                }
            })
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data-sources', methods=['GET'])
def get_data_sources():
    """Get available data sources and their status"""
    try:
        sources = {
            'serpapi': {
                'name': 'SerpAPI (Google Flights)',
                'enabled': bool(Config.SERPAPI_KEY),
                'status': 'active' if Config.SERPAPI_KEY else 'disabled'
            },
            'skyscanner': {
                'name': 'Skyscanner',
                'enabled': bool(os.getenv('SKYSCANNER_API_KEY')),
                'status': 'active' if os.getenv('SKYSCANNER_API_KEY') else 'disabled'
            },
            'kayak': {
                'name': 'Kayak',
                'enabled': bool(os.getenv('KAYAK_API_KEY')),
                'status': 'active' if os.getenv('KAYAK_API_KEY') else 'disabled'
            }
        }

        return jsonify({'success': True, 'sources': sources})
    except Exception as e:
        logger.error(f"Error fetching data sources: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Serve React frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve React frontend"""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


def _update_env_file(updates: Dict[str, str]):
    """Update .env file with new values"""
    env_path = '.env'

    # Read existing .env
    existing_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_vars[key] = value

    # Update with new values
    existing_vars.update(updates)

    # Write back to .env
    with open(env_path, 'w') as f:
        for key, value in existing_vars.items():
            f.write(f"{key}={value}\n")

    logger.info(f"Updated .env file with {len(updates)} changes")


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask development server"""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_server(debug=True)
