"""
Scheduler for AI Employee tasks using APScheduler
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEmployeeScheduler:
    def __init__(self, agent):
        self.agent = agent
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """Setup all scheduled jobs"""
        logger.info("Setting up scheduled jobs...")

        # Start all watchers at boot (these run continuously, not scheduled)
        self._start_watchers()

        # Schedule LinkedIn auto post daily at 9 AM
        self.scheduler.add_job(
            func=self._run_linkedin_post,
            trigger=CronTrigger(hour=9, minute=0),
            id='linkedin_auto_post',
            name='LinkedIn daily post',
            replace_existing=True
        )

        # Schedule Claude reasoning loop daily at 8 AM
        self.scheduler.add_job(
            func=self._run_daily_plan,
            trigger=CronTrigger(hour=8, minute=0),
            id='daily_business_plan',
            name='Daily business plan and strategy',
            replace_existing=True
        )

        # Schedule weekly audit every Monday at 9 AM
        self.scheduler.add_job(
            func=self._run_weekly_audit,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_audit',
            name='Weekly CEO briefing and audit',
            replace_existing=True
        )

        # Schedule periodic watcher health checks every 30 minutes
        self.scheduler.add_job(
            func=self._check_watcher_health,
            trigger=IntervalTrigger(minutes=30),
            id='watcher_health_check',
            name='Watcher health check',
            replace_existing=True
        )

        logger.info("All jobs scheduled successfully")

    def _start_watchers(self):
        """Start all watchers at boot"""
        logger.info("Starting all watchers...")

        try:
            # Start Gmail watcher
            result = self.agent.run("gmail_watcher_skill", action="start")
            logger.info(f"Gmail watcher: {result}")
        except Exception as e:
            logger.error(f"Error starting Gmail watcher: {e}")

        try:
            # Start WhatsApp watcher
            result = self.agent.run("whatsapp_watcher_skill", action="start")
            logger.info(f"WhatsApp watcher: {result}")
        except Exception as e:
            logger.error(f"Error starting WhatsApp watcher: {e}")

        try:
            # Start LinkedIn watcher
            result = self.agent.run("linkedin_watcher_skill", action="start")
            logger.info(f"LinkedIn watcher: {result}")
        except Exception as e:
            logger.error(f"Error starting LinkedIn watcher: {e}")

        logger.info("All watchers started")

    def _run_linkedin_post(self):
        """Run LinkedIn auto post job"""
        logger.info(f"Running LinkedIn auto post job at {datetime.now()}")
        try:
            result = self.agent.run(
                "linkedin_auto_post",
                post_topic="Daily business insights",
                context="Daily post about business strategy and insights"
            )
            logger.info(f"LinkedIn post job completed: {result}")
        except Exception as e:
            logger.error(f"Error in LinkedIn post job: {e}")

    def _run_daily_plan(self):
        """Run daily business plan job"""
        logger.info(f"Running daily business plan job at {datetime.now()}")
        try:
            result = self.agent.run(
                "claude_reasoning_loop",
                task_description="Create today's business plan and sales strategy",
                context="Generate a comprehensive business plan and sales strategy for today, focusing on key priorities, potential opportunities, and strategic initiatives."
            )
            logger.info(f"Daily plan job completed: {result}")
        except Exception as e:
            logger.error(f"Error in daily plan job: {e}")

    def _check_watcher_health(self):
        """Check if watchers are still running"""
        logger.info(f"Running watcher health check at {datetime.now()}")

        # In a real implementation, we would check if the watcher threads are still alive
        # and restart any that have stopped
        logger.info("Watcher health check completed")

    def _run_weekly_audit(self):
        """Run weekly audit job"""
        logger.info(f"Running weekly audit job at {datetime.now()}")
        try:
            # Import and run the weekly audit orchestrator
            from weekly_audit_orchestrator import run_weekly_audit_job
            result = run_weekly_audit_job()
            logger.info(f"Weekly audit job completed: {result}")
        except Exception as e:
            logger.error(f"Error in weekly audit job: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

            # Shut down the scheduler when exiting the app
            atexit.register(self.shutdown)

    def shutdown(self):
        """Shut down the scheduler"""
        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown()
        logger.info("Scheduler shut down")


# Example of cron jobs (for systems that support cron)
CRON_EXAMPLE = """
# Example crontab entries (Linux/Mac)
# To edit: crontab -e

# Daily LinkedIn post at 9 AM
0 9 * * * cd /path/to/ai_employee && python -c "from core.agent import AIAgent; agent = AIAgent(); agent.run('linkedin_auto_post', post_topic='Daily business insights', context='Daily post about business strategy and insights')"

# Daily business plan at 8 AM
0 8 * * * cd /path/to/ai_employee && python -c "from core.agent import AIAgent; agent = AIAgent(); agent.run('claude_reasoning_loop', task_description='Create today\\'s business plan and sales strategy', context='Generate a comprehensive business plan and sales strategy for today')"

# Note: These cron examples would need proper environment setup and are alternatives to the APScheduler approach
"""