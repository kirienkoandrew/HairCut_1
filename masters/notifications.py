from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


def notify_master_registration(profile):
    """Send confirmation message to the master after submitting the form."""
    subject = "Заявка получена"
    message = (
        f"Здравствуйте, {profile.user.first_name}!\n\n"
        "Мы получили вашу заявку и скоро свяжемся с вами после проверки данных."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [profile.user.email])


def notify_admin_about_master(profile, request=None):
    """Ping project administrators about the new master."""
    subject = "Новая заявка мастера"
    dashboard_url = ""
    if request:
        dashboard_url = request.build_absolute_uri(reverse("admin:masters_masterprofile_change", args=[profile.pk]))

    message = (
        f"Новая заявка от {profile.user} ({profile.profession.name}).\n"
        f"Телефон: {profile.phone}\n"
        f"Рабочее время: {profile.work_start} - {profile.work_end}\n"
        f"Подробнее: {profile.about or 'не указано'}\n\n"
    )
    if dashboard_url:
        message += f"Ссылка: {dashboard_url}"

    recipient_list = [email for _, email in settings.ADMINS]
    if recipient_list:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

