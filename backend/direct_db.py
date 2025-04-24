#!/usr/bin/env python
"""
Запуск прямого SQL-запроса к базе данных
"""
import os
import sys

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.direct_query import main

if __name__ == "__main__":
    main() 