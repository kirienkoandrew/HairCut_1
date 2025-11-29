from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from calendarapp.models import Appointment
from clients.models import Client
from masters.models import MasterProfile, Profession

User = get_user_model()


class AuthenticationAPITestCase(APITestCase):
    """Test token-based authentication."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="master@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Master",
        )
        self.profession = Profession.objects.create(
            name="Парикмахер",
            slug="hairdresser",
        )
        self.master_profile = MasterProfile.objects.create(
            user=self.user,
            profession=self.profession,
            phone="+71234567890",
            work_start=time(9, 0),
            work_end=time(18, 0),
            status=MasterProfile.Status.ACTIVE,
        )

    def test_get_token_with_valid_credentials(self):
        """Test obtaining auth token with valid email/password."""
        url = reverse("api:auth-token")
        data = {"username": "master@test.com", "password": "testpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user_id", response.data)
        self.assertIn("master_id", response.data)
        self.assertEqual(response.data["master_id"], self.master_profile.id)

    def test_get_token_with_invalid_credentials(self):
        """Test token endpoint rejects invalid credentials."""
        url = reverse("api:auth-token")
        data = {"username": "master@test.com", "password": "wrongpass"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_token_without_master_profile(self):
        """Test token endpoint works even if user has no master profile."""
        user2 = User.objects.create_user(
            email="regular@test.com",
            password="testpass123",
        )
        url = reverse("api:auth-token")
        data = {"username": "regular@test.com", "password": "testpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIsNone(response.data.get("master_id"))


class MasterProfileAPITestCase(APITestCase):
    """Test master profile endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="master@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Master",
        )
        self.profession = Profession.objects.create(
            name="Парикмахер",
            slug="hairdresser",
        )
        self.master_profile = MasterProfile.objects.create(
            user=self.user,
            profession=self.profession,
            phone="+71234567890",
            work_start=time(9, 0),
            work_end=time(18, 0),
            status=MasterProfile.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.user)

    def test_get_master_profile(self):
        """Test retrieving master profile."""
        url = reverse("api:master-profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.master_profile.id)
        self.assertEqual(response.data["status"], "active")
        self.assertEqual(response.data["profession"]["name"], "Парикмахер")
        self.assertEqual(response.data["work_start"], "09:00:00")
        self.assertEqual(response.data["work_end"], "18:00:00")

    def test_get_master_profile_requires_authentication(self):
        """Test that unauthenticated requests are rejected."""
        self.client.force_authenticate(user=None)
        url = reverse("api:master-profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AppointmentAPITestCase(APITestCase):
    """Test appointment CRUD operations."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="master@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Master",
        )
        self.profession = Profession.objects.create(
            name="Парикмахер",
            slug="hairdresser",
        )
        self.master_profile = MasterProfile.objects.create(
            user=self.user,
            profession=self.profession,
            phone="+71234567890",
            work_start=time(9, 0),
            work_end=time(18, 0),
            status=MasterProfile.Status.ACTIVE,
        )
        self.client_obj = Client.objects.create(
            full_name="Иван Иванов",
            phone="+79991234567",
        )
        self.client.force_authenticate(user=self.user)

    def test_create_appointment(self):
        """Test creating a new appointment."""
        url = reverse("api:appointment-list")
        tomorrow = timezone.localdate() + timedelta(days=1)
        data = {
            "client_name": "Петр Петров",
            "client_phone": "+79991234568",
            "service_date": tomorrow.strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "duration_minutes": "30",
            "notes": "Стрижка",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.master, self.master_profile)
        self.assertEqual(appointment.client_name, "Петр Петров")
        self.assertIsNotNone(appointment.client)
        self.assertEqual(appointment.client.phone, "+79991234568")

    def test_create_appointment_creates_client(self):
        """Test that creating appointment auto-creates client if not exists."""
        url = reverse("api:appointment-list")
        tomorrow = timezone.localdate() + timedelta(days=1)
        initial_count = Client.objects.count()
        data = {
            "client_name": "Новый Клиент",
            "client_phone": "+79999999999",
            "service_date": tomorrow.strftime("%Y-%m-%d"),
            "start_time": "11:00",
            "duration_minutes": "45",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), initial_count + 1)
        new_client = Client.objects.get(phone="+79999999999")
        self.assertEqual(new_client.full_name, "Новый Клиент")

    def test_list_appointments(self):
        """Test listing appointments for authenticated master."""
        today = timezone.localdate()
        appointment1 = Appointment.objects.create(
            master=self.master_profile,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 30))
            ),
        )
        tomorrow = today + timedelta(days=1)
        appointment2 = Appointment.objects.create(
            master=self.master_profile,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(tomorrow, time(14, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(tomorrow, time(15, 0))
            ),
        )

        url = reverse("api:appointment-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_appointments_by_date(self):
        """Test filtering appointments by specific date."""
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        Appointment.objects.create(
            master=self.master_profile,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 30))
            ),
        )
        Appointment.objects.create(
            master=self.master_profile,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(tomorrow, time(14, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(tomorrow, time(15, 0))
            ),
        )

        url = reverse("api:appointment-list")
        response = self.client.get(url, {"date": today.strftime("%Y-%m-%d")})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["starts_at"][:10], today.strftime("%Y-%m-%d")
        )

    def test_create_appointment_outside_work_hours(self):
        """Test that appointments outside work hours are rejected."""
        url = reverse("api:appointment-list")
        tomorrow = timezone.localdate() + timedelta(days=1)
        data = {
            "client_name": "Клиент",
            "client_phone": "+79991234568",
            "service_date": tomorrow.strftime("%Y-%m-%d"),
            "start_time": "20:00",  # After work_end (18:00)
            "duration_minutes": "30",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_appointment_requires_authentication(self):
        """Test that unauthenticated users cannot create appointments."""
        self.client.force_authenticate(user=None)
        url = reverse("api:appointment-list")
        tomorrow = timezone.localdate() + timedelta(days=1)
        data = {
            "client_name": "Клиент",
            "client_phone": "+79991234568",
            "service_date": tomorrow.strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "duration_minutes": "30",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ClientAPITestCase(APITestCase):
    """Test client detail and history endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="master@test.com",
            password="testpass123",
        )
        self.profession = Profession.objects.create(
            name="Парикмахер",
            slug="hairdresser",
        )
        self.master_profile = MasterProfile.objects.create(
            user=self.user,
            profession=self.profession,
            phone="+71234567890",
            work_start=time(9, 0),
            work_end=time(18, 0),
            status=MasterProfile.Status.ACTIVE,
        )
        self.client_obj = Client.objects.create(
            full_name="Иван Иванов",
            phone="+79991234567",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_client_detail(self):
        """Test retrieving client details."""
        # Create an appointment so client is accessible to this master
        today = timezone.localdate()
        Appointment.objects.create(
            master=self.master_profile,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 30))
            ),
        )
        url = reverse("api:client-detail", kwargs={"pk": self.client_obj.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.client_obj.id)
        self.assertEqual(response.data["full_name"], "Иван Иванов")
        self.assertEqual(response.data["phone"], "+79991234567")

    def test_get_client_appointment_history(self):
        """Test retrieving client's appointment history."""
        today = timezone.localdate()
        appointment1 = Appointment.objects.create(
            master=self.master_profile,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 30))
            ),
        )
        yesterday = today - timedelta(days=1)
        appointment2 = Appointment.objects.create(
            master=self.master_profile,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(yesterday, time(14, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(yesterday, time(15, 0))
            ),
        )

        url = reverse("api:client-appointments", kwargs={"pk": self.client_obj.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Should be ordered by starts_at descending (most recent first)
        self.assertGreater(
            response.data[0]["starts_at"], response.data[1]["starts_at"]
        )

    def test_client_history_only_shows_current_master_appointments(self):
        """Test that client history only shows appointments for current master."""
        other_user = User.objects.create_user(
            email="other@test.com",
            password="testpass123",
        )
        other_master = MasterProfile.objects.create(
            user=other_user,
            profession=self.profession,
            phone="+79999999999",
            work_start=time(9, 0),
            work_end=time(18, 0),
            status=MasterProfile.Status.ACTIVE,
        )

        today = timezone.localdate()
        # Appointment with current master
        Appointment.objects.create(
            master=self.master_profile,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(today, time(10, 30))
            ),
        )
        # Appointment with other master
        Appointment.objects.create(
            master=other_master,
            client=self.client_obj,
            client_name=self.client_obj.full_name,
            client_phone=self.client_obj.phone,
            starts_at=timezone.make_aware(
                timezone.datetime.combine(today, time(14, 0))
            ),
            ends_at=timezone.make_aware(
                timezone.datetime.combine(today, time(15, 0))
            ),
        )

        url = reverse("api:client-appointments", kwargs={"pk": self.client_obj.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["master"], self.master_profile.id)
