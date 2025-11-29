from rest_framework import serializers

from calendarapp.models import Appointment
from clients.models import Client
from masters.models import MasterProfile, Profession


class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ("id", "name", "slug", "description")


class MasterProfileSerializer(serializers.ModelSerializer):
    profession = ProfessionSerializer()

    class Meta:
        model = MasterProfile
        fields = (
            "id",
            "status",
            "phone",
            "about",
            "work_start",
            "work_end",
            "profession",
        )


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ("id", "full_name", "phone", "email", "notes")


class AppointmentSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    master = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id",
            "master",
            "starts_at",
            "ends_at",
            "client",
            "client_name",
            "client_phone",
            "notes",
        )


class AppointmentCreateSerializer(serializers.Serializer):
    client_name = serializers.CharField(max_length=150)
    client_phone = serializers.RegexField(regex=r"^\+?\d{10,15}$")
    notes = serializers.CharField(required=False, allow_blank=True)
    service_date = serializers.DateField()
    start_time = serializers.TimeField()
    duration_minutes = serializers.IntegerField(min_value=15, max_value=600)


