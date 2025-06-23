import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path to import our scraper.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import TransatPassScraper
from config import Config

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path('/var/log/scraper')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def save_results(data, output_dir):
    """Save scraping results to file"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"scraper_results_{timestamp}.json"
    
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return str(file_path)

def run_scraper():
    """Main function to run the scraper"""
    logger = setup_logging()
    logger.info("Starting scheduled scraper run")
    
    try:
        # Validate configuration
        if not Config.PASS_USERNAME or not Config.PASS_PASSWORD:
            raise ValueError("Username and password must be provided")
        
        # Initialize scraper
        scraper = TransatPassScraper(
            headless=Config.HEADLESS,
            timeout=Config.TIMEOUT
        )
    
        # Run scraping
        result = scraper.run_full_scrape(
            pass_username=Config.PASS_USERNAME,
            pass_password=Config.PASS_PASSWORD
        )
        
        # Add metadata
        result['scrape_metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'success': 'error' not in result
        }
        
        # Save results
        output_file = save_results(result, Config.OUTPUT_DIR)
        logger.info(f"Results saved to: {output_file}")
        
        # Close scraper
        scraper.close()
        
        if 'error' in result:
            logger.error(f"Scraping failed: {result['error']}")
            sys.exit(1)
        else:
            logger.info("Scraping completed successfully")
            
    except Exception as e:
        logger.error(f"Scraper run failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_scraper()
