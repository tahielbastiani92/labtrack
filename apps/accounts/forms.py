from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from config.forms import BootstrapFormMixin

from .models import User

PASSWORD_HELP_TEXT = " ".join(password_validation.password_validators_help_texts())


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class AdminUserCreateForm(BootstrapFormMixin, forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text=PASSWORD_HELP_TEXT,
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "is_active")

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                self.add_error("password2", "The two password fields did not match.")
            else:
                candidate = User(
                    username=cleaned_data.get("username", ""),
                    email=cleaned_data.get("email", ""),
                    first_name=cleaned_data.get("first_name", ""),
                    last_name=cleaned_data.get("last_name", ""),
                )
                try:
                    password_validation.validate_password(password2, user=candidate)
                except ValidationError as exc:
                    self.add_error("password2", exc)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AdminUserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    new_password1 = forms.CharField(
        label="New password",
        required=False,
        widget=forms.PasswordInput,
        help_text="Leave blank to keep the current password. " + PASSWORD_HELP_TEXT,
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        required=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "is_active")

    def __init__(self, *args, acting_user=None, **kwargs) -> None:
        self.acting_user = acting_user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")
        if password1 or password2:
            if password1 != password2:
                self.add_error("new_password2", "The two password fields did not match.")
            else:
                candidate = User(
                    username=cleaned_data.get("username") or self.instance.username,
                    email=cleaned_data.get("email") or self.instance.email,
                    first_name=cleaned_data.get("first_name", ""),
                    last_name=cleaned_data.get("last_name", ""),
                )
                try:
                    password_validation.validate_password(password1, user=candidate)
                except ValidationError as exc:
                    self.add_error("new_password1", exc)

        if self.acting_user is not None and self.instance.pk == self.acting_user.pk:
            if not cleaned_data.get("is_active"):
                self.add_error("is_active", "You cannot deactivate your own account.")
            role = cleaned_data.get("role")
            if role and role != User.Role.ADMINISTRATOR:
                self.add_error("role", "You cannot remove your own administrator role.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("new_password1")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
