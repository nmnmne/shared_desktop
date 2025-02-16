import os
import subprocess
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json

# API для перезапуска
@csrf_exempt
def restart_web_admin_api(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            ip_address = body.get("ip_address")

            if ip_address:
                base_path = os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
                cmd = os.path.join(
                    base_path,
                    "tools",
                    "restart_web_admin",
                    "restart_web_admin.exe",
                ) + f" -i {ip_address}"
                
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return JsonResponse({"status": "success", "message": "Web admin restarted successfully."})
                else:
                    return JsonResponse({"status": "error", "message": result.stderr}, status=500)
            else:
                return JsonResponse({"status": "error", "message": "Missing IP address."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format."}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Only POST requests are allowed."}, status=405)

# Генерация HTML-страницы
def restart_web_admin(request):
    return render(request, "tools/restart_web_admin.html")