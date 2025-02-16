from django.shortcuts import render


def calculate_cycle(request):
    """Таблица направлений!"""
    template = "tools/calculate_cycle.html"
    return render(request, template)
