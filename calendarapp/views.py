import calendar
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View

from masters.models import MasterProfile

from .forms import AppointmentForm
from .models import Appointment


class MasterProfileRequiredMixin(LoginRequiredMixin):
    """Ensure the authenticated user has a master profile."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, "masterprofile"):
            return redirect("masters:register")

        self.master_profile = request.user.masterprofile
        return super().dispatch(request, *args, **kwargs)


class MasterCalendarView(MasterProfileRequiredMixin, View):
    template_name = "calendarapp/calendar.html"

    def get(self, request):
        today = timezone.localdate()
        selected_date = self._get_selected_date(request, fallback=today)
        month_anchor = self._get_month_anchor(request, selected_date)

        cal = calendar.Calendar(firstweekday=0)
        month_grid = cal.monthdatescalendar(month_anchor.year, month_anchor.month)

        start_range = month_grid[0][0]
        end_range = month_grid[-1][-1]

        appointments = (
            Appointment.objects.filter(
                master=self.master_profile,
                starts_at__date__range=(start_range, end_range),
            )
            .select_related("client")
            .order_by("starts_at")
        )

        appointments_by_day = {}
        for appointment in appointments:
            day = appointment.starts_at.date()
            appointments_by_day.setdefault(day, []).append(appointment)

        if selected_date < start_range or selected_date > end_range:
            selected_date = month_anchor

        weeks = []
        for week in month_grid:
            week_cells = []
            for day in week:
                week_cells.append(
                    {
                        "date": day,
                        "in_month": day.month == month_anchor.month,
                        "is_today": day == today,
                        "is_selected": day == selected_date,
                        "count": len(appointments_by_day.get(day, [])),
                        "url": f"?month={month_anchor:%Y-%m}&date={day:%Y-%m-%d}",
                    }
                )
            weeks.append(week_cells)

        prev_month = (month_anchor - timedelta(days=1)).replace(day=1)
        next_month = (month_anchor.replace(day=28) + timedelta(days=4)).replace(day=1)

        context = {
            "master": self.master_profile,
            "weeks": weeks,
            "current_month_label": month_anchor.strftime("%B %Y"),
            "prev_month_url": f"?month={prev_month:%Y-%m}&date={prev_month:%Y-%m-%d}",
            "next_month_url": f"?month={next_month:%Y-%m}&date={next_month:%Y-%m-%d}",
            "selected_date": selected_date,
            "selected_appointments": appointments_by_day.get(selected_date, []),
            "can_manage": self.master_profile.status == MasterProfile.Status.ACTIVE,
            "add_appointment_url": f"{reverse_lazy('calendar:add')}?date={selected_date:%Y-%m-%d}",
            "weekdays": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        }
        return render(request, self.template_name, context)

    @staticmethod
    def _get_selected_date(request, fallback: date) -> date:
        raw_value = request.GET.get("date")
        if not raw_value:
            return fallback
        try:
            year, month, day = map(int, raw_value.split("-"))
            return date(year, month, day)
        except ValueError:
            return fallback

    @staticmethod
    def _get_month_anchor(request, selected: date) -> date:
        raw = request.GET.get("month")
        if raw:
            try:
                year, month = map(int, raw.split("-"))
                return date(year, month, 1)
            except ValueError:
                pass
        return selected.replace(day=1)


class AppointmentCreateView(MasterProfileRequiredMixin, View):
    template_name = "calendarapp/appointment_form.html"
    success_url = reverse_lazy("calendar:list")

    def _resolve_service_date(self, request):
        date_str = request.GET.get("date") or request.POST.get("service_date")
        if date_str:
            try:
                year, month, day = map(int, date_str.split("-"))
                return date(year, month, day)
            except ValueError:
                pass
        return timezone.localdate()

    def get(self, request):
        if self.master_profile.status != MasterProfile.Status.ACTIVE:
            return redirect("calendar:list")
        service_date = self._resolve_service_date(request)
        form = AppointmentForm(master=self.master_profile, service_date=service_date)
        return render(
            request,
            self.template_name,
            {"form": form, "service_date": service_date},
        )

    def post(self, request):
        if self.master_profile.status != MasterProfile.Status.ACTIVE:
            return redirect("calendar:list")
        service_date = self._resolve_service_date(request)
        form = AppointmentForm(request.POST, master=self.master_profile, service_date=service_date)
        if form.is_valid():
            appointment = form.save()
            appointment.created_by = request.user
            appointment.save(update_fields=["created_by"])
            return redirect(self.success_url)
        return render(
            request,
            self.template_name,
            {"form": form, "service_date": service_date},
        )

# Create your views here.
