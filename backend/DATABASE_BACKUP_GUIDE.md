# Руководство по бэкапу и восстановлению базы данных

Это руководство описывает использование скриптов для создания бэкапов и восстановления базы данных PostgreSQL в проекте Cryptoobmen.

## Файлы скриптов

### JSON бэкапы (рекомендуется)
- `backup_json.py` - Скрипт для создания JSON бэкапов через Django ORM
- `restore_json.py` - Скрипт для восстановления из JSON бэкапа
- `backup_json.sh` - Удобный shell-скрипт для JSON бэкапов
- `restore_json.sh` - Удобный shell-скрипт для восстановления JSON

### SQL бэкапы (требует совместимую версию pg_dump)
- `backup_database.py` - Основной скрипт для создания SQL бэкапов
- `restore_database.py` - Скрипт для восстановления из SQL бэкапа
- `backup_rotation.py` - Скрипт для автоматического создания SQL бэкапов с ротацией
- `backup_db.sh` - Удобный shell-скрипт для SQL бэкапов
- `restore_db.sh` - Удобный shell-скрипт для восстановления SQL
- `backup_rotation.sh` - Удобный shell-скрипт для ротации SQL бэкапов

## Создание бэкапа

### JSON бэкапы (рекомендуется)

JSON бэкапы используют Django ORM и не зависят от версий PostgreSQL. Они идеально подходят для небольших и средних баз данных.

#### Базовое использование

```bash
# Создать JSON бэкап с автоматическим именем
./backup_json.sh

# Или напрямую через Python
python3 backup_json.py
```

#### Расширенные опции JSON бэкапов

```bash
# Создать JSON бэкап с кастомным именем
./backup_json.sh --name "production_backup"

# Создать несжатый JSON бэкап
./backup_json.sh --no-compress

# Изменить период хранения старых бэкапов (по умолчанию 7 дней)
./backup_json.sh --keep-days 14

# Установить уровень логирования
./backup_json.sh --log-level DEBUG

# Только очистить старые JSON бэкапы
./backup_json.sh --cleanup-only

# Показать список существующих JSON бэкапов
./backup_json.sh --list
```

### SQL бэкапы (требует совместимую версию pg_dump)

SQL бэкапы используют pg_dump и могут иметь проблемы совместимости версий.

#### Базовое использование

```bash
# Создать SQL бэкап с автоматическим именем
./backup_db.sh

# Или напрямую через Python
python3 backup_database.py
```

### Расширенные опции

```bash
# Создать бэкап с кастомным именем
./backup_db.sh --name "production_backup"

# Создать несжатый бэкап
./backup_db.sh --no-compress

# Изменить период хранения старых бэкапов (по умолчанию 7 дней)
./backup_db.sh --keep-days 14

# Установить уровень логирования
./backup_db.sh --log-level DEBUG

# Только очистить старые бэкапы
./backup_db.sh --cleanup-only
```

### Параметры JSON скриптов

#### backup_json.py

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--name, -n` | Имя JSON бэкапа (без расширения) | Автоматическое |
| `--no-compress` | Не сжимать JSON бэкап | Сжатие включено |
| `--keep-days` | Дни хранения старых JSON бэкапов | 7 |
| `--log-level` | Уровень логирования | INFO |
| `--cleanup-only` | Только очистка старых JSON бэкапов | - |
| `--list` | Показать список существующих JSON бэкапов | - |

#### restore_json.py

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `backup_file` | Путь к файлу JSON бэкапа | Обязательный |
| `--no-backup` | Не создавать резервную копию текущей БД | Создается |
| `--no-clear` | Не очищать базу данных перед восстановлением | Очищается |
| `--no-migrate` | Не запускать миграции Django после восстановления | Запускаются |
| `--log-level` | Уровень логирования | INFO |
| `--force` | Принудительное восстановление без подтверждения | Запрашивается |

### Параметры SQL скриптов

#### backup_database.py

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--name, -n` | Имя SQL бэкапа (без расширения) | Автоматическое |
| `--no-compress` | Не сжимать SQL бэкап | Сжатие включено |
| `--keep-days` | Дни хранения старых SQL бэкапов | 7 |
| `--log-level` | Уровень логирования | INFO |
| `--cleanup-only` | Только очистка старых SQL бэкапов | - |

## Восстановление из бэкапа

### JSON бэкапы

#### Базовое использование

```bash
# Восстановить из JSON бэкапа
./restore_json.sh backups/cryptoobmen_json_backup_20240101_120000.json.gz

# Или напрямую через Python
python3 restore_json.py backups/cryptoobmen_json_backup_20240101_120000.json.gz
```

