#!/usr/bin/env python3
"""
Tripplanner Web Dashboard Server
Starts the Flask API server for the web dashboard
"""
import sys
import os
import logging
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api import app, run_server
from src.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Start the web dashboard server"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Tripplanner Web Dashboard Server')
    parser.add_argument('--port', type=int, default=None, help='Port to run the server on (default: 5000)')
    parser.add_argument('--host', type=str, default=None, help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("Starting Tripplanner Web Dashboard")
    logger.info("="*60)

    # Validate configuration
    errors = Config.validate_config()
    if errors:
        logger.warning("Configuration warnings:")
        for error in errors:
            logger.warning(f"  - {error}")

    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    # Server configuration (command-line args override environment variables)
    host = args.host or os.getenv('WEB_HOST', '0.0.0.0')
    port = args.port or int(os.getenv('WEB_PORT', '5000'))
    debug = args.debug or (os.getenv('WEB_DEBUG', 'false').lower() == 'true')

    logger.info(f"Dashboard will be available at: http://{host}:{port}")
    logger.info(f"Local access: http://localhost:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info("")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("="*60)

    try:
        run_server(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("\nShutting down web server...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
