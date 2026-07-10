from django.urls import path

from .views import (ExchangeAccountBalancesView, ExchangeAccountDetailView,
                    ExchangeAccountListCreateView, ExchangeAccountSyncView,
                    ExchangeAccountTestView, ExchangeDetailView,
                    ExchangeListView)

urlpatterns = [
    path("", ExchangeListView.as_view(), name="exchange-list"),
    path("<str:pk>/", ExchangeDetailView.as_view(), name="exchange-detail"),
    path(
        "accounts/",
        ExchangeAccountListCreateView.as_view(),
        name="exchange-account-list",
    ),
    path(
        "accounts/<str:pk>/",
        ExchangeAccountDetailView.as_view(),
        name="exchange-account-detail",
    ),
    path(
        "accounts/<str:pk>/test/",
        ExchangeAccountTestView.as_view(),
        name="exchange-account-test",
    ),
    path(
        "accounts/<str:pk>/sync/",
        ExchangeAccountSyncView.as_view(),
        name="exchange-account-sync",
    ),
    path(
        "accounts/<str:pk>/balances/",
        ExchangeAccountBalancesView.as_view(),
        name="exchange-account-balances",
    ),
]
