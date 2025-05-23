## Этап сборки
FROM node:18-slim AS builder

WORKDIR /app

# Копирование файлов package.json и package-lock.json
COPY frontend/package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода и .env.production
COPY frontend/ .

# Убедимся, что переменные окружения правильно настроены
RUN echo "NEXT_PUBLIC_API_URL=https://tkxn.org/api" > .env.production \
    && echo "NEXT_PUBLIC_BACKEND_URL=https://tkxn.org" >> .env.production \
    && echo "NODE_ENV=production" >> .env.production \
    && echo "NEXT_PUBLIC_AUTH_COOKIE_NAME=auth-token" >> .env.production \
    && echo "NEXT_PUBLIC_AUTH_COOKIE_MAX_AGE=2592000" >> .env.production \
    && echo "NEXT_PUBLIC_REDIRECT_URI=https://tkxn.org/api/auth/callback" >> .env.production \
    && echo "NEXT_PUBLIC_SECURE_COOKIE=true" >> .env.production \
    && echo "NEXT_PUBLIC_SAME_SITE=strict" >> .env.production \
    && echo "NEXT_PUBLIC_DEBUG=false" >> .env.production \
    && echo "NEXT_PUBLIC_ENABLE_LOGS=false" >> .env.production \
    && echo "NEXT_PUBLIC_WS_URL=wss://tkxn.org/ws/" >> .env.production \
    && echo "NEXT_PUBLIC_ENABLE_CACHE=true" >> .env.production \
    && echo "NEXT_PUBLIC_CDN_URL=https://tkxn.org/static" >> .env.production

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
COPY --from=builder --chown=app:app /app/.env.production ./

# Переключение на непривилегированного пользователя
USER app

# Открытие порта
EXPOSE 3000

# Запуск приложения в production-режиме
CMD ["npm", "start"] 