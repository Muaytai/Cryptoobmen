# Быстрый старт - Бэкап и восстановление БД

## Создание бэкапа

### JSON бэкапы (рекомендуется)
```bash
# Простой JSON бэкап
./backup_json.sh

# JSON бэкап с кастомным именем
./backup_json.sh --name "before_update"

# JSON бэкап без сжатия
./backup_json.sh --no-compress
```

### SQL бэкапы (если pg_dump совместим)
```bash
# Простой SQL бэкап
./backup_db.sh

# Ежедневный бэкап с ротацией
./backup_rotation.sh

# SQL бэкап с кастомным именем
./backup_db.sh --name "before_update"
```

## Восстановление из бэкапа

### JSON бэкапы
```bash
# Восстановить из JSON бэкапа (с подтверждением)
./restore_json.sh backups/cryptoobmen_json_backup_20240101_120000.json.gz

# Принудительное восстановление из JSON
./restore_json.sh backups/test_backup_20240101.json.gz --force
```

### SQL бэкапы
```bash
# Восстановить из SQL бэкапа (с подтверждением)
./restore_db.sh backups/cryptoobmen_backup_20240101_120000.sql.gz

# Принудительное восстановление из SQL
./restore_db.sh backups/daily_20240101.sql.gz --force
```

## Автоматизация (cron)

```bash
# Открыть crontab
crontab -e

# Добавить ежедневный бэкап в 2:00
0 2 * * * cd /path/to/project && ./backup_rotation.sh --strategy daily
```

## Полезные команды

```bash
# Показать список JSON бэкапов
./backup_json.sh --list

# Показать список SQL бэкапов
./backup_rotation.sh --list

# Только очистить старые JSON бэкапы
./backup_json.sh --cleanup-only

# Только очистить старые SQL бэкапы
./backup_db.sh --cleanup-only

# Проверить сжатый JSON бэкап
gunzip -t backups/cryptoobmen_json_backup_20240101.json.gz

# Проверить сжатый SQL бэкап
gunzip -t backups/daily_20240101.sql.gz
```

## ⚠️ Важно

- Восстановление **полностью удаляет** текущие данные
- Всегда создается резервная копия перед восстановлением
- Тестируйте на тестовой среде

Подробная документация: `DATABASE_BACKUP_GUIDE.md`
