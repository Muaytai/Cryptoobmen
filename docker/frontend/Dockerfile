## Этап сборки
FROM node:18-slim AS builder

WORKDIR /app

# Копирование файлов package.json и package-lock.json
COPY frontend/package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода и .env.production
COPY frontend/ .

# Выбираем файл переменных окружения в зависимости от аргумента сборки
ARG BUILD_ENV=production  # допустимые значения: production | development

# Копируем соответствующий env-файл в контейнер
COPY frontend/.env.${BUILD_ENV} .env

# Устанавливаем NODE_ENV для production-сборки
ENV NODE_ENV=${BUILD_ENV}

# Сборка приложения
RUN npm run build

## Этап запуска
FROM node:18-slim

WORKDIR /app

# Создание пользователя без прав администратора
RUN addgroup --system app && adduser --system --group app

# Копирование только необходимых файлов из этапа сборки с правильными правами
COPY --from=builder --chown=app:app /app/next.config.ts ./
COPY --from=builder --chown=app:app /app/public ./public
COPY --from=builder --chown=app:app /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder --chown=app:app /app/package.json ./package.json
COPY --from=builder --chown=app:app /app/.env ./

# Переключение на непривилегированного пользователя
USER app

# Открытие порта
EXPOSE 3000

# Запуск приложения в production-режиме
CMD ["npm", "start"] 