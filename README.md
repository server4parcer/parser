# Парсер YCLIENTS

Система автоматического сбора данных бронирования с платформы YClients и сохранения в базу данных Supabase.

## 1. Технические характеристики

### Архитектура
- База данных: Supabase (PostgreSQL)  
- API сервер: FastAPI
- Парсер: Playwright browser automation
- Деплой: TimeWeb Cloud Apps

### Автоматизация
- Обновление данных каждые 10 минут
- Автоматический деплой при push в GitHub
- Извлечено записей: 53,859+

## 2. API эндпоинты

### Основные
- `GET /status` - статус системы и статистика
- `GET /data` - получить данные бронирования с фильтрами
- `POST /parse` - запустить парсинг для URL
- `POST /parse/all` - запустить парсинг всех URL

### Аутентификация
Все запросы требуют заголовок:
```
X-API-Key: yclients_parser_secure_key_2024
```

### Примеры использования
```bash
# Проверить статус
curl -H "X-API-Key: yclients_parser_secure_key_2024" \
  https://server4parcer-parser-4949.twc1.net/status

# Получить данные
curl -H "X-API-Key: yclients_parser_secure_key_2024" \
  "https://server4parcer-parser-4949.twc1.net/data?limit=10"

# Запустить парсинг
curl -X POST -H "X-API-Key: yclients_parser_secure_key_2024" \
  "https://server4parcer-parser-4949.twc1.net/parse?url=URL_ДЛЯ_ПАРСИНГА"
```

## 3. Переменные окружения

### Обязательные
- `SUPABASE_URL` - адрес базы данных Supabase
- `SUPABASE_KEY` - ключ доступа к Supabase
- `API_KEY` - ключ для доступа к API
- `PARSE_URLS` - URL для парсинга (через запятую)

### Дополнительные
- `API_HOST` - хост API сервера (по умолчанию: 0.0.0.0)
- `API_PORT` - порт API сервера (по умолчанию: 8000)
- `PARSE_INTERVAL` - интервал парсинга в секундах (по умолчанию: 600)

## 4. Управление URL

### Добавление новых URL
1. В панели TimeWeb: добавить URL в переменную `PARSE_URLS`
2. Через API: использовать эндпоинты `/urls`
3. В Supabase Studio: напрямую в таблицу `urls`

### Формат URL
URL должны быть в формате YClients для бронирования:
```
https://b918666.yclients.com/company/855029/personal/menu?o=m-1
```

## 5. Структура данных

### Таблица booking_data
- `id` - уникальный идентификатор
- `date` - дата бронирования
- `time` - время слота
- `price` - цена услуги
- `provider` - поставщик услуги
- `duration` - длительность в минутах
- `created_at` - время создания записи

### Таблица urls
- `id` - уникальный идентификатор
- `url` - адрес для парсинга
- `is_active` - статус активности
- `created_at` - время добавления

## 6. Мониторинг

### Проверка работы
- Логи деплоя: панель TimeWeb
- Данные в реальном времени: Supabase Studio
- API статус: эндпоинт `/status`

### Критерии работоспособности
1. API возвращает статус 200
2. Количество записей в БД растет
3. Новые данные появляются каждые 10 минут
4. Парсер извлекает корректные цены (не время)# Force redeploy
