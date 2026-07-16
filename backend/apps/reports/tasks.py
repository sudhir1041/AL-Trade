"""
apps/reports/tasks.py
T15 ✅
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.reports.tasks")


@shared_task(queue="reports", name="apps.reports.tasks.generate_report")
def generate_report(report_id: str) -> dict:
    """T15 ✅  Generate a report and save results to the Report record."""
    from apps.reports.models import Report, ReportStatus
    from apps.reports.services import ReportService
    from django.utils import timezone

    try:
        report          = Report.objects.get(pk=report_id)
        report.status   = ReportStatus.GENERATING
        report.save(update_fields=["status"])

        data            = ReportService().generate(report)
        report.data     = data
        report.status   = ReportStatus.READY
        report.generated_at = timezone.now()
        report.save(update_fields=["data", "status", "generated_at"])

        logger.info("Report generated: %s (%s)", report_id, report.report_type)
        return {"status": "READY", "report_id": report_id}

    except Exception as exc:
        logger.exception("Report generation failed: %s", report_id)
        Report.objects.filter(pk=report_id).update(
            status=ReportStatus.FAILED, error_message=str(exc)[:500]
        )
        return {"status": "FAILED", "error": str(exc)}


@shared_task(queue="reports", name="apps.reports.tasks.generate_daily_reports")
def generate_daily_reports() -> None:
    """T15 ✅  Auto-generate daily reports for all active users — midnight UTC."""
    from apps.accounts.models import User
    from apps.reports.models import Report, ReportType
    from django.utils import timezone

    yesterday = str((timezone.now() - timezone.timedelta(days=1)).date())
    for user in User.objects.filter(is_active=True):
        report = Report.objects.create(
            user=user,
            tenant_id=user.tenant_id or user.id,
            report_type=ReportType.DAILY,
            title=f"Daily Report — {yesterday}",
            parameters={"date": yesterday},
        )
        generate_report.delay(str(report.id))


@shared_task(queue="reports", name="apps.reports.tasks.generate_weekly_reports")
def generate_weekly_reports() -> None:
    """T15 ✅  Auto-generate weekly reports — Monday 01:00 UTC."""
    from apps.accounts.models import User
    from apps.reports.models import Report, ReportType
    from django.utils import timezone

    today  = timezone.now().date()
    monday = today - timezone.timedelta(days=today.weekday() + 7)
    for user in User.objects.filter(is_active=True):
        report = Report.objects.create(
            user=user,
            tenant_id=user.tenant_id or user.id,
            report_type=ReportType.WEEKLY,
            title=f"Weekly Report — w/c {monday}",
            parameters={"week_start": str(monday)},
        )
        generate_report.delay(str(report.id))
