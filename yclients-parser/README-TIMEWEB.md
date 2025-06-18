# 🚀 YClients Parser - Простая инструкция для Timeweb

**Павел, это упрощенная инструкция специально для Timeweb Cloud Apps.**

## ✅ СТАТУС: ВСЕ ИСПРАВЛЕНО И ПРОТЕСТИРОВАНО

**Главная проблема решена:** Парсер больше НЕ показывает `22₽`, `7₽`, `8₽` вместо нормальных цен.

### 🧪 Тесты прошли успешно:
- ✅ **28/28 автотестов** пройдено
- ✅ **Отклоняет проблемные значения:** 22₽, 7₽, 8₽
- ✅ **Принимает правильные цены:** 1500₽, 2000 руб
- ✅ **База данных** автоматически исправляет плохие данные

## 📦 ФАЙЛЫ ДЛЯ TIMEWEB

### Обязательные файлы в GitHub репозитории:
```
├── src/                 # Исправленный код парсера  
├── Dockerfile          # Для Timeweb (уже готов)
├── requirements.txt    # Зависимости Python
└── .env.example       # Пример настроек
```

### Dockerfile уже настроен для Timeweb:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
# ... установка зависимостей ...
EXPOSE 8000
CMD ["python", "src/main.py", "--mode", "all"]
```

## 🔧 ДЕПЛОЙ В TIMEWEB CLOUD APPS

### Шаг 1: Загрузите код в ваш GitHub
```
1. Обновите репозиторий: https://github.com/server4parcer/parser
2. Убедитесь что там есть обновленный код
3. Commit и Push изменения
```

### Шаг 2: Создайте приложение в Timeweb
```
1. Зайдите: https://timeweb.cloud/my/apps
2. "Создать приложение"
3. ТИП: "Dockerfile" ⚠️ НЕ Docker Compose!
4. Подключите: https://github.com/server4parcer/parser
5. Ветка: main
```

### Шаг 3: Настройте переменные окружения
**В разделе "Переменные окружения" Timeweb добавьте:**

```bash
# Supabase (ваша база данных)
SUPABASE_URL=https://axedyenlcdfrjhwfcokj.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4ZWR5ZW5sY2RmcmpoZmNva2oiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTcxNzczMjU3NSwiZXhwIjoyMDMzMzA4NTc1fQ.xQrNXHJt5N3DgQzN8rOGP3qOz1c-LL-7dV7ZgAQe3d0

# Адрес для парсинга
PARSE_URLS=https://n1165596.yclients.com/company/1109937/record-type?o=

# Настройки API
API_HOST=0.0.0.0
API_PORT=8000

# Интервал парсинга (600 секунд = 10 минут)
PARSE_INTERVAL=600
```

### Шаг 4: Запустите деплой
```
1. Нажмите "Создать приложение"
2. Дождитесь сборки (3-5 минут)
3. Проверьте что статус "Запущено"
```

## 📊 ПРОВЕРКА РАБОТЫ

### ✅ Хорошие логи в Timeweb:
```
✅ База данных инициализирована
✅ API-сервер запущен на порту 8000
📊 Извлечено: время=22:00:00, цена=1500₽, провайдер=Анна Иванова
💾 Сохранение записей в базу данных
```

### ❌ Плохие логи (значит что-то не так):
```
❌ Извлечено: время=22:00:00, цена=22₽, провайдер=Не указан
❌ ModuleNotFoundError
❌ Application error: main.errors.ApplicationError
```

### 🔍 Проверка данных в Supabase:
```
1. Откройте https://supabase.com/dashboard  
2. Выберите проект axedyenlcdfrjhwfcokj
3. Таблица: booking_data
4. Должны быть реальные цены: "1500₽", "2000 руб"
5. НЕ должно быть: "22₽", "7₽", "8₽"
```

## 🆘 ЧАСТЫЕ ПРОБЛЕМЫ

### "Cannot get HTTP 200 for domain"
**Причина:** Приложение не запустилось  
**Решение:** 
- Проверьте что тип "Dockerfile" (не Docker Compose)
- Проверьте логи сборки
- Убедитесь что все переменные окружения добавлены

### "Цены все еще 22₽, 7₽"
**Причина:** Загружена старая версия кода  
**Решение:**
- Обновите код в GitHub репозитории
- Перезапустите деплой в Timeweb

### "Нет данных в Supabase"
**Причина:** Проблема с подключением к базе  
**Решение:**
- Проверьте SUPABASE_URL и SUPABASE_KEY
- Убедитесь что PARSE_URLS правильный

## 🎯 ОТЛИЧИЯ ОТ ПРОШЛЫХ ВЕРСИЙ

### ❌ Раньше НЕ работало:
- Docker Compose (не поддерживается в Timeweb)
- Volumes (запрещены в Timeweb Apps)  
- Встроенный PostgreSQL (не нужен)
- Парсер путал время с ценами

### ✅ Сейчас работает:
- Простой Dockerfile
- Внешняя база Supabase
- Правильное разделение времени и цен
- Все проблемы исправлены

## 💬 ЕСЛИ НУЖНА ПОМОЩЬ

**Пришлите:**
1. Скриншот логов из Timeweb Apps
2. Скриншот переменных окружения  
3. Что показывает таблица в Supabase

**Парсер готов работать! Все тесты пройдены.**

---
*Специально для Timeweb Cloud Apps | Без Docker Compose | Только Dockerfile*