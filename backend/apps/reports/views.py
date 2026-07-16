"""
apps/reports/views.py
T15 ✅  Report REST endpoints.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import serializers as drf_serializers
from core.responses import created_response, error_response, success_response
from common.utils import paginate_queryset
from .models import Report, ReportType, ReportStatus


class ReportSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model  = Report
        fields = ["id", "report_type", "title", "status", "parameters",
                  "data", "error_message", "generated_at", "created_at"]
        read_only_fields = ["id", "status", "data", "error_message", "generated_at", "created_at"]


class ReportListView(APIView):
    """GET /api/v1/reports/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs    = Report.objects.filter(user=request.user, deleted_at__isnull=True).order_by("-created_at")
        rtype = request.query_params.get("type")
        if rtype:
            qs = qs.filter(report_type=rtype.upper())
        page  = int(request.query_params.get("page", 1))
        paged = paginate_queryset(qs, page, 20)
        return success_response(
            data=ReportSerializer(paged["results"], many=True).data,
            meta={"total": paged["count"]},
        )


class ReportGenerateView(APIView):
    """POST /api/v1/reports/generate/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        report_type = request.data.get("report_type", "DAILY").upper()
        if report_type not in ReportType.values:
            return error_response("VALIDATION_ERROR", f"Invalid report_type. Choose: {', '.join(ReportType.values)}")

        report = Report.objects.create(
            user=request.user,
            tenant_id=request.user.tenant_id or request.user.id,
            report_type=report_type,
            title=request.data.get("title", f"{report_type.title()} Report"),
            parameters=request.data.get("parameters", {}),
        )
        from apps.reports.tasks import generate_report
        generate_report.delay(str(report.id))

        return created_response(
            data=ReportSerializer(report).data,
            message="Report generation queued.",
        )


class ReportDetailView(APIView):
    """GET /api/v1/reports/{id}/  |  DELETE /api/v1/reports/{id}/"""
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return Report.objects.get(pk=pk, user=user)
        except Report.DoesNotExist:
            return None

    def get(self, request: Request, pk: str):
        r = self._get(pk, request.user)
        if not r:
            return error_response("RESOURCE_NOT_FOUND", "Report not found.", status_code=404)
        return success_response(data=ReportSerializer(r).data)

    def delete(self, request: Request, pk: str):
        r = self._get(pk, request.user)
        if not r:
            return error_response("RESOURCE_NOT_FOUND", "Report not found.", status_code=404)
        r.soft_delete(deleted_by=request.user.id)
        return success_response(message="Report deleted.")
