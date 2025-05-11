FROM python:3.13.3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установка зависимостей
RUN apt-get update \
    && apt-get install postgresql gcc python3-dev musl-dev -y \
    && apt-get install gettext -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /usr/src/app

# Копирование и установка зависимостей
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Мы не копируем весь код, он будет смонтирован как том
# для мгновенного отражения изменений во время разработки

# Открываем порт
EXPOSE 8000

# Запускаем Django в режиме разработки
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 