# Используем базовый образ с Python 3.11
FROM python:3.11

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем Gunicorn
RUN pip install gunicorn==20.1.0

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt --no-cache-dir

# Копируем весь проект в рабочую директорию
COPY . .

# Выполняем collectstatic после установки зависимостей и копирования файлов
RUN python manage.py collectstatic --noinput

# Копирование скрипта
COPY tools/restart_web_admin /app/tools/restart_web_admin

# Команда для запуска Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "shared_desktop.wsgi"]
