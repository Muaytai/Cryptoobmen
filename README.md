# Crypto Exchange Platform

Платформа для обмена криптовалют с современным интерфейсом и безопасной авторизацией.

## Структура проекта

- `backend/` - Django REST Framework бэкенд
- `frontend/` - Next.js фронтенд
- `postgres/` - PostgreSQL

## Установка и запуск

Для запуска проекта испльзуется Docker.

##### 1. Клонировать репозиторий

    git clone https://github.com/Muaytai/Cryptoobmen.git

##### 2. Перейти в папку репозитория

    cd Cryptoobmen

##### 3. Создать файл .env с переменными окружения в папке backend

Например:

    SECRET_KEY=secret_key
    DEBUG=debug
    ALLOWED_HOSTS=allowed_hosts
    DB_ENGINE=sql_engine
    DB_NAME=sql_name
    DB_USER=sql_user
    DB_PASSWORD=sql_password
    DB_HOST=sql_host
    DB_PORT=sql_port

##### 4. Создать файл .env с переменными окружения в папке frontend:

    NODE_ENV=development
    PORT=3000

##### 5. Создать файл .env с переменными окружения в папке postgres

Например:

    POSTGRES_DB=sql_name
    POSTGRES_USER=sql_user
    POSTGRES_PASSWORD=sql_password

##### 6. Создать образ

    docker compose build

##### 7. Запустить bash в сервисе backend

    docker compose run backend bash

##### 8. Применить миграции

    python manage.py migrate

##### 9. Создать суперпользователя

    python manage.py createsuperuser

##### 10. Выйти из bash

    exit

##### 11. Запустить сервисы

    docker compose up

## Возможности

- Светлая и темная тема интерфейса
- Авторизация через Google, Yandex, Telegram
- Личный кабинет пользователя
- Удобная система обмена криптовалют
- Просмотр истории транзакций

## Технологии

- Backend: Django, Django REST Framework, JWT
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Авторизация: django-allauth, next-auth
