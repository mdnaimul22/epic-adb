"""
adb-turbo - Main Entry Point
Clean Architecture Implementation with CLI support
"""

import os
import sys
import argparse
import signal
import atexit
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

# Add current directory to path for Clean Architecture
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import settings, setup_logging
from src.helpers.network import kill_process_on_port
from src.api import api_bp

# Initialize Flask app
app = Flask(__name__, static_folder=settings.STATIC_DIR, template_folder=settings.STATIC_DIR)
CORS(app, origins=settings.CORS_ORIGINS)

# Register API Blueprint
app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/')
def index():
    """Serve the main web interface"""
    return send_from_directory(settings.STATIC_DIR, 'index.html')


def print_banner(url):
    """Print a nice banner with the server URL"""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                   adb-turbo                                  ║
║        Friendly Android Performance Tool                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🚀 Server running at: {url}

Press Ctrl+C to stop the server
"""
    print(banner)


def cleanup():
    """Cleanup function to run on exit"""
    print(f"\n\n👋 Server stopped. Port {settings.ADB_PORT} is now free.")
    print("Thank you for using adb-turbo!")


def start_web_server():
    """Configure and start the Flask web server"""
    setup_logging(settings)
    
    # Ensure port is free before starting
    kill_process_on_port(settings.ADB_PORT)
    print_banner(settings.url)
    
    try:
        logging.getLogger(__name__).info(f"Starting Flask server on {settings.ADB_HOST}:{settings.ADB_PORT}")
        app.run(host=settings.ADB_HOST, port=settings.ADB_PORT, debug=settings.DEBUG, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='adb-turbo - Android Performance Optimizer')
    parser.add_argument('command', choices=['web'], help='Command to run (e.g., "web" to start server)')
    
    args = parser.parse_args()

    if args.command == 'web':
        # Register cleanup handlers
        atexit.register(cleanup)
        # Handle termination signals
        signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
        signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
        
        start_web_server()
