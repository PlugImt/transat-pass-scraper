import os
from dotenv import load_dotenv

# Load environment variables from .env only (not .env-example).
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

class Config:
    # Scraper credentials.
    PASS_USERNAME = os.getenv('PASS_USERNAME', 'your_username_here')
    PASS_PASSWORD = os.getenv('PASS_PASSWORD', 'your_password_here')
    
    # Throw error if credentials are default placeholders.
    if PASS_USERNAME in ('', 'your_username_here') or PASS_PASSWORD in ('', 'your_password_here'):
        raise ValueError("PASS_USERNAME and PASS_PASSWORD must be set in your .env file and not use default values!")
    
    # Scraper settings.
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    TIMEOUT = int(os.getenv('TIMEOUT', '10'))
    
    # Output settings.
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/data')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Health check.
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '8080'))

    # API settings
    TRANSAT_API_EMAIL = os.getenv('TRANSAT_API_EMAIL', 'your_email_here')
    TRANSAT_API_PASSWORD = os.getenv('TRANSAT_API_PASSWORD', 'your_password_here')
    TEMPORARY_USER_EMAIL = os.getenv('TEMPORARY_USER_EMAIL', 'your_email_here')

    # Throw error if API credentials are default placeholders.
    if TRANSAT_API_EMAIL in ('', 'your_email_here') or TRANSAT_API_PASSWORD in ('', 'your_password_here'):
        raise ValueError("TRANSAT_API_EMAIL and TRANSAT_API_PASSWORD must be set in your .env file and not use default values!")
    
    if TEMPORARY_USER_EMAIL in ('', 'your_email_here'):
        raise ValueError("TEMPORARY_USER_EMAIL must be set in your .env file and not use default values!")

    TEMPORARY_USER_ID = os.getenv('TEMPORARY_USER_ID', 'default_user_id')
    if TEMPORARY_USER_ID == 'default_user_id':
        raise ValueError("TEMPORARY_USER_ID must be set in your .env file and not use default values!")
    
    ENV = os.getenv('ENV', 'dev').lower()
    if ENV not in ('dev', 'prod'):
        raise ValueError("ENV must be either 'dev' or 'prod' in your .env file!")
    
    DEV_API_URL = os.getenv('DEV_API_URL', 'http://host.docker.internal:3000')
    PROD_API_URL = os.getenv('PROD_API_URL', 'https://transat.destimt.fr')
    BASE_API_URL = PROD_API_URL if ENV == 'prod' else DEV_API_URL
    if not BASE_API_URL:
        raise ValueError("BASE_API_URL must be set in your .env file!")
