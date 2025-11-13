from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    """
    Simple home / dashboard page.
    The template created by the other AI should be 'home.html' extending base.html.
    """
    return render(request, "home.html")
