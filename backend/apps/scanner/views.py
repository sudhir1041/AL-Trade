"""
apps/scanner/views.py
T5 ✅  Scanner REST endpoints (Vol.5 §8).
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from core.responses import error_response, success_response
from .models import ScannerJob, ScannerResult, ScannerSettings
from .serializers import ScannerJobSerializer, ScannerResultSerializer, ScannerSettingsSerializer


class ScannerRunView(APIView):
    """POST /api/v1/scanner/run/  — trigger manual scan"""
    permission_classes = [IsAuthenticated]
    def post(self, request: Request):
        from apps.scanner.tasks import run_market_scan
        run_market_scan.delay()
        return success_response(message="Market scan triggered.")


class ScannerStatusView(APIView):
    """GET /api/v1/scanner/status/"""
    permission_classes = [IsAuthenticated]
    def get(self, request: Request):
        latest = ScannerJob.objects.order_by("-created_at").first()
        if not latest:
            return success_response(data={"status": "NO_SCANS_YET"})
        return success_response(data=ScannerJobSerializer(latest).data)


class ScannerResultsView(APIView):
    """GET /api/v1/scanner/results/"""
    permission_classes = [IsAuthenticated]
    def get(self, request: Request):
        latest_job = ScannerJob.objects.filter(status="COMPLETED").order_by("-created_at").first()
        if not latest_job:
            return success_response(data=[], message="No scan results yet.")
        limit   = int(request.query_params.get("limit", 50))
        results = ScannerResult.objects.filter(
            scanner_job=latest_job
        ).select_related("trading_pair").order_by("-confidence_score")[:limit]
        return success_response(
            data=ScannerResultSerializer(results, many=True).data,
            meta={"job_id": str(latest_job.id), "scanned_at": latest_job.completed_at},
        )


class ScannerCandidatesView(APIView):
    """GET /api/v1/scanner/candidates/"""
    permission_classes = [IsAuthenticated]
    def get(self, request: Request):
        latest_job = ScannerJob.objects.filter(status="COMPLETED").order_by("-created_at").first()
        if not latest_job:
            return success_response(data=[])
        results = ScannerResult.objects.filter(
            scanner_job=latest_job, is_candidate=True
        ).select_related("trading_pair").order_by("-confidence_score")
        return success_response(data=ScannerResultSerializer(results, many=True).data)


class ScannerSettingsView(APIView):
    """GET/PATCH /api/v1/scanner/settings/"""
    permission_classes = [IsAuthenticated]
    def get(self, request: Request):
        settings, _ = ScannerSettings.objects.get_or_create(
            user=request.user,
            defaults={"tenant_id": request.user.tenant_id or request.user.id},
        )
        return success_response(data=ScannerSettingsSerializer(settings).data)

    def patch(self, request: Request):
        settings, _ = ScannerSettings.objects.get_or_create(
            user=request.user,
            defaults={"tenant_id": request.user.tenant_id or request.user.id},
        )
        serializer = ScannerSettingsSerializer(settings, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Invalid settings.", details=serializer.errors)
        serializer.save()
        return success_response(data=serializer.data, message="Scanner settings updated.")
