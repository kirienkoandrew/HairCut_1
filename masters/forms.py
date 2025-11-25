from django import forms
from django.contrib.auth import get_user_model

from .models import MasterProfile, Profession
from .notifications import notify_admin_about_master, notify_master_registration


class MasterRegistrationForm(forms.Form):
    """Collect the minimum data for a master onboarding request."""

    first_name = forms.CharField(label="Имя", max_length=150)
    last_name = forms.CharField(label="Фамилия", max_length=150)
    email = forms.EmailField(label="E-mail")
    phone = forms.CharField(label="Телефон", max_length=32)
    profession = forms.ModelChoiceField(
        label="Профессия",
        queryset=Profession.objects.all(),
        empty_label="Выберите профессию",
    )
    work_start = forms.TimeField(
        label="Начало рабочего дня",
        widget=forms.TimeInput(format="%H:%M"),
        help_text="Формат ЧЧ:ММ",
    )
    work_end = forms.TimeField(
        label="Окончание рабочего дня",
        widget=forms.TimeInput(format="%H:%M"),
        help_text="Формат ЧЧ:ММ",
    )
    about = forms.CharField(
        label="Краткое описание услуг",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        user_model = get_user_model()
        if user_model.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким e-mail уже зарегистрирован.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        work_start = cleaned_data.get("work_start")
        work_end = cleaned_data.get("work_end")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Пароли должны совпадать.")

        if work_start and work_end and work_start >= work_end:
            self.add_error("work_end", "Конец рабочего дня должен быть позже начала.")

        return cleaned_data

    def save(self, request=None) -> MasterProfile:
        data = self.cleaned_data
        user_model = get_user_model()
        user = user_model.objects.create_user(
            email=data["email"],
            password=data["password1"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        user.phone = data["phone"]
        user.save(update_fields=["phone"])

        profile = MasterProfile.objects.create(
            user=user,
            profession=data["profession"],
            phone=data["phone"],
            about=data.get("about", ""),
            work_start=data["work_start"],
            work_end=data["work_end"],
        )

        # Send notifications (console backend by default).
        notify_master_registration(profile)
        notify_admin_about_master(profile, request=request)

        return profile

