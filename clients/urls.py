from django.urls import path

from .views import ClientDetailView

app_name = "clients"

urlpatterns = [
    path("<int:pk>/", ClientDetailView.as_view(), name="detail"),
]

