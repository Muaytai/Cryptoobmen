FROM node:22.15.0

WORKDIR /app

# Копирование файлов package.json и package-lock.json
COPY ./frontend/package*.json ./

# Установка зависимостей
RUN npm cache clean --force && npm install

# Мы не копируем весь код, он будет смонтирован как том
# для мгновенного отражения изменений во время разработки

# Открываем порт
EXPOSE 3000

# Запускаем Next.js в режиме разработки
CMD ["npm", "run", "dev"] 