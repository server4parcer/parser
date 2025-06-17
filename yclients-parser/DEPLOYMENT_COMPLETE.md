# YClients Parser - ГОТОВ К ДЕПЛОЮ НА TIMEWEB

## ✅ ЧТО СДЕЛАНО:

### 🔧 Исправлены все проблемы парсера:
- ✅ **Цены с валютой**: Теперь сохраняются как "1500 ₽" вместо "1500"
- ✅ **Правильные провайдеры**: Имена сотрудников вместо чисел  
- ✅ **URL редиректы**: Обработка промежуточных страниц выбора услуг
- ✅ **Улучшенные селекторы**: Адаптивный поиск элементов

### Создан правильный Dockerfile для Timeweb:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y wget curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps
COPY . .
RUN mkdir -p /app/data /app/logs
EXPOSE 8000
CMD ["python", "src/main.py", "--mode", "all"]
```

###  Настроены переменные окружения:
```
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_KEY=yclients_parser_secure_key_2024
SUPABASE_URL=https://axedyenlcdfrjhwfcokj.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
PARSE_URLS=https://n1165596.yclients.com/company/1109937/record-type?o=
PARSE_INTERVAL=600
```

###  Созданы вспомогательные файлы:
- ✅ `check_deployment.py` - проверка готовности к деплою
- ✅ `requirements.txt` - оптимизированные зависимости
- ✅ `.dockerignore` - исключения для Docker
- ✅ Резервные копии оригинальных файлов

##  ИНСТРУКЦИЯ ПО ДЕПЛОЮ В TIMEWEB:

### Шаг 1: Загрузка кода в Git
```bash
# Если нужно настроить Git remote:
git remote add origin https://github.com/server4parcer/parser.git

# Загрузка изменений:
git push origin master
```

### Шаг 2: Настройки в панели Timeweb
**Измените настройки в панели:**
- **Окружение**: `Docker` (НЕ Docker Compose!)
- **Фреймворк**: `Docker`
- **Dockerfile**: `Dockerfile`
- **Команда запуска**: `python src/main.py --mode all`
- **Порт**: `8000`

### Шаг 3: Переменные окружения в Timeweb
**Добавьте в разделе "Переменные окружения":**
```
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_KEY=yclients_parser_secure_key_2024
SUPABASE_URL=https://axedyenlcdfrjhwfcokj.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4ZWR5ZW5sY2RmcmpoZmNva2oiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTcxNzczMjU3NSwiZXhwIjoyMDMzMzA4NTc1fQ.xQrNXHJt5N3DgQzN8rOGP3qOz1c-LL-7dV7ZgAQe3d0
PARSE_URLS=https://n1165596.yclients.com/company/1109937/record-type?o=
PARSE_INTERVAL=600
```

### Шаг 4: Запуск деплоя
1. **Нажмите "Создать приложение"** в Timeweb
2. **Выберите "Из Git-репозитория"**
3. **Укажите**: `https://github.com/server4parcer/parser`
4. **Примените настройки** из Шага 2 и 3
5. **Запустите деплой**

##  ПРОВЕРКА ПОСЛЕ ДЕПЛОЯ:

### ✅ Успешный деплой должен показать:
- **Статус**: "Работает" 
- **Логи**: Сообщения о запуске парсера и API
- **API**: Доступен по `https://ваш-домен.timeweb.cloud/docs`
- **Supabase**: Данные появляются в таблице `booking_data`

###  Если есть проблемы:
1. **Проверьте логи** в панели Timeweb
2. **Убедитесь в правильности переменных** окружения
3. **Проверьте статус приложения**

## ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:

После успешного деплоя:
- ✅ **Парсер работает каждые 10 минут**
- ✅ **Цены сохраняются с валютой**: "1500 ₽"
- ✅ **Провайдеры сохраняются как имена**: "Анна Иванова"  
- ✅ **API доступен** для получения данных
- ✅ **Все данные сохраняются в Supabase**

##  БЫСТРАЯ ПОМОЩЬ:

Если нужна помощь:
1. **Покажите логи** из панели Timeweb
2. **Проверьте переменные** окружения
3. **Убедитесь в настройках** Docker (НЕ Docker Compose)

---

**ВСЁ ГОТОВО! Можно запускать деплой в Timeweb!**
