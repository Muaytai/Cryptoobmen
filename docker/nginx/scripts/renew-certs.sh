#!/bin/bash

# Скрипт для автоматического обновления сертификатов Let's Encrypt

# Домены для сертификатов
DOMAINS="kripto-obmen.com www.kripto-obmen.com"
EMAIL="cryptooveron@gmail.com"

# Проверка наличия сертификата
if [ ! -d "/etc/letsencrypt/live/kripto-obmen.com" ]; then
    echo "Сертификат не найден. Запрашиваем новый сертификат..."
    
    # Запрос нового сертификата
    certbot certonly --webroot -w /var/www/certbot \
        -d kripto-obmen.com -d www.kripto-obmen.com \
        --email $EMAIL --agree-tos --no-eff-email
    
    # Создание символических ссылок для Nginx
    mkdir -p /etc/nginx/ssl/live/kripto-obmen.com
    ln -sf /etc/letsencrypt/live/kripto-obmen.com/fullchain.pem /etc/nginx/ssl/live/kripto-obmen.com/fullchain.pem
    ln -sf /etc/letsencrypt/live/kripto-obmen.com/privkey.pem /etc/nginx/ssl/live/kripto-obmen.com/privkey.pem
else
    echo "Обновление существующего сертификата..."
    certbot renew --quiet
fi

# Перезапуск Nginx для применения новых сертификатов
nginx -s reload

echo "Обновление сертификатов завершено." 