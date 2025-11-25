from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import MasterRegistrationForm
from .models import MasterProfile


class MasterRegistrationView(View):
    template_name = "masters/register_master.html"
    success_url = reverse_lazy("masters:dashboard")

    def get(self, request):
        form = MasterRegistrationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = MasterRegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save(request=request)
            login(request, profile.user)
            return redirect(self.success_url)
        return render(request, self.template_name, {"form": form})


class MasterDashboardView(View):
    template_name = "masters/dashboard.html"
    form_class = AuthenticationForm

    def get(self, request):
        if not request.user.is_authenticated:
            form = self.form_class(request=request)
            return render(request, self.template_name, {"login_form": form})

        profile = getattr(request.user, "masterprofile", None)
        if not profile:
            return redirect("masters:register")

        context = {
            "profile": profile,
            "is_pending": profile.status == MasterProfile.Status.PENDING,
            "is_active": profile.status == MasterProfile.Status.ACTIVE,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("masters:dashboard")

        form = self.form_class(request=request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("masters:dashboard")
        return render(request, self.template_name, {"login_form": form})
