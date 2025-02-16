import paramiko
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

# Генерация HTML-страницы
def swarco_ssh(request):
    return render(request, "tools/swarco_ssh.html")

@csrf_exempt
def execute_ps(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ip_adress = data.get('ip')

        if ip_adress:
            ssh_client = SSHClient(ip_adress, 'root', 'N1eZ4pC')
            ps_output = ssh_client.execute_ps()

            return JsonResponse({'success': True, 'result': ps_output})

        return JsonResponse({'success': False, 'result': 'IP адрес не указан'})

# Обработчик для сброса процессов
@csrf_exempt
def execute_kill(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ip_adress = data.get('ip')

        if ip_adress:
            ssh_client = SSHClient(ip_adress, 'root', 'N1eZ4pC')
            kill_output = ssh_client.execute_kill()

            return JsonResponse({'success': True, 'result': kill_output})

        return JsonResponse({'success': False, 'result': 'IP адрес не указан'})

@csrf_exempt
def execute_top(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ip_adress = data.get('ip')

        if ip_adress:
            ssh_client = SSHClient(ip_adress, 'root', 'N1eZ4pC')
            top_output = ssh_client.execute_top()

            return JsonResponse({'success': True, 'result': top_output})

        return JsonResponse({'success': False, 'result': 'IP адрес не указан'})

    return JsonResponse({'success': False, 'result': 'Неверный метод запроса'})
class SSHClient:
    def __init__(self, ip_adress, login, password):
        self.ip_adress = ip_adress
        self.login = login
        self.password = password
        self.client = None

    def create_ssh_session(self):
        """Создает и возвращает SSH-соединение."""
        try:
            if not self.client:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(self.ip_adress, username=self.login, password=self.password)
            return self.client
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return None

    def run_command(self, command):
        """Выполняет команду через SSH и возвращает результат."""
        client = self.create_ssh_session()
        if client:
            stdin, stdout, stderr = client.exec_command(command)
            result = stdout.read().decode()
            return result
        else:
            print("Не удалось установить соединение.")
            return None

    def execute_top(self):
        """Выполняет команду 'top' и возвращает вывод."""
        command = 'top -n 1 -b'
        return self.run_command(command) or "Ошибка при выполнении команды."

    def execute_ps(self):
        """Выполняет команду 'ps l | grep -e 502' и возвращает отфильтрованный вывод."""
        command = 'ps l | grep -e 502'
        result = self.run_command(command)
        filtered_result = [line for line in result.splitlines() if '-tcp-client' in line and 'grep' not in line]
        return '\n'.join(filtered_result) if filtered_result else "Процессы не найдены."
    def execute_kill(self):
        """
        Выполняет команду 'kill -9 [PID]' для сброса процессов.
        """
        # Выполнение команды ps для получения процессов
        ps_command = 'ps l | grep -e 502 | grep -e tcp-client'
        print(f"Выполняем команду: {ps_command}")
        
        ps_result = self.run_command(ps_command)
        print(f"Результат команды ps:\n{ps_result}")

        pids = []
        killed_processes = []
        all_processes = []

        # Разбираем вывод команды и готовим список для удаления
        for line in ps_result.splitlines():
            if 'grep' in line:  # Пропускаем строки с 'grep'
                continue

            parts = line.split()
            pid = parts[2]  # Здесь берём второй PID, который находится в индексе 2
            process_info = ' '.join(parts)

            pids.append(pid)
            all_processes.append(process_info)

        print(f"Найденные PID для удаления: {pids}")

        if pids:
            # Находим процесс с максимальным PID
            max_pid = max(pids, key=int)

            # Убираем максимальный PID из списка для удаления
            pids_to_kill = [pid for pid in pids if pid != max_pid]
            
            if pids_to_kill:
                kill_command = f"kill -9 {' '.join(pids_to_kill)}"
                print(f"Команда для удаления: {kill_command}")

                kill_result = self.run_command(kill_command)
                print(f"Результат выполнения команды kill:\n{kill_result}")

                # Проверяем результаты после выполнения команды
                ps_result_after_kill = self.run_command(ps_command)
                print(f"Результат после удаления:\n{ps_result_after_kill}")

                # Собираем убитые процессы
                killed_processes = [line for line in ps_result.splitlines() if line.split()[2] in pids_to_kill]

                # Оставшиеся процессы (кроме тех, которые были убиты)
                remaining_processes = [
                    line for line in ps_result_after_kill.splitlines() if line.split()[2] in pids and line.split()[2] != max_pid
                ]

                result_message = "Убиты следующие процессы:\n{}\nОставшиеся процессы:\n{}".format(
                    '\n'.join(killed_processes),
                    '\n'.join([line.strip() for line in ps_result_after_kill.splitlines()]) if ps_result_after_kill else "Нет оставшихся процессов"
                )


                return result_message
            else:
                return "Процессы для удаления не найдены."
        else:
            return "Процессы не найдены."
