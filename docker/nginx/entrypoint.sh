#!/bin/sh

# Меняем владельца для статических и медиа файлов
echo "Changing ownership of static and media files..."
chown -R nginx:nginx /usr/share/nginx/static
chown -R nginx:nginx /usr/share/nginx/media
echo "Ownership change finished."

# Запускаем оригинальную команду nginx
exec "$@"