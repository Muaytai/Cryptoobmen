FROM nginx:1.23

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    apache2-utils \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Аргументы для учетных данных
ARG ADMIN_USER=admin
ARG ADMIN_PASSWORD=admin

# Создание файла с паролем для базовой аутентификации
RUN htpasswd -bc /etc/nginx/.htpasswd ${ADMIN_USER} ${ADMIN_PASSWORD}

# Копируем и делаем скрипт исполняемым
COPY ./docker/nginx/entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Устанавливаем точку входа
ENTRYPOINT ["/docker-entrypoint.sh"]

# Команда по умолчанию
CMD ["nginx", "-g", "daemon off;"]