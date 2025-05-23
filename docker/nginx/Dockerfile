FROM nginx:1.25-alpine

# Установка необходимых пакетов
RUN apk add --no-cache openssl apache2-utils

# Создание директории для SSL сертификатов
RUN mkdir -p /etc/nginx/ssl/cloudflare

# Создание файла с паролем для базовой аутентификации
RUN htpasswd -bc /etc/nginx/.htpasswd admin CryptoAdmin2025

# Копирование конфигурационных файлов
COPY ./conf.d/ /etc/nginx/conf.d/

# Копирование скриптов
COPY ./scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# Создание директорий для статических файлов
RUN mkdir -p /usr/share/nginx/static /usr/share/nginx/media

# Установка прав
RUN chown -R nginx:nginx /usr/share/nginx/static \
    /usr/share/nginx/media \
    /var/cache/nginx \
    /var/log/nginx \
    /etc/nginx/conf.d \
    /etc/nginx/ssl \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid

USER nginx

# Порты, которые будет слушать Nginx
EXPOSE 80 443 8080

# Запуск Nginx
CMD ["nginx", "-g", "daemon off;"] 