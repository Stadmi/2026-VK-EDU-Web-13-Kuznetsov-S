from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, ProfileForm, SignupForm
from .models import Profile


def login_view(request):
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            redirect_to = form.cleaned_data.get('next') or reverse('questions:index')
            return redirect(redirect_to)
    else:
        form = LoginForm(request, initial={'next': next_url})

    return render(request, 'core/login.html', {'form': form})


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('questions:index')
    else:
        form = SignupForm()

    return render(request, 'core/signup.html', {'form': form})


@login_required(login_url='core:login')
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('core:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'core/profile.html', {'form': form, 'profile': profile})


@login_required(login_url='core:login')
def logout_view(request):
    if request.method != 'POST':
        return redirect(reverse('questions:index'))

    next_url = request.POST.get('next') or reverse('questions:index')
    allowed_hosts = {request.get_host()}
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts=allowed_hosts,
        require_https=request.is_secure(),
    ):
        next_url = reverse('questions:index')

    auth_logout(request)
    return redirect(next_url)