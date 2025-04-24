"""
Скрипт для создания файла .env на основе примера env.example.
Этот файл не должен попадать в репозиторий.
"""

import os
import shutil
import locale

# Устанавливаем локаль для корректной работы с кириллицей на Windows
try:
    if os.name == 'nt':  # Для Windows
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
except Exception as e:
    print(f"Предупреждение: не удалось установить локаль: {e}")

def create_env_file():
    """Создает файл .env из примера env.example"""
    example_path = os.path.join(os.path.dirname(__file__), 'env.example')
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(example_path):
        # Если файл .env уже существует, не перезаписываем его
        if not os.path.exists(env_path):
            shutil.copy2(example_path, env_path)
            print(f"Файл .env создан на основе примера. Путь: {env_path}")
        else:
            print(f"Файл .env уже существует: {env_path}")
    else:
        print(f"Ошибка: файл-пример не найден: {example_path}")
        # Создаем файл .env с минимальными настройками, если примера нет
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("""# Настройки Django
SECRET_KEY=django-insecure-i+$7q*cy+1!jvjty71zpo1ecf$v!x6zqo(m1qf46@veozs97-g
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Настройки базы данных PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=Crypto
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
""")
        print(f"Файл .env создан с базовыми настройками: {env_path}")
    
    print("\nВнимание! Убедитесь, что файл .env добавлен в .gitignore,")
    print("чтобы секретные данные не попали в репозиторий")

if __name__ == "__main__":
    create_env_file() 