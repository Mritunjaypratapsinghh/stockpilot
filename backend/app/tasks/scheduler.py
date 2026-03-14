from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..utils.logger import logger
from .alert_checker import check_alerts, check_stop_losses
from .digest_generator import generate_daily_digest
from .earnings_checker import check_earnings_alerts
from .hourly_update import send_hourly_update
from .ipo_tracker import check_ipo_alerts, scrape_ipo_data
from .portfolio_advisor import run_portfolio_advisor
from .price_updater import update_all_prices
from .tax_harvest_alert import check_tax_harvesting
from .weekly_report import send_weekly_report
from .ws_broadcaster import broadcast_prices

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


def start_scheduler():
    # WebSocket price broadcast (every 5 seconds during market hours)
    scheduler.add_job(broadcast_prices, "interval", seconds=5, id="ws_broadcast")

    # Price updates
    scheduler.add_job(update_all_prices, "interval", minutes=5, id="price_update")

    # User-defined price alerts
    scheduler.add_job(check_alerts, "interval", minutes=1, id="alert_check")

    # Stop-loss breach monitoring (every 5 min during market hours)
    scheduler.add_job(
        check_stop_losses,
        "cron",
        day_of_week="mon-fri",
        hour="9-16",
        minute="*/5",
        id="stop_loss_check",
    )

    # Hourly portfolio update (market hours: 9 AM - 4 PM IST, weekdays only)
    scheduler.add_job(send_hourly_update, "cron", day_of_week="mon-fri", hour="9-16", minute=0, id="hourly_update")

    # Smart Portfolio Advisor - twice daily during market hours
    scheduler.add_job(run_portfolio_advisor, "cron", hour=9, minute=30, id="advisor_morning")
    scheduler.add_job(run_portfolio_advisor, "cron", hour=15, minute=0, id="advisor_afternoon")

    # Daily digest at 6 PM IST
    scheduler.add_job(generate_daily_digest, "cron", hour=18, minute=0, id="daily_digest")

    # Earnings reminders at 9 AM IST
    scheduler.add_job(check_earnings_alerts, "cron", hour=9, minute=0, id="earnings_check")

    # IPO tracking
    scheduler.add_job(scrape_ipo_data, "interval", hours=2, id="ipo_scrape")
    scheduler.add_job(check_ipo_alerts, "cron", hour=9, minute=30, id="ipo_alerts")

    # Weekly AI report - Saturday 10 AM IST
    scheduler.add_job(
        send_weekly_report,
        "cron",
        day_of_week="sat",
        hour=10,
        minute=0,
        id="weekly_report",
    )

    # Tax harvesting alerts - Monday 9 AM IST
    scheduler.add_job(
        check_tax_harvesting,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=0,
        id="tax_harvest_alert",
    )

    scheduler.start()
    logger.info("Scheduler started with all jobs (IST timezone)")
