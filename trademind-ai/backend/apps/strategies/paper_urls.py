"""Paper trading URL patterns — /api/v1/paper/"""
from django.urls import path
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.request import Request
from core.responses import success_response, error_response


class PaperStartView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request: Request):
        # Enable paper mode on all user strategies
        from apps.strategies.models import UserStrategy
        UserStrategy.objects.filter(user=request.user).update(is_paper_mode=True)
        return success_response(message="Paper trading mode enabled on all strategies.")


class PaperStopView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request: Request):
        from apps.strategies.models import UserStrategy
        UserStrategy.objects.filter(user=request.user).update(is_paper_mode=False)
        return success_response(message="Paper trading mode disabled.")


class PaperResetView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request: Request):
        from apps.orders.models import Order, Position
        Order.objects.filter(user=request.user, is_paper_trade=True).delete()
        Position.objects.filter(user=request.user, is_paper_trade=True).delete()
        return success_response(message="Paper trading history cleared.")


urlpatterns = [
    path("start/",  PaperStartView.as_view(),  name="paper-start"),
    path("stop/",   PaperStopView.as_view(),   name="paper-stop"),
    path("reset/",  PaperResetView.as_view(),  name="paper-reset"),
]
