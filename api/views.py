from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from calendarapp.models import Appointment
from clients.models import Client
from masters.models import MasterProfile

from .permissions import IsMasterUser
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    ClientSerializer,
    MasterProfileSerializer,
)


class CustomAuthToken(ObtainAuthToken):
    """Return auth token plus basic profile info."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data["token"])
        user = token.user
        payload = {"token": token.key, "email": user.email, "user_id": user.id}
        if hasattr(user, "masterprofile"):
            payload["master_id"] = user.masterprofile.id
        return Response(payload)


class MasterProfileView(APIView):
    permission_classes = [IsMasterUser]

    def get(self, request):
        serializer = MasterProfileSerializer(request.user.masterprofile)
        return Response(serializer.data)


class AppointmentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsMasterUser]

    def get_queryset(self):
        qs = (
            Appointment.objects.filter(master=self.request.user.masterprofile)
            .select_related("client")
            .order_by("starts_at")
        )
        date_param = self.request.query_params.get("date")
        if date_param:
            try:
                target = datetime.strptime(date_param, "%Y-%m-%d").date()
                qs = qs.filter(starts_at__date=target)
            except ValueError:
                pass
        return qs

    def create(self, request, *args, **kwargs):
        serializer = AppointmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        master = request.user.masterprofile
        data = serializer.validated_data

        # Validate start time range
        start_time = data["start_time"]
        work_start = master.work_start
        work_end = master.work_end
        if not (work_start <= start_time < work_end):
            return Response(
                {"start_time": "Время должно быть в пределах рабочего дня мастера."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (datetime.combine(datetime.today(), start_time) - datetime.combine(datetime.today(), work_start)).seconds % (
            15 * 60
        ):
            return Response(
                {"start_time": "Можно выбирать время только с шагом 15 минут."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_date = data["service_date"]
        start_dt_naive = datetime.combine(service_date, start_time)
        start_dt = timezone.make_aware(start_dt_naive, timezone.get_current_timezone())
        duration = data["duration_minutes"]
        end_dt = start_dt + timedelta(minutes=duration)

        client, _ = Client.objects.get_or_create(
            phone=data["client_phone"],
            defaults={"full_name": data["client_name"]},
        )
        if client.full_name != data["client_name"]:
            client.full_name = data["client_name"]
            client.save(update_fields=["full_name"])

        appointment = Appointment.objects.create(
            master=master,
            client=client,
            client_name=client.full_name,
            client_phone=client.phone,
            starts_at=start_dt,
            ends_at=end_dt,
            notes=data.get("notes", ""),
            created_by=request.user,
        )

        output = AppointmentSerializer(appointment)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class ClientViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsMasterUser]

    def get_queryset(self):
        master = self.request.user.masterprofile
        client_ids = master.appointments.values_list("client_id", flat=True)
        return Client.objects.filter(id__in=client_ids)

    @action(detail=True, methods=["get"])
    def appointments(self, request, pk=None):
        client = self.get_object()
        appointments = client.appointments.filter(master=request.user.masterprofile).order_by("-starts_at")
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

# Create your views here.
