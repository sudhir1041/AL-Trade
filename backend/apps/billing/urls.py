from django.urls import path
from .views import (
    PlanListView, SubscriptionView, SubscriptionCancelView,
    InvoiceListView, CouponValidateView,
)

urlpatterns = [
    path("plans/",                PlanListView.as_view(),          name="billing-plans"),
    path("subscription/",         SubscriptionView.as_view(),      name="billing-subscription"),
    path("subscription/cancel/",  SubscriptionCancelView.as_view(), name="billing-cancel"),
    path("invoices/",             InvoiceListView.as_view(),        name="billing-invoices"),
    path("coupons/validate/",     CouponValidateView.as_view(),     name="billing-coupon-validate"),
]
