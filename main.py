"""
adb-turbo - Main Entry Point
Clean Architecture Implementation with CLI support
"""

import sys
import argparse
import signal
import atexit
from flask import Flask, send_from_directory
from flask_cors import CORS

from src.config import Settings, setup_logger
from src.helpers.network import kill_process_on_port
from src.api import api_bp

# Standardized logger
logger = setup_logger(Settings.LOG_DIR / "app.log", name="epic_adb.main")

# Initialize Flask app
app = Flask(__name__, static_folder=Settings.STATIC_DIR, template_folder=Settings.STATIC_DIR)
CORS(app, origins=Settings.CORS_ORIGINS)

# Register API Blueprint
app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/')
def index():
    """Serve the main web interface"""
    return send_from_directory(Settings.STATIC_DIR, 'index.html')


def log_banner(url):
    """Log a nice banner with the server URL"""
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
    logger.info(banner)


def cleanup():
    """Cleanup function to run on exit"""
    logger.info(f"Server stopped. Port {Settings.ADB_PORT} is now free.")
    logger.info("Thank you for using adb-turbo!")


def start_web_server():
    """Configure and start the Flask web server"""
    # Ensure port is free before starting
    kill_process_on_port(Settings.ADB_PORT)
    log_banner(Settings.url)
    
    try:
        logger.info(f"Starting Flask server on {Settings.ADB_HOST}:{Settings.ADB_PORT}")
        app.run(host=Settings.ADB_HOST, port=Settings.ADB_PORT, debug=Settings.DEBUG, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error during server execution: {e}")


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
