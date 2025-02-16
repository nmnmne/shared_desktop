from django.http import Http404
from django.shortcuts import render
from django.conf import settings

class DebugMode404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if settings.DEBUG and response.status_code == 404:
            return self.handle_404_error(request)

        return response

    def handle_404_error(self, request):
        template = "board/404.html"
        return render(request, template, {'path': request.path}, status=404)
