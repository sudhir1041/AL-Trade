from django.urls import path
from .views import (
    OrderListCreateView, OrderDetailView,
    PositionListView, PositionDetailView,
    PositionCloseView, PositionPartialCloseView,
    TradeHistoryView,
)

urlpatterns = [
    path("",                                    OrderListCreateView.as_view(),      name="order-list"),
    path("<str:pk>/",                           OrderDetailView.as_view(),          name="order-detail"),
    path("positions/",                          PositionListView.as_view(),         name="position-list"),
    path("positions/<str:pk>/",                 PositionDetailView.as_view(),       name="position-detail"),
    path("positions/<str:pk>/close/",           PositionCloseView.as_view(),        name="position-close"),
    path("positions/<str:pk>/partial-close/",   PositionPartialCloseView.as_view(), name="position-partial-close"),
    path("trades/",                             TradeHistoryView.as_view(),         name="trade-history"),
]
