"""
TradeMind AI – Celery Application Configuration
Defines the Celery app, task queues, and beat schedule for all background jobs.
"""
import os

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

# ─────────────────────────────────────────
# Django settings bootstrap
# ─────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# ─────────────────────────────────────────
# Celery application
# ─────────────────────────────────────────
app = Celery("trademind")

# Load all CELERY_* keys from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in every INSTALLED_APP's tasks.py / tasks/ package
app.autodiscover_tasks()


# =============================================================================
# Queue Definitions
# =============================================================================
default_exchange    = Exchange("default",       type="direct")
scanner_exchange    = Exchange("scanner",       type="direct")
ai_exchange         = Exchange("ai_scoring",    type="direct")
notify_exchange     = Exchange("notifications", type="direct")
reports_exchange    = Exchange("reports",       type="direct")
ml_exchange         = Exchange("ml_training",   type="direct")
portfolio_exchange  = Exchange("portfolio_sync", type="direct")
order_exchange      = Exchange("order_sync",    type="direct")
backtest_exchange   = Exchange("backtest",      type="direct")

app.conf.task_queues = (
    # General-purpose queue
    Queue("default",        default_exchange,   routing_key="default"),

    # Market scanner – high-frequency, many workers
    Queue("scanner",        scanner_exchange,   routing_key="scanner"),

    # AI scoring & signal generation
    Queue("ai_scoring",     ai_exchange,        routing_key="ai_scoring"),

    # Notifications (email, Telegram, push)
    Queue("notifications",  notify_exchange,    routing_key="notifications"),

    # Report generation (PDF / Excel exports)
    Queue("reports",        reports_exchange,   routing_key="reports"),

    # ML model retraining
    Queue("ml_training",    ml_exchange,        routing_key="ml_training"),

    # Portfolio synchronisation with exchanges
    Queue("portfolio_sync", portfolio_exchange, routing_key="portfolio_sync"),

    # Live order synchronisation
    Queue("order_sync",     order_exchange,     routing_key="order_sync"),

    # Strategy backtesting
    Queue("backtest",       backtest_exchange,  routing_key="backtest"),
)

app.conf.task_default_queue        = "default"
app.conf.task_default_exchange     = "default"
app.conf.task_default_routing_key  = "default"


# =============================================================================
# Task Routing
# =============================================================================
app.conf.task_routes = {
    # Scanner
    "apps.scanner.tasks.*":          {"queue": "scanner"},

    # AI engine
    "apps.ai_engine.tasks.*":        {"queue": "ai_scoring"},
    "apps.ml_engine.tasks.score_*":  {"queue": "ai_scoring"},

    # ML training
    "apps.ml_engine.tasks.train_*":  {"queue": "ml_training"},
    "apps.ml_engine.tasks.retrain_*": {"queue": "ml_training"},

    # Notifications
    "apps.notifications.tasks.*":    {"queue": "notifications"},

    # Reports
    "apps.reports.tasks.*":          {"queue": "reports"},

    # Portfolio
    "apps.portfolio.tasks.sync_*":   {"queue": "portfolio_sync"},

    # Orders
    "apps.orders.tasks.sync_*":      {"queue": "order_sync"},

    # Backtesting
    "apps.strategies.tasks.backtest_*": {"queue": "backtest"},
}


# =============================================================================
# General Celery Settings
# =============================================================================
app.conf.update(
    # Serialisation
    task_serializer          = "json",
    result_serializer        = "json",
    accept_content           = ["json"],

    # Timezone
    timezone                 = "UTC",
    enable_utc               = True,

    # Task execution
    task_acks_late           = True,       # ACK after task completes (safer)
    task_reject_on_worker_lost = True,     # Re-queue on unexpected worker exit
    task_track_started       = True,
    task_time_limit          = 3600,       # Hard limit: 1 hour
    task_soft_time_limit     = 3300,       # Soft limit: 55 min (triggers SoftTimeLimitExceeded)

    # Result backend
    result_expires           = 86400,      # Keep results for 24 hours
    result_cache_max         = 1000,

    # Worker
    worker_prefetch_multiplier = 1,        # Fair task distribution
    worker_max_tasks_per_child = 200,      # Recycle workers to avoid memory leaks

    # Retry defaults
    task_max_retries         = 3,
    task_default_retry_delay = 60,         # seconds

    # Beat scheduler
    beat_scheduler           = "django_celery_beat.schedulers:DatabaseScheduler",
)


# =============================================================================
# Beat Schedule (periodic tasks)
# =============================================================================
app.conf.beat_schedule = {

    # ── Market Scanner – every 60 seconds during trading hours ──────────────
    "market-scan-every-60s": {
        "task":     "apps.scanner.tasks.run_market_scan",
        "schedule": 60.0,
        "options":  {"queue": "scanner", "expires": 55},
    },

    # ── Portfolio Sync – every 30 seconds ───────────────────────────────────
    "portfolio-sync-every-30s": {
        "task":     "apps.portfolio.tasks.sync_all_portfolios",
        "schedule": 30.0,
        "options":  {"queue": "portfolio_sync", "expires": 25},
    },

    # ── Order Sync – every 15 seconds ───────────────────────────────────────
    "order-sync-every-15s": {
        "task":     "apps.orders.tasks.sync_open_orders",
        "schedule": 15.0,
        "options":  {"queue": "order_sync", "expires": 12},
    },

    # ── Daily Reports – midnight UTC ────────────────────────────────────────
    "daily-reports-midnight": {
        "task":     "apps.reports.tasks.generate_daily_reports",
        "schedule": crontab(hour=0, minute=0),
        "options":  {"queue": "reports"},
    },

    # ── Weekly Reports – Monday 01:00 UTC ───────────────────────────────────
    "weekly-reports-monday": {
        "task":     "apps.reports.tasks.generate_weekly_reports",
        "schedule": crontab(hour=1, minute=0, day_of_week=1),
        "options":  {"queue": "reports"},
    },

    # ── ML Retraining Check – every Sunday 03:00 UTC ────────────────────────
    "ml-retraining-check-weekly": {
        "task":     "apps.ml_engine.tasks.check_and_retrain_models",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
        "options":  {"queue": "ml_training"},
    },

    # ── Cleanup Old Data – daily 02:00 UTC ──────────────────────────────────
    "cleanup-old-data-daily": {
        "task":     "apps.monitoring.tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),
        "options":  {"queue": "default"},
    },

    # ── Cleanup Expired Celery Results – daily 03:30 UTC ────────────────────
    "celery-backend-cleanup": {
        "task":     "celery.backend_cleanup",
        "schedule": crontab(hour=3, minute=30),
        "options":  {"queue": "default"},
    },

    # ── Recalculate AI Scores – every 5 minutes ─────────────────────────────
    "ai-score-refresh-5m": {
        "task":     "apps.ai_engine.tasks.refresh_watchlist_scores",
        "schedule": crontab(minute="*/5"),
        "options":  {"queue": "ai_scoring", "expires": 280},
    },

    # ── Risk Monitor – every 2 minutes ──────────────────────────────────────
    "risk-monitor-2m": {
        "task":     "apps.risk.tasks.check_portfolio_risk_limits",
        "schedule": crontab(minute="*/2"),
        "options":  {"queue": "default", "expires": 110},
    },
}


# =============================================================================
# Debug task (useful for health checks)
# =============================================================================
@app.task(bind=True, name="trademind.debug_task")
def debug_task(self):
    print(f"Request: {self.request!r}")
    return {"status": "ok", "worker": self.request.hostname}
