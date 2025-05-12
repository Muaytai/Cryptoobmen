# Локальное окружение Docker

Эта директория содержит конфигурационные файлы для запуска проекта в локальном окружении Docker.

## Файлы

- `backend.Dockerfile` - Dockerfile для бэкенда (Django)
- `frontend.Dockerfile` - Dockerfile для фронтенда (Next.js)
- `docker-compose.local.yml` - Конфигурация docker-compose для локальной разработки
- `start-local.ps1` - PowerShell скрипт для запуска всех контейнеров

## Запуск

Для запуска локальной среды разработки, выполните:

```powershell
.\docker\local\start-local.ps1
```

Скрипт:
1. Проверит, запущены ли базы данных (PostgreSQL и Redis)
2. Запустит контейнер с бэкендом на порту 8000
3. Запустит контейнер с фронтендом на порту 3000

## Проблемы CSS/Tailwind

Если у вас возникают проблемы с CSS/Tailwind в контейнере Docker, рекомендуется запускать фронтенд напрямую на вашей машине:

```bash
cd frontend
npm install
npm run dev
```

При этом бэкенд можно продолжать запускать через Docker. 