#### Расширенные опции JSON восстановления

```bash
# Восстановить без создания резервной копии текущей БД
./restore_json.sh backup_file.json.gz --no-backup

# Восстановить без очистки базы данных
./restore_json.sh backup_file.json.gz --no-clear

# Восстановить без применения миграций Django
./restore_json.sh backup_file.json.gz --no-migrate

# Принудительное восстановление без подтверждения
./restore_json.sh backup_file.json.gz --force

# Установить уровень логирования
./restore_json.sh backup_file.json.gz --log-level DEBUG
```

### SQL бэкапы

#### Базовое использование

```bash
# Восстановить из SQL бэкапа
./restore_db.sh backups/cryptoobmen_backup_20240101_120000.sql.gz

# Или напрямую через Python
python3 restore_database.py backups/cryptoobmen_backup_20240101_120000.sql.gz
```

### Расширенные опции

```bash
# Восстановить без создания резервной копии текущей БД
./restore_db.sh backup_file.sql.gz --no-backup

# Восстановить без пересоздания базы данных
./restore_db.sh backup_file.sql.gz --skip-db-creation

# Восстановить без применения миграций Django
./restore_db.sh backup_file.sql.gz --no-migrate

# Принудительное восстановление без подтверждения
./restore_db.sh backup_file.sql.gz --force

# Установить уровень логирования
./restore_db.sh backup_file.sql.gz --log-level DEBUG
```

### Параметры скрипта restore_database.py

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `backup_file` | Путь к файлу бэкапа | Обязательный |
| `--no-backup` | Не создавать резервную копию текущей БД | Создается |
| `--skip-db-creation` | Не пересоздавать базу данных | Пересоздается |
| `--no-migrate` | Не запускать миграции Django | Запускаются |
| `--log-level` | Уровень логирования | INFO |
| `--force` | Принудительное восстановление без подтверждения | Запрашивается |

## Структура файлов

### Директории

- `backups/` - Директория для хранения бэкапов
- `logs/` - Директория для логов

### Формат имен файлов

#### JSON бэкапы
- JSON бэкапы: `cryptoobmen_json_backup_YYYYMMDD_HHMMSS.json.gz`
- Кастомные JSON имена: `{имя}_{timestamp}.json.gz`
- JSON логи: `backup_json_YYYYMMDD.log`, `restore_json_YYYYMMDD.log`

#### SQL бэкапы
- SQL бэкапы: `cryptoobmen_backup_YYYYMMDD_HHMMSS.sql.gz`
- Кастомные SQL имена: `{имя}_{timestamp}.sql.gz`
- SQL логи: `backup_YYYYMMDD.log`, `restore_YYYYMMDD.log`

## Автоматическое создание бэкапов с ротацией

### Использование скрипта ротации

```bash
# Ежедневный бэкап (по умолчанию)
./backup_rotation.sh

# Еженедельный бэкап
./backup_rotation.sh --strategy weekly

# Месячный бэкап
./backup_rotation.sh --strategy monthly

# Годовой бэкап
./backup_rotation.sh --strategy yearly

# Кастомное имя бэкапа
./backup_rotation.sh --name "pre_deployment_backup"

# Показать список существующих бэкапов
./backup_rotation.sh --list

# Только очистить старые бэкапы
./backup_rotation.sh --cleanup-only
```

### Стратегии ротации

| Стратегия | Формат имени | Период хранения | Пример |
|-----------|--------------|-----------------|---------|
| daily | `daily_YYYYMMDD` | 7 дней | `daily_20240101` |
| weekly | `weekly_YYYY_WNN` | 4 недели | `weekly_2024_W01` |
| monthly | `monthly_YYYYMM` | 12 месяцев | `monthly_202401` |
| yearly | `yearly_YYYY` | 3 года | `yearly_2024` |

## Автоматизация

### Cron для регулярных бэкапов

#### Ежедневные JSON бэкапы в 2:00
```bash
# Открыть crontab
crontab -e

# Добавить строку для JSON бэкапов
0 2 * * * cd /path/to/project && ./backup_json.sh
```

#### Ежедневные SQL бэкапы в 2:00
```bash
# Открыть crontab
crontab -e

# Добавить строку для SQL бэкапов
0 2 * * * cd /path/to/project && ./backup_rotation.sh --strategy daily
```

#### Еженедельные бэкапы в воскресенье в 1:00
```bash
0 1 * * 0 cd /path/to/project && ./backup_rotation.sh --strategy weekly
```

