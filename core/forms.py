import os

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme

_ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
_MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB

from .models import Profile


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )
    next = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean_next(self):
        next_url = self.cleaned_data.get('next') or ''
        if not next_url:
            return ''
        allowed_hosts = {self.request.get_host()} if self.request is not None else set()
        require_https = self.request.is_secure() if self.request is not None else False
        if not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts=allowed_hosts,
            require_https=require_https,
        ):
            raise ValidationError('Некорректный адрес для перенаправления.')
        return next_url

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                raise ValidationError('Неверный логин или пароль.')
        return cleaned_data

    def get_user(self):
        return self.user_cache


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )
    first_name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name')
        labels = {
            'username': 'Логин',
            'email': 'Email',
            'first_name': 'Имя',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повтор пароля'

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.get_or_create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    avatar = forms.ImageField(
        label='Аватар',
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        labels = {
            'username': 'Nick',
            'email': 'Email',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'name'):
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in _ALLOWED_AVATAR_EXTENSIONS:
                raise ValidationError('Допустимые форматы: JPG, PNG, GIF, WEBP.')
            if avatar.size > _MAX_AVATAR_SIZE:
                raise ValidationError('Размер файла не должен превышать 2 МБ.')
        return avatar

    def save(self, commit=True):
        user = super().save(commit=False)
        avatar = self.cleaned_data.get('avatar')

        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            if avatar:
                profile.avatar = avatar
                profile.save()
        return user