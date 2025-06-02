import os
from dotenv import load_dotenv

# Load environment variables from .env only (not .env-example).
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

class Config:
    # Scraper credentials.
    USERNAME = os.getenv('SCRAPER_USERNAME', '')
    PASSWORD = os.getenv('SCRAPER_PASSWORD', '')
    
    # Throw error if credentials are default placeholders.
    if USERNAME in ('', 'your_username_here') or PASSWORD in ('', 'your_password_here'):
        raise ValueError("SCRAPER_USERNAME and SCRAPER_PASSWORD must be set in your .env file and not use default values!")
    
    # Scraper settings.
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    TIMEOUT = int(os.getenv('TIMEOUT', '10'))
    
    # Output settings.
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/data')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Health check.
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
