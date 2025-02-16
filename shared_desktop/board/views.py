from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .models import Rule


def index(request):
    """Главная страница."""
    template = "board/index.html"
    # text = 'Правила'
    rules = Rule.objects.order_by("-pub_date")[:30]
    context = {
        "rules": rules,
    }
    return render(request, template, context)


def full(request):
    """Главная страница с метаданными."""
    template = "board/full.html"
    # text = 'Правила'
    rules = Rule.objects.order_by("-pub_date")[:30]
    context = {
        "rules": rules,
    }
    return render(request, template, context)


def rules_list(request):
    return HttpResponse("Правила")


def rules_detail(request, pk):
    return HttpResponse(f"Правило {pk}")

def handler403(request, exception):
    template = "board/403.html"
    return render(request, template, status=403)

def handler404(request, exception):
    template = "board/404.html"
    return render(request, template, {'path': request.path}, status=404)

def handler500(request):
    template = "board/500.html"
    return render(request, template, status=500)
