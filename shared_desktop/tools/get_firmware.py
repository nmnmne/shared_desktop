import asyncio
import json
from django.shortcuts import render
from django.http import JsonResponse
from tools.toolkit.sdp_lib.management_controllers import controller_management
import requests
from bs4 import BeautifulSoup
import urllib3
from pysnmp.hlapi.asyncio import *
from django.views.decorators.csrf import csrf_exempt
from collections import deque
import threading
import os
from dotenv import load_dotenv


load_dotenv()


login = os.getenv('LOGIN_POTOK')
password = os.getenv('PASSWORD_POTOK')
# Очередь для хранения последних 10 пар (ip, protocol)
cache = {}
cache_order = deque(maxlen=10)  # Должен содержать только 10 последних записей

async def get_version_itc_2(ip):
    version = controller_management.AsyncGetItcDataSSH(ip)
    error, res, obj = await version.get_states()
    result = obj.create_json(error, res)
    vers = result.get('responce_entity', {}).get('raw_data', {}).get('current_states', {}).get('itc', {}).get('Firmware')
    return vers or "Не удалось получить прошивку"


def get_potok_firmware(ip):
    # Отключаем предупреждения об SSL-сертификатах
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # URL страницы логина с подставленным IP
    login_url = f"https://{ip}/login"
    # URL страницы, с которой нужно получить данные, также с подставленным IP
    data_url = f"https://{ip}/index"

    # Сессия для поддержания состояния между запросами
    session = requests.Session()

    # Сначала получаем страницу с формой для логина, чтобы извлечь актуальный CSRF токен
    response = session.get(login_url, verify=False)

    if response.status_code == 200:
        # Парсинг страницы для извлечения CSRF токена
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

        # Задание данных для формы авторизации с извлеченным CSRF токеном
        login_data = {
            "csrf_token": csrf_token,  # Используем актуальный токен
            "login": login, 
            "password": password  
        }

        # Отправка POST-запроса для авторизации (с отключенной проверкой SSL)
        response = session.post(login_url, data=login_data, verify=False)

        # Проверка успешности авторизации
        if response.status_code == 200 and "csrf_token" not in response.text:
            # Переход на страницу, с которой нужно извлечь данные (с отключенной проверкой SSL)
            response = session.get(data_url, verify=False)
            
            if response.status_code == 200:
                # Парсинг страницы с помощью BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Поиск нужного элемента по id и вывод его текста
                version_element = soup.find("span", {"id": "tl_version"})
                
                if version_element:
                    version_text = version_element.text
                    return f'Поток: {version_text}'
                else:
                    return "Элемент с id 'tl_version' не найден на странице."
            else:
                return "Не удалось загрузить страницу после авторизации."
        else:
            return "Ошибка авторизации. Возможно, неверный логин/пароль или CSRF токен."
    else:
        return "Не удалось получить страницу логина."


async def get_version_itc_3(ip):
    community_string = "private"
    version_oid = ObjectIdentity(
        ".1.3.6.1.4.1.1206.4.2.6.1.3.1.5.1"
    )
    error_indication, error_status, error_index, var_binds = await getCmd(
        SnmpEngine(),
        CommunityData(community_string),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(version_oid),
    )

    if error_indication:
        return 0
    else:
        try:
            version_value = var_binds[0][1].prettyPrint()
            return version_value
        except (IndexError, ValueError) as e:
            print(f"Ошибка: {e}")
            return None

# Функция для проверки OID, определяющего тип устройства
async def check_device_type(ip):
    community_string = "private"
    check_oid = ObjectIdentity(".1.3.6.1.4.1.1206.4.2.6.1.3.1.4.1")

    error_indication, error_status, error_index, var_binds = await getCmd(
        SnmpEngine(),
        CommunityData(community_string),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(check_oid),
    )

    if error_indication:
        return None
    else:
        try:
            var_value = var_binds[0][1].prettyPrint()
            return var_value
        except (IndexError, ValueError) as e:
            print(f"Ошибка: {e}")
            return None


async def get_version_swarco(ip):
    # Проверяем, является ли устройство ITC-3
    device_type = await check_device_type(ip)

    if device_type == "ITC-3":
        version = await get_version_itc_3(ip)
        return version
    else:
        version = await get_version_itc_2(ip)
        return version

# Функция для асинхронного кэширования
async def fetch_version(ip, protocol, cache_key):
    version = None
    errorMessage = None
    
    if protocol == "Swarco":
        version = await get_version_swarco(ip)
    elif protocol in ["Поток", "Поток (P)", "Поток (S)"]:
        version = get_potok_firmware(ip)
    if version:
        cache[cache_key] = version
    else:
        cache[cache_key] = errorMessage

# Асинхронная обертка для вызова асинхронной функции в потоке
def async_task(ip, protocol, cache_key):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fetch_version(ip, protocol, cache_key))

@csrf_exempt
def get_firmware_api(request):
    print(f"Request body: {request.body.decode('utf-8')}")

    version = None
    errorMessage = None

    if request.method == "POST":
        try:
            # Преобразуем тело запроса в Python-словарь
            data = json.loads(request.body)
            ip = data.get("ip")
            protocol = data.get("protocol")

            # Принт для отладки
            print(f"Received IP: {ip}, Protocol: {protocol}")

            cache_key = f"{ip}_{protocol}"

            # Если данные есть в кэше, проверяем их состояние
            if cache_key in cache:
                cached_response = cache[cache_key]
                if cached_response == "loading":
                    return JsonResponse({'version': "loading"})  # Если еще не готово, возвращаем "loading"
                else:
                    return JsonResponse({'version': cached_response})  # Возвращаем закешированный ответ

            # Если данных нет в кэше, установим "loading"
            cache[cache_key] = "loading"
            cache_order.append(cache_key)

            # Запуск асинхронного кэширования в отдельном потоке
            threading.Thread(target=async_task, args=(ip, protocol, cache_key)).start()

            return JsonResponse({'version': "loading"})  # Сразу возвращаем "loading"

        except json.JSONDecodeError:
            errorMessage = "Invalid JSON data"

    if version:
        return JsonResponse({'version': version})
    else:
        return JsonResponse({'errorMessage': errorMessage})

def get_firmware(request):
    version = None

    if request.method == "POST":
        ip = request.POST.get("ip")
        protocol = request.POST.get("protocol")

        if protocol == "Тип ДК":
            version = "Пожалуйста выберете тип ДК"
        elif protocol == "Swarco":
            version = asyncio.run(get_version_swarco(ip))
        elif protocol == "Поток" or "Поток (P)" or "Поток (S)":
            version = get_potok_firmware(ip)
    
    return render(request, "tools/get_firmware.html", {'version': version})