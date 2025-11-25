from django.contrib import admin
from django.utils import timezone

from .models import MasterProfile, Profession


@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.action(description="Активировать выбранных мастеров")
def activate_masters(modeladmin, request, queryset):
    queryset.filter(status=MasterProfile.Status.PENDING).update(
        status=MasterProfile.Status.ACTIVE,
        approved_at=timezone.now(),
    )


@admin.register(MasterProfile)
class MasterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "profession", "phone", "status", "created_at")
    list_filter = ("status", "profession")
    search_fields = ("user__email", "user__first_name", "user__last_name", "phone")
    actions = [activate_masters]
