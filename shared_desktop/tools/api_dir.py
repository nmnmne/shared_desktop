import os
import requests
import time

from django.http import JsonResponse
from django.shortcuts import render

from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Конфигурация
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

# Глобальные переменные для хранения токена и времени его получения
TOKEN_CACHE = {
    "token": None,
    "timestamp": None
}

# Функция для получения токена
def get_token(api_key):
    global TOKEN_CACHE
    current_time = time.time()

    # Проверяем, есть ли токен и не истекло ли 24 часа
    if TOKEN_CACHE["token"] and TOKEN_CACHE["timestamp"]:
        elapsed_time = current_time - TOKEN_CACHE["timestamp"]
        if elapsed_time < 24 * 60 * 60:  # 24 часа в секундах
            print(f"Используем кешированный токен")
            return TOKEN_CACHE["token"]

    # Получаем новый токен
    url = f"{API_URL}/auth/refresh?APIKey={api_key}"
    headers = {"accept": "application/json"}
    response = requests.post(url, headers=headers)
    if response.status_code == 200 and response.json().get("Success"):
        TOKEN_CACHE["token"] = response.json()["Auth"]["Token"]
        TOKEN_CACHE["timestamp"] = current_time
        print(f"Получен новый токен")
        return TOKEN_CACHE["token"]
    else:
        print(f"Ошибка получения токена: {response.status_code} - {response.text}")
        TOKEN_CACHE["token"] = None
        TOKEN_CACHE["timestamp"] = None
        return None


# Функция для получения информации о контроллере
def get_controller_info(controller_id, token):
    url = f"{API_URL}/controllers/ext:{controller_id}"
    headers = {"accept": "application/json", "x-rmsapi-token": token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "Success": False,
            "Message": "Не удалось получить информацию о контроллере.",
        }

# Функция для получения статуса контроллера
def get_controller_status(controller_id, token):
    url = f"{API_URL}/controllers/ext:{controller_id}/status"
    headers = {"accept": "application/json", "x-rmsapi-token": token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "Success": False,
            "Message": "Не удалось получить статус контроллера.",
        }

# Основная функция для обработки запросов
def api_dir(request):
    if request.method == "POST":
        controller_id = request.POST.get("controllerId")
        token = get_token(API_KEY)
        if token:
            controller_info = get_controller_info(controller_id, token)
            controller_status = get_controller_status(controller_id, token)

            response = {"Success": True}

            if controller_info.get("Success"):
                response["Controller"] = controller_info.get("Controller")
            else:
                response["ControllerError"] = controller_info.get("Message")

            if controller_status.get("Success"):
                response["ControllerStatus"] = controller_status.get(
                    "ControllerStatus"
                )
            else:
                response["ControllerStatusError"] = controller_status.get(
                    "Message"
                )

            if (
                "Controller" not in response
                and "ControllerStatus" not in response
            ):
                response["Success"] = False
                response["Message"] = (
                    "Не удалось получить информацию о контроллере или его статус."
                )

            return JsonResponse(response)
        else:
            return JsonResponse(
                {
                    "Success": False,
                    "Message": "Не удалось получить токен авторизации.",
                }
            )
    return render(request, "tools/api_dir.html")
