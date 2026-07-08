"""Backtest URL patterns — /api/v1/backtest/"""
from django.urls import path
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.request import Request
from core.responses import success_response, error_response
from .models import BacktestJob
from .serializers import BacktestJobSerializer
from common.utils import paginate_queryset


class BacktestListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request: Request):
        qs    = BacktestJob.objects.filter(user=request.user).order_by("-created_at")
        paged = paginate_queryset(qs, int(request.query_params.get("page", 1)), 20)
        return success_response(
            data=BacktestJobSerializer(paged["results"], many=True).data,
            meta={"total": paged["count"]},
        )


class BacktestDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request: Request, pk: str):
        try:
            job = BacktestJob.objects.get(pk=pk, user=request.user)
        except BacktestJob.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Backtest job not found.", status_code=404)
        return success_response(data=BacktestJobSerializer(job).data)

    def delete(self, request: Request, pk: str):
        try:
            job = BacktestJob.objects.get(pk=pk, user=request.user)
        except BacktestJob.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Backtest job not found.", status_code=404)
        job.delete()
        return success_response(message="Backtest deleted.")


urlpatterns = [
    path("",          BacktestListView.as_view(),   name="backtest-list"),
    path("<str:pk>/", BacktestDetailView.as_view(), name="backtest-detail"),
]
