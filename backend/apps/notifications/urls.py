from django.urls import path
from .views import NotificationListView, NotificationMarkReadView, NotificationDeleteView

urlpatterns = [
    path("",           NotificationListView.as_view(),    name="notification-list"),
    path("read/",      NotificationMarkReadView.as_view(), name="notification-read"),
    path("<str:pk>/",  NotificationDeleteView.as_view(),  name="notification-delete"),
]
