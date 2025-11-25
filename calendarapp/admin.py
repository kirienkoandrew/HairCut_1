from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("master", "client_name", "starts_at", "ends_at")
    search_fields = ("client_name", "client_phone", "notes")
    list_filter = ("master",)
