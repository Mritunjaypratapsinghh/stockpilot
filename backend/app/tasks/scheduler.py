from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .price_updater import update_all_prices
from .alert_checker import check_alerts
from .digest_generator import generate_daily_digest
from .earnings_checker import check_earnings_alerts
from .ipo_tracker import scrape_ipo_data, check_ipo_alerts
from .portfolio_advisor import run_portfolio_advisor
from .hourly_update import send_hourly_update
from ..logger import logger

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Price updates
    scheduler.add_job(update_all_prices, 'interval', minutes=5, id='price_update')
    
    # User-defined price alerts
    scheduler.add_job(check_alerts, 'interval', minutes=1, id='alert_check')
    
    # Hourly portfolio update (market hours: 9 AM - 4 PM)
    scheduler.add_job(send_hourly_update, 'cron', hour='9-16', minute=0, id='hourly_update')
    
    # Smart Portfolio Advisor - twice daily during market hours
    scheduler.add_job(run_portfolio_advisor, 'cron', hour=9, minute=30, id='advisor_morning')
    scheduler.add_job(run_portfolio_advisor, 'cron', hour=15, minute=0, id='advisor_afternoon')
    
    # Daily digest at 6 PM
    scheduler.add_job(generate_daily_digest, 'cron', hour=18, minute=0, id='daily_digest')
    
    # Earnings reminders at 9 AM
    scheduler.add_job(check_earnings_alerts, 'cron', hour=9, minute=0, id='earnings_check')
    
    # IPO tracking
    scheduler.add_job(scrape_ipo_data, 'interval', hours=2, id='ipo_scrape')
    scheduler.add_job(check_ipo_alerts, 'cron', hour=9, minute=30, id='ipo_alerts')
    
    scheduler.start()
    logger.info("Scheduler started with all jobs")
