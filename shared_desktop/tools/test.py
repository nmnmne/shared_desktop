import paramiko

class SSHClient:
    def __init__(self, ip_adress, login, password):
        self.ip_adress = ip_adress
        self.login = login
        self.password = password

    def create_ssh_session(self):
        """
        Создает синхронное SSH-соединение с использованием paramiko.
        """
        try:
            # Создаем SSH клиент
            client = paramiko.SSHClient()
            # Автоматически добавляем ключи хоста
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # Подключаемся к серверу
            client.connect(self.ip_adress, username=self.login, password=self.password)
            return client
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return None

    def run_command(self, command):
        """
        Выполняет команду через SSH и возвращает результат.
        """
        client = self.create_ssh_session()
        if client:
            stdin, stdout, stderr = client.exec_command(command)
            result = stdout.read().decode()
            client.close()
            return result
        else:
            print("Не удалось установить соединение.")
            return None

    def execute_top(self):
        """
        Выполняет команду 'top' и возвращает вывод.
        """
        command = 'top -n 1 -b'
        result = self.run_command(command)
        if result:
            return result
        else:
            return "Ошибка при выполнении команды."

def main():
    ip_adress = '10.45.154.18'
    login = 'root'
    password = 'N1eZ4pC'
    
    ssh_client = SSHClient(ip_adress, login, password)
    top_output = ssh_client.execute_top()
    print(f"Вывод команды top:\n{top_output}")

if __name__ == "__main__":
    main()
