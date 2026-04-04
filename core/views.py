from django.shortcuts import render


def login_view(request):
    return render(request, 'core/login.html')


def signup_view(request):
    return render(request, 'core/signup.html')


def profile_view(request):
    profile_data = {
        'username': 'megan_fox',
        'email': 'megan.fox@example.com',
        'first_name': 'Megan',
        'last_name': 'Fox',
        'about': 'Технический эксперт и активный участник AskPupkin.',
    }
    return render(request, 'core/profile.html', {'profile': profile_data})
