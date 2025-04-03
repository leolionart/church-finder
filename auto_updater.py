from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from church_list_scraper import ChurchListScraper
import logging
from datetime import datetime
import pytz

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('auto_updater')

class ChurchDataUpdater:
    def __init__(self):
        self.scraper = ChurchListScraper()
        self.scheduler = BackgroundScheduler()
        self.vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')

    def update_data(self):
        """Update church data from giothanhle.net."""
        try:
            current_time = datetime.now(self.vietnam_tz).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Starting data update at {current_time}")
            
            updated_count = self.scraper.run()
            logger.info(f"Successfully updated {updated_count} churches")
            
        except Exception as e:
            logger.error(f"Error updating data: {str(e)}")

    def start(self):
        """Start the scheduler."""
        try:
            # Add job to run every hour
            self.scheduler.add_job(
                func=self.update_data,
                trigger=IntervalTrigger(hours=1),
                id='update_church_data',
                name='Update church data from giothanhle.net',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            logger.info("Scheduler started successfully")
            
            # Run initial update
            self.update_data()
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")

    def stop(self):
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
