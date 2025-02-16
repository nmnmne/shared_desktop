from django.shortcuts import render


def tools(request):
    """Инструменты."""
    template = "tools/tools.html"
    tools = "tools"
    context = {
        "tools": tools,
    }
    return render(request, template, context)
