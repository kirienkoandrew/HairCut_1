from django.urls import path

from .views import MasterDashboardView, MasterRegistrationView

app_name = "masters"

urlpatterns = [
    path("register/", MasterRegistrationView.as_view(), name="register"),
    path("dashboard/", MasterDashboardView.as_view(), name="dashboard"),
]

