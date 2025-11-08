#!/bin/bash

# Скрипт для автоматического обновления сертификатов Let's Encrypt

# Домены для сертификатов
DOMAINS="tkxn.org www.tkxn.org"
EMAIL="cryptooveron@gmail.com"

# Проверка наличия сертификата
if [ ! -d "/etc/letsencrypt/live/tkxn.org" ]; then
    echo "Сертификат не найден. Запрашиваем новый сертификат..."
    
    # Запрос нового сертификата
    certbot certonly --webroot -w /var/www/certbot \
        -d tkxn.org -d www.tkxn.org \
        --email $EMAIL --agree-tos --no-eff-email
    
    # Создание символических ссылок для Nginx
    mkdir -p /etc/nginx/ssl/live/tkxn.org
    ln -sf /etc/letsencrypt/live/tkxn.org/fullchain.pem /etc/nginx/ssl/live/tkxn.org/fullchain.pem
    ln -sf /etc/letsencrypt/live/tkxn.org/privkey.pem /etc/nginx/ssl/live/tkxn.org/privkey.pem
else
    echo "Обновление существующего сертификата..."
    certbot renew --quiet
fi

# Перезапуск Nginx для применения новых сертификатов
nginx -s reload

echo "Обновление сертификатов завершено." 