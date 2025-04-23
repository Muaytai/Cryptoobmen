#!/bin/bash

echo "===== Установка Crypto Exchange Platform ====="

echo ""
echo "===== Настройка backend ====="
cd backend

echo "Создаем виртуальное окружение Python..."
python -m venv venv

echo "Активируем виртуальное окружение..."
source venv/bin/activate

echo "Устанавливаем зависимости для backend..."
pip install -r requirements.txt

echo ""
cd ..

echo "===== Настройка frontend ====="
cd frontend

echo "Устанавливаем зависимости для frontend..."
npm install

echo ""
cd ..

echo "===== Установка завершена ====="
echo ""
echo "Для запуска backend:"
echo "cd backend && source venv/bin/activate && python manage.py runserver"
echo ""
echo "Для запуска frontend:"
echo "cd frontend && npm run dev"
echo ""
echo "Удачной разработки!" 