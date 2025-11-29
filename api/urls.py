from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, ClientViewSet, CustomAuthToken, MasterProfileView

app_name = "api"

router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")
router.register(r"clients", ClientViewSet, basename="client")

urlpatterns = [
    path("auth/token/", CustomAuthToken.as_view(), name="auth-token"),
    path("masters/me/", MasterProfileView.as_view(), name="master-profile"),
    path("", include(router.urls)),
]

