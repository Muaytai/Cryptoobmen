# Crypto Exchange Platform

Платформа для обмена криптовалют с современным интерфейсом и безопасной авторизацией.

## Структура проекта

- `backend/` - Django REST Framework бэкенд
- `frontend/` - Next.js фронтенд

## Установка и запуск

### Backend (Django)

```bash
# Переход в директорию бэкенда
cd backend

# Активация виртуального окружения
python -m venv venv
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Создание и применение миграций
python manage.py makemigrations
python manage.py migrate

# Запуск сервера разработки
python manage.py runserver
```

### Frontend (Next.js)

```bash
# Переход в директорию фронтенда
cd frontend

# Установка зависимостей
npm install

# Запуск сервера разработки
npm run dev
```

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