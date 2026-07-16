"""
TradeMind AI - Core Abstract Base Models
==========================================
All application models should inherit from BaseModel (or TenantBaseModel for
multi-tenant entities) to guarantee a consistent schema:

    - UUID primary key
    - Tenant isolation via tenant_id
    - Automatic created_at / updated_at timestamps
    - Auditable created_by / updated_by fields
    - Optimistic-locking via version counter
    - Non-destructive soft-delete via deleted_at / SoftDeleteManager
"""

import uuid
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Managers
# ---------------------------------------------------------------------------

class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that understands soft-delete semantics."""

    def alive(self):
        """Return only records that have NOT been soft-deleted."""
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        """Return only records that HAVE been soft-deleted."""
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        """Bulk soft-delete: sets deleted_at on all matching records."""
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently remove records from the database (use with caution)."""
        return super().delete()

    def restore(self):
        """Undo a soft-delete on all matching records."""
        return self.update(deleted_at=None)


class SoftDeleteManager(models.Manager):
    """
    Default manager that automatically excludes soft-deleted records.

    Usage:
        MyModel.objects.all()           → only alive records
        MyModel.objects.deleted()       → only deleted records
        MyModel.all_objects.all()       → all records (bypass soft-delete)
    """

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def alive(self):
        return self.get_queryset().alive()

    def deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()

    def with_deleted(self):
        """Return all records, including soft-deleted ones."""
        return SoftDeleteQuerySet(self.model, using=self._db)


class AllObjectsManager(models.Manager):
    """
    Unfiltered manager — exposes every row, including soft-deleted ones.
    Attached as `all_objects` on BaseModel.
    """

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


# ---------------------------------------------------------------------------
# Abstract Base Model
# ---------------------------------------------------------------------------

class BaseModel(models.Model):
    """
    Abstract foundation for every TradeMind AI model.

    Fields
    ------
    id          : UUID v4 primary key (no auto-increment integer leak)
    tenant_id   : UUID that scopes the record to a specific tenant
    created_at  : Timestamp set once on INSERT
    updated_at  : Timestamp updated on every SAVE
    created_by  : UUID of the user who created the record (nullable)
    updated_by  : UUID of the user who last modified the record (nullable)
    version     : Monotonically increasing integer for optimistic locking
    deleted_at  : Soft-delete timestamp; NULL means the record is alive

    Managers
    --------
    objects     : SoftDeleteManager  — the default; hides soft-deleted rows
    all_objects : AllObjectsManager  — includes soft-deleted rows

    Properties
    ----------
    is_deleted  : bool — True when deleted_at is set

    Methods
    -------
    soft_delete(deleted_by=None)  : Mark record as deleted
    restore()                     : Undo soft-delete
    """

    # ── Primary key ─────────────────────────────────────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
        help_text="Unique identifier (UUID v4).",
    )

    # ── Multi-tenancy ────────────────────────────────────────────────────────
    tenant_id = models.UUIDField(
        db_index=True,
        null=False,
        blank=False,
        verbose_name="Tenant ID",
        help_text="The tenant this record belongs to.",
    )

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        db_index=True,
        verbose_name="Created At",
        help_text="Timestamp when the record was created (UTC).",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name="Updated At",
        help_text="Timestamp of the last update (UTC).",
    )

    # ── Audit ────────────────────────────────────────────────────────────────
    created_by = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="Created By",
        help_text="UUID of the user who created this record.",
    )
    updated_by = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="Updated By",
        help_text="UUID of the user who last modified this record.",
    )

    # ── Optimistic locking ───────────────────────────────────────────────────
    version = models.PositiveIntegerField(
        default=1,
        verbose_name="Version",
        help_text=(
            "Monotonically increasing version counter used for optimistic locking. "
            "Increment this on every meaningful business-logic save."
        ),
    )

    # ── Soft delete ──────────────────────────────────────────────────────────
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Deleted At",
        help_text="Non-null when the record has been soft-deleted (UTC).",
    )

    # ── Managers ─────────────────────────────────────────────────────────────
    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    # ── Meta ─────────────────────────────────────────────────────────────────
    class Meta:
        abstract = True
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "-created_at"]),
            models.Index(fields=["tenant_id", "deleted_at"]),
        ]

    # ── Properties ───────────────────────────────────────────────────────────
    @property
    def is_deleted(self) -> bool:
        """Return True if this record has been soft-deleted."""
        return self.deleted_at is not None

    # ── Soft-delete helpers ──────────────────────────────────────────────────
    def soft_delete(self, deleted_by: uuid.UUID | None = None) -> None:
        """
        Soft-delete this record by setting deleted_at to the current UTC time.

        Parameters
        ----------
        deleted_by : UUID, optional
            UUID of the user performing the deletion (stored in updated_by).
        """
        if self.is_deleted:
            return  # idempotent — already deleted

        now = timezone.now()
        self.deleted_at = now
        self.updated_at = now
        if deleted_by is not None:
            self.updated_by = deleted_by
        self.save(update_fields=["deleted_at", "updated_at", "updated_by"])

    def restore(self, restored_by: uuid.UUID | None = None) -> None:
        """
        Restore a soft-deleted record by clearing deleted_at.

        Parameters
        ----------
        restored_by : UUID, optional
            UUID of the user performing the restore (stored in updated_by).
        """
        if not self.is_deleted:
            return  # idempotent — not deleted

        now = timezone.now()
        self.deleted_at = None
        self.updated_at = now
        if restored_by is not None:
            self.updated_by = restored_by
        self.save(update_fields=["deleted_at", "updated_at", "updated_by"])

    def increment_version(self) -> None:
        """Atomically increment the optimistic-lock version counter."""
        self.__class__.objects.filter(pk=self.pk).update(
            version=models.F("version") + 1
        )
        self.refresh_from_db(fields=["version"])

    # ── String representation ────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} "
            f"tenant={self.tenant_id} deleted={self.is_deleted}>"
        )

    def __str__(self) -> str:
        return str(self.id)


# ---------------------------------------------------------------------------
# Tenant-aware abstract model (convenience alias with enforced tenant_id)
# ---------------------------------------------------------------------------

class TenantBaseModel(BaseModel):
    """
    Identical to BaseModel but signals intent that this model is strictly
    scoped to a single tenant. Application code can use this as a semantic
    marker to differentiate platform-wide records (BaseModel) from
    per-tenant records (TenantBaseModel).
    """

    class Meta(BaseModel.Meta):
        abstract = True


# ---------------------------------------------------------------------------
# Named mixin — adds a human-readable name / description pair
# ---------------------------------------------------------------------------

class NamedMixin(models.Model):
    """
    Mixin that adds `name` and `description` to any model.
    Combine with BaseModel via multiple inheritance.
    """

    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Name",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Description",
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Status mixin — adds a generic is_active flag
# ---------------------------------------------------------------------------

class ActiveMixin(models.Model):
    """Mixin that adds an `is_active` boolean flag."""

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Is Active",
        help_text="Inactive records are hidden from regular API responses.",
    )

    class Meta:
        abstract = True
