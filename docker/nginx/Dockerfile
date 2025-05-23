FROM nginx:1.25.5-alpine

# Установка необходимых инструментов
RUN apk add --no-cache bash openssl

# Удаление дефолтной nginx конфигурации
RUN rm /etc/nginx/conf.d/default.conf

# Копирование конфигураций сайта
COPY conf.d/ /etc/nginx/conf.d/

# Создание необходимых каталогов
RUN mkdir -p /usr/share/nginx/static \
    /usr/share/nginx/media \
    /etc/nginx/ssl/cloudflare

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
EXPOSE 80 443

# Запуск Nginx
CMD ["nginx", "-g", "daemon off;"] 