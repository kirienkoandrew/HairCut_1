from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from masters.models import MasterProfile

from .models import Client


class MasterProfileRequiredMixin(LoginRequiredMixin):
    """Ensure only authenticated masters access client history."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not hasattr(request.user, "masterprofile"):
            return redirect("masters:register")
        self.master_profile = request.user.masterprofile
        return super().dispatch(request, *args, **kwargs)


class ClientDetailView(MasterProfileRequiredMixin, View):
    template_name = "clients/client_detail.html"

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        appointments = (
            client.appointments.filter(master=self.master_profile)
            .select_related("master")
            .order_by("-starts_at")
        )
        if not appointments.exists():
            # Prevent masters from accessing foreign clients
            return redirect("calendar:list")
        return render(
            request,
            self.template_name,
            {
                "client": client,
                "appointments": appointments,
            },
        )
from django.shortcuts import render

# Create your views here.
