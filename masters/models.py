from django.conf import settings
from django.db import models


class Profession(models.Model):
    """Specialization offered by a master (hairdresser, manicurist, etc.)."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class MasterProfile(models.Model):
    """Profile with onboarding/approval workflow for service masters."""

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает подтверждения"
        ACTIVE = "active", "Активирован"
        REJECTED = "rejected", "Отклонен"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profession = models.ForeignKey(Profession, on_delete=models.PROTECT, related_name="masters")
    phone = models.CharField(max_length=32)
    about = models.TextField(blank=True)
    work_start = models.TimeField(help_text="Например, 09:00")
    work_end = models.TimeField(help_text="Например, 18:00")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user} · {self.profession.name}"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE
