from django.shortcuts import render
from django.http import HttpResponse

def calculate_crc(file_content):
    lines = file_content.splitlines(keepends=True)[1:]  # Пропускаем первую строку

    crc_sum = 0
    for line in lines:
        for char in line:
            crc_sum += ord(char)

    return crc_sum

def crcpeek(request):
    context = {
        'crc_sum': None,
        'file_content': None,
        'initial_crc': None,
        'crc_diff': None,
        'sum_in_file': None,
        'new_sum_in_file': None
    }

    if request.method == "POST":
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            file_content = uploaded_file.read().decode('utf-8-sig')  # Используем utf-8-sig для удаления BOM, если есть

            crc_sum = calculate_crc(file_content)
            sum_in_file = int(file_content.splitlines()[0][:6])
            context['crc_sum'] = crc_sum
            context['file_content'] = file_content
            context['initial_crc'] = crc_sum
            context['sum_in_file'] = sum_in_file
        elif 'file_content' in request.POST:
            file_content = request.POST['file_content']
            initial_crc = int(request.POST['initial_crc'])
            new_crc = calculate_crc(file_content)

            crc_diff = new_crc - initial_crc
            sum_in_file = int(request.POST['sum_in_file'])
            new_sum_in_file = sum_in_file - crc_diff

            # Подставляем новую сумму в начало файла
            new_file_content = f"{new_sum_in_file:06d}" + file_content[6:]

            # Извлекаем первые 3 цифры из второй строки для имени файла
            lines = new_file_content.splitlines()
            if len(lines) > 1:
                prefix = lines[1][:3]
            else:
                prefix = "000"

            filename = f"RAG{prefix}.T"

            context['crc_sum'] = new_crc
            context['file_content'] = new_file_content
            context['initial_crc'] = initial_crc
            context['crc_diff'] = crc_diff
            context['sum_in_file'] = sum_in_file
            context['new_sum_in_file'] = new_sum_in_file

            if request.POST.get('action') == 'save':
                # Формируем файл для скачивания
                response = HttpResponse(content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response.write(new_file_content)
                return response

    return render(request, "tools/crcpeek.html", context)
