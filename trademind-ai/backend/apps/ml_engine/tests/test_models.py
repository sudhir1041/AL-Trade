import pytest

from apps.ml_engine.models import FeatureStore, ModelRegistry


@pytest.mark.django_db
def test_model_registry_creation():
    model = ModelRegistry.objects.create(model_id="test-model", version="1.0")
    assert model.model_id == "test-model"
    assert model.version == "1.0"
    assert model.approval_status == "PENDING"


@pytest.mark.django_db
def test_feature_store_creation():
    store = FeatureStore.objects.create(version="1.0")
    assert store.version == "1.0"