#### Месячные бэкапы 1 числа в 3:00
```bash
0 3 1 * * cd /path/to/project && ./backup_rotation.sh --strategy monthly
```

#### Годовые бэкапы 1 января в 4:00
```bash
0 4 1 1 * cd /path/to/project && ./backup_rotation.sh --strategy yearly
```

### Комбинированная стратегия

Для максимальной безопасности рекомендуется использовать комбинированную стратегию:

```bash
# Ежедневные бэкапы (хранятся 7 дней)
0 2 * * * cd /path/to/project && ./backup_rotation.sh --strategy daily

# Еженедельные бэкапы (хранятся 4 недели)
0 1 * * 0 cd /path/to/project && ./backup_rotation.sh --strategy weekly

# Месячные бэкапы (хранятся 12 месяцев)
0 3 1 * * cd /path/to/project && ./backup_rotation.sh --strategy monthly

# Годовые бэкапы (хранятся 3 года)
0 4 1 1 * cd /path/to/project && ./backup_rotation.sh --strategy yearly
```

## Безопасность

### Важные предупреждения

⚠️ **ВНИМАНИЕ**: Восстановление базы данных приведет к **полной потере** всех текущих данных!

⚠️ **Рекомендации**:
- Всегда создавайте резервную копию перед восстановлением
- Тестируйте восстановление на тестовой среде
- Храните бэкапы в безопасном месте
- Регулярно проверяйте целостность бэкапов

### Проверка бэкапа

```bash
# Проверить сжатый бэкап
gunzip -t backup_file.sql.gz

# Просмотреть содержимое бэкапа (первые строки)
gunzip -c backup_file.sql.gz | head -20
```

## Устранение неполадок

### Частые ошибки

1. **Ошибка подключения к БД**
   ```
   Error: connection to server at "localhost" (127.0.0.1), port 5432 failed
   ```
   - Проверьте настройки в `.env` файле
   - Убедитесь, что PostgreSQL запущен

2. **Ошибка прав доступа**
   ```
   Error: permission denied for database
   ```
   - Проверьте права пользователя БД
   - Убедитесь, что пользователь имеет права на создание/удаление БД

3. **Ошибка при восстановлении**
   ```
   Error: database "dbname" already exists
   ```
   - Используйте `--skip-db-creation` если БД уже существует
   - Или позвольте скрипту пересоздать БД

### Логи

Все операции логируются в файлы:
- `logs/backup_YYYYMMDD.log` - логи создания бэкапов
- `logs/restore_YYYYMMDD.log` - логи восстановления

Для отладки используйте уровень `DEBUG`:
```bash
./backup_db.sh --log-level DEBUG
```

## Примеры использования

### Сценарий 1: Ежедневный JSON бэкап

```bash
# Создать JSON бэкап с автоматической очисткой старых файлов
./backup_json.sh --keep-days 7
```

### Сценарий 2: JSON бэкап перед обновлением

```bash
# Создать именованный JSON бэкап перед важным обновлением
./backup_json.sh --name "before_update_$(date +%Y%m%d)"
```

### Сценарий 3: Восстановление из JSON на тестовой среде

```bash
# Восстановить из JSON на тестовой БД без подтверждений
./restore_json.sh production_backup_20240101.json.gz --force --no-backup
```

### Сценарий 4: Экстренное восстановление из JSON

```bash
# Полное восстановление из JSON с резервной копией
./restore_json.sh emergency_backup.json.gz
# Ответить "yes" на все запросы подтверждения
```

### Сценарий 5: Сравнение JSON и SQL бэкапов

```bash
# Создать оба типа бэкапов для сравнения
./backup_json.sh --name "comparison_backup"
./backup_db.sh --name "comparison_backup"  # Если pg_dump совместим
```

## Требования

### Для JSON бэкапов (рекомендуется)
- Python 3.6+
- Django проект с настроенной БД
- Права на чтение/запись БД
- gzip (для сжатия бэкапов)

### Для SQL бэкапов
- Python 3.6+
- PostgreSQL client tools (pg_dump, psql) **совместимых версий**
- Django проект с настроенной БД
- Права на создание/удаление БД
- gzip (для сжатия бэкапов)

## Поддержка

При возникновении проблем:
1. Проверьте логи в директории `logs/`
2. Убедитесь в корректности настроек БД
3. Проверьте права доступа к файлам и БД
4. Используйте уровень логирования `DEBUG` для детальной диагностики
