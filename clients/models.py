from django.db import models


class Client(models.Model):
    """Customer who visits masters."""

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, unique=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("full_name",)

    def __str__(self):
        return f"{self.full_name} ({self.phone})"
from django.db import models

# Create your models here.
