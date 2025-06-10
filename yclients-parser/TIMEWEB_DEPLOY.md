# 🚀 Деплой на Timeweb - Готово!

## 📋 Checklist перед деплоем:
- ✅ Исправления применены
- ✅ Dockerfile-timeweb создан
- ✅ Переменные окружения подготовлены
- ✅ Импорты проверены

## 🔗 Шаги деплоя в Timeweb:

### 1. Создайте приложение
- Войдите в панель Timeweb
- Приложения → Создать приложение
- Выберите "Из Git-репозитория"
- Укажите ваш репозиторий

### 2. Настройте Docker
- Dockerfile: `Dockerfile-timeweb`
- Команда запуска: `python src/main.py --mode all`
- Порт: `8000`

### 3. Добавьте переменные окружения
Скопируйте из файла `timeweb-env.txt`:
```
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_KEY=yclients_parser_secure_key_2024
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_KEY=ваш-anon-ключ
PARSE_URLS=https://n1165596.yclients.com/company/1109937/record-type?o=
PARSE_INTERVAL=600
```

### 4. Проверьте работу
- Логи: должны появиться сообщения о запуске
- API: https://ваш-домен.timeweb.cloud/docs
- Supabase: проверьте таблицу booking_data

## 🎯 Ожидаемый результат:
- Парсер работает каждые 10 минут
- Цены сохраняются с валютой (например: "1500 ₽")
- Провайдеры сохраняются как имена (например: "Анна Иванова")
