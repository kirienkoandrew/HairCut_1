from django.urls import path

from .views import AppointmentCreateView, MasterCalendarView

app_name = "calendar"

urlpatterns = [
    path("", MasterCalendarView.as_view(), name="list"),
    path("appointments/add/", AppointmentCreateView.as_view(), name="add"),
]

