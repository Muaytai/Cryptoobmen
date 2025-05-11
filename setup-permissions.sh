#!/bin/bash
# Скрипт для настройки прав доступа на Linux-сервере

# Установка прав на выполнение для bash-скриптов
chmod +x start-prod.sh
chmod +x stop-prod.sh

echo "Права на выполнение для скриптов установлены."

# Проверка наличия Docker и Docker Compose
if ! [ -x "$(command -v docker)" ]; then
  echo "Ошибка: Docker не установлен." >&2
  echo "Пожалуйста, установите Docker: https://docs.docker.com/engine/install/" >&2
  exit 1
fi

if ! [ -x "$(command -v docker-compose)" ] && ! [ -x "$(command -v docker)" ]; then
  echo "Предупреждение: Docker Compose не найден как отдельная команда." >&2
  
  # Проверка Docker Compose plugin в Docker CLI
  if docker compose version > /dev/null 2>&1; then
    echo "Docker Compose V2 найден как плагин Docker CLI." >&2
    echo "В скриптах используйте 'docker compose' вместо 'docker-compose'." >&2
    
    # Создание символической ссылки для совместимости
    echo "Создание символической ссылки для совместимости со скриптами..."
    if [ -d /usr/local/bin ]; then
      sudo ln -sf $(which docker) /usr/local/bin/docker-compose
      echo "Символическая ссылка создана. Используйте './start-prod.sh' для запуска."
    else
      echo "Не удалось создать символическую ссылку. Пожалуйста, отредактируйте скрипты вручную."
      echo "Замените 'docker-compose' на 'docker compose' в start-prod.sh и stop-prod.sh."
    fi
  else
    echo "Docker Compose не найден." >&2
    echo "Пожалуйста, установите Docker Compose: https://docs.docker.com/compose/install/" >&2
    exit 1
  fi
fi

echo "Система готова к запуску продакшен-окружения."
echo "Выполните './start-prod.sh' для запуска." 