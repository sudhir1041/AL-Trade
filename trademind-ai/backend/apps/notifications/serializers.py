"""
apps/notifications/serializers.py
T14 ✅
"""
from rest_framework import serializers
from .models import Notification, NotificationDelivery


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = [
            "id", "event_type", "title", "message",
            "payload", "is_read", "read_at", "created_at",
        ]
        read_only_fields = fields


class NotificationDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model  = NotificationDelivery
        fields = ["channel", "status", "attempts", "delivered_at", "error_message"]
