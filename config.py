import os
from dotenv import load_dotenv

# Load environment variables.
load_dotenv()

class Config:
    # Scraper credentials.
    USERNAME = os.getenv('SCRAPER_USERNAME', '')
    PASSWORD = os.getenv('SCRAPER_PASSWORD', '')
    
    # Scraper settings.
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    TIMEOUT = int(os.getenv('TIMEOUT', '10'))
    
    # Output settings.
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/data')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Health check.
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
