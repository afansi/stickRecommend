from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from database import SessionLocal
from models.tables import User
from services.scanner_service import ScannerService
import config
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def scan_all_users():
    """
    Scheduled job to scan markets for all users.
    Runs based on configured schedule.
    """
    logger.info("Starting scheduled market scan for all users...")
    session = SessionLocal()
    
    try:
        # Get all active users
        users = session.exec(select(User).where(User.is_active == True)).all()
        
        total_recommendations = 0
        for user in users:
            if not user.active_sectors:
                continue
                
            sectors = user.active_sectors.split(",")
            logger.info(f"Scanning sectors {sectors} for user {user.username}")
            
            scanner = ScannerService(session)
            
            # 1. Broad Discovery Scan (Institutional Setups)
            logger.info(f"Running discovery scan for {user.username}...")
            scanner.discover_opportunities(user.id)

            # 2. Sector-specific Scans
            results = scanner.scan_active_sectors(sectors, user.id)
            total_recommendations += len(results)
            
            # 3. Alerts
            from services.alert_service import AlertService
            alert_service = AlertService(session)
            alert_service.generate_alerts_from_recommendations(user, results)
            alert_service.generate_alerts_for_portfolio(user)
            
        logger.info(f"Scheduled scan complete.")
        
    except Exception as e:
        logger.error(f"Error in scheduled scan: {e}")
    finally:
        session.close()

def start_scheduler():
    """
    Initialize and start the APScheduler.
    """
    if not config.ENABLE_SCHEDULED_SCAN:
        logger.info("Scheduled scanning is disabled.")
        return
        
    # Parse cron expression (format: "minute hour day month day_of_week")
    # Example: "0 6 * * 0" = Every Sunday at 6:00 AM
    cron_parts = config.SCAN_SCHEDULE.split()
    if len(cron_parts) != 5:
        logger.error(f"Invalid SCAN_SCHEDULE format: {config.SCAN_SCHEDULE}. Using default.")
        cron_parts = ["0", "6", "*", "*", "0"]  # Default: Sunday 6 AM
    
    trigger = CronTrigger(
        minute=cron_parts[0],
        hour=cron_parts[1],
        day=cron_parts[2],
        month=cron_parts[3],
        day_of_week=cron_parts[4]
    )
    
    scheduler.add_job(scan_all_users, trigger, id="market_scan", replace_existing=True)
    scheduler.start()
    logger.info(f"Scheduler started with cron: {config.SCAN_SCHEDULE}")

def stop_scheduler():
    """
    Shutdown the scheduler gracefully.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
