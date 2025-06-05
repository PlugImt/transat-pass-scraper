import os
from dotenv import load_dotenv

# Load environment variables from .env only (not .env-example).
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

class Config:
    # Scraper credentials.
    USERNAME = os.getenv('SCRAPER_USERNAME', 'your_username_here')
    PASSWORD = os.getenv('SCRAPER_PASSWORD', 'your_password_here')
    
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

    # API settings
    DEV_API_URL = os.getenv('DEV_API_URL', 'http://host.docker.internal:3000')
    PROD_API_URL = os.getenv('PROD_API_URL', 'https://transat.destimt.fr')
    API_EMAIL = os.getenv('API_EMAIL', 'your_email_here')
    API_PASSWORD = os.getenv('API_PASSWORD', 'your_password_here')
    USER_EMAIL = os.getenv('USER_EMAIL', 'your_email_here')

    # Throw error if API credentials are default placeholders.
    if API_EMAIL in ('', 'your_email_here') or API_PASSWORD in ('', 'your_password_here'):
        raise ValueError("API_EMAIL and API_PASSWORD must be set in your .env file and not use default values!")
    if USER_EMAIL in ('', 'your_email_here'):
        raise ValueError("USER_EMAIL must be set in your .env file and not use default values!")
