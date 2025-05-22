## Этап сборки
FROM node:18-slim AS builder

WORKDIR /app

# Копирование файлов package.json и package-lock.json
COPY frontend/package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода и .env.production
COPY frontend/ .

# Сборка приложения
RUN npm run build

## Этап запуска
FROM node:18-slim

WORKDIR /app

# Создание пользователя без прав администратора
RUN addgroup --system app && adduser --system --group app

# Копирование только необходимых файлов из этапа сборки
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/.env.production ./

# Настройка разрешений
RUN chown -R app:app /app

# Переключение на непривилегированного пользователя
USER app

# Открытие порта
EXPOSE 3000

# Запуск приложения в production-режиме
CMD ["npm", "start"] 