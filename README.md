# YClients Parser для TimeWeb Cloud Apps

🎯 **Парсер данных бронирования с сайтов YClients**

## ✅ Исправления для TimeWeb

- **Убрана проблема time/price** - парсер больше не путает время (22:00) с ценой (22₽)
- **Добавлена диагностика** - полное логирование для отладки
- **Оптимизирован Dockerfile** - работает с ограничениями TimeWeb Cloud Apps
- **Поддержка Supabase** - внешняя база данных

## 🚀 Переменные окружения для TimeWeb

```bash
SUPABASE_URL=https://axedyenlcdfrjhwfcokj.supabase.co
SUPABASE_KEY=ваш-ключ-supabase
PARSE_URLS=https://n1165596.yclients.com/company/1109937/record-type?o=
API_HOST=0.0.0.0
API_PORT=8000
PARSE_INTERVAL=600
```

## 📊 Ожидаемый результат

Парсер извлекает:
- ✅ Реальные цены: `1500₽`, `2000 руб` 
- ✅ Имена провайдеров: `Анна Иванова`, `Мария Петрова`
- ✅ Правильное время: `22:00:00`, `07:30:00`

## 🔧 Архитектура

- `src/main.py` - точка входа с диагностикой
- `src/parser/` - исправленные парсеры данных  
- `src/database/` - работа с Supabase
- `src/api/` - REST API для доступа к данным

**Версия**: Fixed для TimeWeb Cloud Apps  
**Статус**: Готов к продакшену
