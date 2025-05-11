FROM node:22.15.0

# Устанавливаем рабочую директорию
WORKDIR /usr/src/app

# Копирование файлов package.json и package-lock.json
COPY ./frontend/package*.json ./

# Установка зависимостей с улучшенными параметрами для совместимости
RUN npm cache clean --force && npm install --legacy-peer-deps

# Явно устанавливаем режим разработки
ENV NODE_ENV=development
ENV WATCHPACK_POLLING=true

# Открываем порт
EXPOSE 3000

# Запускаем Next.js в режиме разработки
CMD ["npm", "run", "dev"] 