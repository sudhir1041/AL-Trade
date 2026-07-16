from django.urls import path
from .views import (
    UserMeView, UserProfilePictureView,
    UserPreferencesView, UserSecurityView, UserActivityView,
)

urlpatterns = [
    path("me/",          UserMeView.as_view(),             name="user-me"),
    path("me/picture/",  UserProfilePictureView.as_view(), name="user-picture"),
    path("preferences/", UserPreferencesView.as_view(),    name="user-preferences"),
    path("security/",    UserSecurityView.as_view(),       name="user-security"),
    path("activity/",    UserActivityView.as_view(),       name="user-activity"),
]
