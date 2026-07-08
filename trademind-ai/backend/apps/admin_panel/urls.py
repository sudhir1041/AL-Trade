from django.urls import path
from .views import (
    AdminUserListView, AdminUserDetailView, AdminSystemView,
    AdminWorkerStatusView, AdminQueueStatusView, AdminLogsView, AdminSettingsView,
)

urlpatterns = [
    path("users/",            AdminUserListView.as_view(),    name="admin-users"),
    path("users/<str:pk>/",   AdminUserDetailView.as_view(),  name="admin-user-detail"),
    path("system/",           AdminSystemView.as_view(),      name="admin-system"),
    path("workers/",          AdminWorkerStatusView.as_view(), name="admin-workers"),
    path("queues/",           AdminQueueStatusView.as_view(), name="admin-queues"),
    path("logs/",             AdminLogsView.as_view(),        name="admin-logs"),
    path("settings/",         AdminSettingsView.as_view(),    name="admin-settings"),
]
