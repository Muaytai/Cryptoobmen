FROM nginx:1.23

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    apache2-utils \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Аргументы для учетных данных
ARG ADMIN_USER=admin
ARG ADMIN_PASSWORD=admin

# Создание файла с паролем для базовой аутентификации
RUN htpasswd -bc /etc/nginx/.htpasswd ${ADMIN_USER} ${ADMIN_PASSWORD}

CMD ["nginx", "-g", "daemon off;"] 