from django.conf import settings
from django.db import models

from masters.models import MasterProfile
from clients.models import Client


class Appointment(models.Model):
    """Single slot in master's calendar."""

    master = models.ForeignKey(MasterProfile, on_delete=models.CASCADE, related_name="appointments")
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="appointments", null=True, blank=True)
    client_name = models.CharField(max_length=150)
    client_phone = models.CharField(max_length=32)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_appointments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("starts_at",)
        unique_together = ("master", "starts_at")

    def __str__(self) -> str:
        return f"{self.master} · {self.starts_at:%Y-%m-%d %H:%M}"

    def clean(self):
        if self.ends_at is None or self.starts_at is None:
            return
        if self.starts_at >= self.ends_at:
            raise ValueError("Время окончания должно быть позже начала.")
