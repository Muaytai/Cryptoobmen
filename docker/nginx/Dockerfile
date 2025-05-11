FROM nginx:1.25.5-alpine

# Удаление дефолтной nginx конфигурации
RUN rm /etc/nginx/conf.d/default.conf

# Создание каталога для статических файлов
RUN mkdir -p /usr/share/nginx/static
RUN mkdir -p /usr/share/nginx/media

# Nginx будет запускаться от имени nginx пользователя
RUN chown -R nginx:nginx /usr/share/nginx/static && \
    chown -R nginx:nginx /usr/share/nginx/media && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

# Порты, которые будет слушать Nginx
EXPOSE 80 443

# Запуск Nginx
CMD ["nginx", "-g", "daemon off;"] 