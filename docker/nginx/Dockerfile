FROM nginx:1.25.5-alpine

# Удаление дефолтной nginx конфигурации
RUN rm /etc/nginx/conf.d/default.conf

# Копирование основного конфигурационного файла
COPY conf.d/nginx.conf /etc/nginx/nginx.conf

# Создание необходимых каталогов одной командой для уменьшения слоев
RUN mkdir -p /usr/share/nginx/static \
    /usr/share/nginx/media

# Установка прав одной командой для уменьшения слоев
RUN chown -R nginx:nginx /usr/share/nginx/static \
    /usr/share/nginx/media \
    /var/cache/nginx \
    /var/log/nginx \
    /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid

USER nginx

# Порты, которые будет слушать Nginx
EXPOSE 80 443

# Запуск Nginx
CMD ["nginx", "-g", "daemon off;"] 