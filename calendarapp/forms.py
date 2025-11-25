from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from clients.models import Client
from masters.models import MasterProfile

from .models import Appointment


def build_duration_choices():
    choices = [(minutes, f"{minutes} мин.") for minutes in range(15, 75, 15)]
    for minutes in range(90, 601, 30):
        hours = minutes // 60
        remainder = minutes % 60
        if remainder:
            label = f"{hours} ч. {remainder} мин."
        else:
            label = f"{hours} ч."
        choices.append((minutes, label))
    return choices


class AppointmentForm(forms.ModelForm):
    """Form to book a client for a specific master slot."""

    DURATION_CHOICES = build_duration_choices()

    client_phone = forms.RegexField(
        label="Телефон клиента",
        regex=r"^\+?\d{10,15}$",
        error_messages={"invalid": "Введите телефон в формате +71234567890"},
    )
    service_date = forms.DateField(widget=forms.HiddenInput())
    start_time = forms.ChoiceField(label="Время начала")
    duration_minutes = forms.ChoiceField(
        label="Потребуется времени",
        choices=DURATION_CHOICES,
    )

    class Meta:
        model = Appointment
        fields = ("client_name", "client_phone", "service_date", "start_time", "duration_minutes", "notes")
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, master: MasterProfile, service_date, **kwargs):
        self.master = master
        self.service_date = service_date
        super().__init__(*args, **kwargs)
        self.fields["service_date"].initial = service_date
        self.fields["start_time"].choices = self._build_time_choices()

    def _build_time_choices(self):
        start = datetime.combine(datetime.today().date(), self.master.work_start)
        end = datetime.combine(datetime.today().date(), self.master.work_end)
        delta = timedelta(minutes=15)
        choices = []
        current = start
        while current < end:
            choices.append((current.strftime("%H:%M"), current.strftime("%H:%M")))
            current += delta
        return choices

    def save(self, commit=True):
        appointment = super().save(commit=False)
        appointment.master = self.master
        client, _ = Client.objects.get_or_create(
            phone=self.cleaned_data["client_phone"],
            defaults={
                "full_name": self.cleaned_data["client_name"],
            },
        )
        if client.full_name != self.cleaned_data["client_name"]:
            client.full_name = self.cleaned_data["client_name"]
            client.save(update_fields=["full_name"])

        appointment.client = client
        appointment.client_name = client.full_name
        appointment.client_phone = client.phone

        service_date = self.cleaned_data["service_date"]
        start_time_str = self.cleaned_data["start_time"]
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        start_dt_naive = datetime.combine(service_date, start_time)
        appointment.starts_at = timezone.make_aware(start_dt_naive, timezone.get_current_timezone())

        duration = int(self.cleaned_data["duration_minutes"])
        appointment.ends_at = appointment.starts_at + timedelta(minutes=duration)

        if commit:
            appointment.save()
        return appointment

