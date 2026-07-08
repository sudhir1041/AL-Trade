"""
apps/reports/models.py
T15 ✅
"""
import uuid
from django.db import models
from core.models import TenantBaseModel


class ReportType(models.TextChoices):
    DAILY     = "DAILY",     "Daily Report"
    WEEKLY    = "WEEKLY",    "Weekly Report"
    MONTHLY   = "MONTHLY",   "Monthly Report"
    YEARLY    = "YEARLY",    "Yearly Report"
    TAX       = "TAX",       "Tax Export"
    STRATEGY  = "STRATEGY",  "Strategy Report"
    TRADE_JOURNAL = "TRADE_JOURNAL", "Trade Journal"
    CUSTOM    = "CUSTOM",    "Custom Report"


class ReportStatus(models.TextChoices):
    PENDING   = "PENDING",   "Pending"
    GENERATING = "GENERATING", "Generating"
    READY     = "READY",     "Ready"
    FAILED    = "FAILED",    "Failed"


class Report(TenantBaseModel):
    """Generated report record with download link."""
    user         = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="reports")
    report_type  = models.CharField(max_length=20, choices=ReportType.choices)
    title        = models.CharField(max_length=255)
    status       = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    parameters   = models.JSONField(default=dict)   # date_from, date_to, strategy_id, etc.
    file_path    = models.CharField(max_length=500, blank=True)
    file_size_kb = models.PositiveIntegerField(default=0)
    data         = models.JSONField(default=dict)    # summary metrics
    error_message = models.TextField(blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Report"
        verbose_name_plural = "Reports"
        ordering            = ["-created_at"]
        indexes = [models.Index(fields=["user", "report_type", "-created_at"])]

    def __str__(self):
        return f"Report({self.report_type}, {self.status}, user={self.user_id})"
