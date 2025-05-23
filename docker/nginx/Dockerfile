FROM nginx:1.25.5-alpine

# Установка необходимых инструментов для работы с сертификатами
RUN apk add --no-cache openssl certbot certbot-nginx bash

# Удаление дефолтной nginx конфигурации
RUN rm /etc/nginx/conf.d/default.conf

# Копирование конфигураций сайта
COPY conf.d/ /etc/nginx/conf.d/

# Создание необходимых каталогов
RUN mkdir -p /usr/share/nginx/static \
    /usr/share/nginx/media \
    /etc/nginx/ssl \
    /var/www/certbot \
    /etc/letsencrypt

# Установка прав
RUN chown -R nginx:nginx /usr/share/nginx/static \
    /usr/share/nginx/media \
    /var/cache/nginx \
    /var/log/nginx \
    /etc/nginx/conf.d \
    /etc/nginx/ssl \
    /var/www/certbot \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid

# Создание временного самоподписанного сертификата (до получения Let's Encrypt)
RUN mkdir -p /etc/nginx/ssl/live/kripto-obmen.com && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/live/kripto-obmen.com/privkey.pem \
    -out /etc/nginx/ssl/live/kripto-obmen.com/fullchain.pem \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=Cryptoobmen/CN=kripto-obmen.com"

# Создание скрипта для обновления сертификатов
COPY scripts/renew-certs.sh /usr/local/bin/renew-certs.sh
RUN chmod +x /usr/local/bin/renew-certs.sh

USER nginx

# Порты, которые будет слушать Nginx
EXPOSE 80 443

# Запуск Nginx
CMD ["nginx", "-g", "daemon off;"] 