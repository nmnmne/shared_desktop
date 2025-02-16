import json

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def make_condition(det_ranges_and_group: str):
    """Функция формирует строку продления/запроса ДК Поток стандартного вида."""
    all_det_ranges = []
    num_group = None

    # Удаляем пробелы и разбиваем строку по запятой
    det_collection = det_ranges_and_group.replace(" ", "").split(",")

    for data in det_collection:
        if data.isdigit():
            num_group = data
            continue
        
        # Определяем разделитель диапазона (дефис или плюс)
        if '-' in data:
            separator = '-'
        elif '+' in data:
            separator = '+'
        else:
            return None, "Некорректный формат диапазона номеров детекторов"

        # Разделяем диапазон на начало и конец
        try:
            det_from, det_to = data.split(separator)
        except ValueError:
            return None, "Некорректный формат диапазона номеров детекторов"

        condition_string = ""

        if not det_from.isdigit() or not det_to.isdigit():
            return None, "Некорректные данные"

        det_from, det_to = int(det_from), int(det_to)
        for num_det in range(det_from, det_to + 1):
            if num_det != det_to:
                if separator == '-':
                    condition_string += f"ddr(D{num_det}) or "
                else:
                    condition_string += f"ddr(D{num_det}) and "
            else:
                if separator == '-':
                    condition_string += f"ddr(D{num_det})"
                else:
                    condition_string += f"ddr(D{num_det})"
        all_det_ranges.append(condition_string)

    condition_string = " or ".join(all_det_ranges)

    if num_group is not None:
        if num_group.isdigit():
            condition_string = f"({condition_string}) and mr(G{num_group})"
        else:
            return None, "Некорректные данные"

    return condition_string, None

def dt_potok(request):
    condition_string = None
    error_message = None
    if request.method == "POST":
        det_ranges_and_group = request.POST.get("det_ranges_and_group")
        condition_string, error_message = make_condition(det_ranges_and_group)

    return render(
        request,
        "tools/dt_potok.html",
        {"condition_string": condition_string, "error_message": error_message},
    )

@csrf_exempt
def dt_potok_api(request):
    if request.method == "POST":
        try:
            # Предполагаем, что данные передаются в формате JSON
            data = json.loads(request.body)
            det_ranges_and_group = data.get("det_ranges_and_group")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат данных."}, status=400)
        
        # Проверка, если det_ranges_and_group не передано
        if det_ranges_and_group is None or det_ranges_and_group.strip() == "":
            return JsonResponse({"error": "Поле 'det_ranges_and_group' не может быть пустым."}, status=400)
        
        # Вызываем make_condition, если входные данные корректны
        condition_string, error_message = make_condition(det_ranges_and_group)
        
        # Если есть ошибка в make_condition, возвращаем её в формате JSON
        if error_message:
            return JsonResponse({"error": error_message}, status=400)
        
        # Возвращаем результат в формате JSON
        return JsonResponse({"condition_string": condition_string})

    return JsonResponse({"error": "Invalid request method."}, status=405)
