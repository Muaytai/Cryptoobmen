FROM python:3.13.3

# Устанавливаем необходимые зависимости
RUN apt-get update \
    && apt-get install postgresql gcc python3-dev musl-dev -y

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем рабочую директорию
WORKDIR /usr/src/app

# Копируем файл с зависимостями
COPY ./backend/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт
EXPOSE 8000

# Команда для запуска приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 