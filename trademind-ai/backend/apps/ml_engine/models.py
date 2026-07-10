import uuid

from django.db import models


class ModelRegistry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_id = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    training_date = models.DateTimeField(auto_now_add=True)
    dataset_version = models.CharField(max_length=50, blank=True, null=True)
    hyperparams = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)
    approval_status = models.CharField(max_length=50, default="PENDING")
    rollback_ref = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Model Registry"
        verbose_name_plural = "Model Registries"

    def __str__(self):
        return f"{self.model_id} v{self.version}"


class FeatureStore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Feature Store"
        verbose_name_plural = "Feature Stores"

    def __str__(self):
        return f"FeatureStore v{self.version}"
