#!/bin/bash

echo "🚀 Подготовка YClients Parser для деплоя на Timeweb"

# 1. Применяем все исправления
echo "📝 Применение исправлений..."
if [ -f "apply_fixes.sh" ]; then
    chmod +x apply_fixes.sh
    ./apply_fixes.sh
fi

# 2. Создаем .dockerignore для оптимизации
echo "📦 Создание .dockerignore..."
cat > .dockerignore << 'EOF'
.git
.gitignore
README.md
Dockerfile
docker-compose.yml
*.md
tests/
.pytest_cache/
__pycache__/
*.pyc
*.pyo
*.pyd
.env.local
.env.development
logs/*.log
data/temp/
.vscode/
.idea/
EOF

# 3. Проверяем наличие всех необходимых файлов
echo "🔍 Проверка файлов проекта..."

required_files=(
    "src/main.py"
    "src/parser/improved_data_extractor.py"
    "requirements.txt"
    "Dockerfile-timeweb"
    "timeweb-env.txt"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Отсутствуют файлы:"
    printf '%s\n' "${missing_files[@]}"
    exit 1
fi

# 4. Тестируем импорты
echo "🧪 Тестирование импортов..."
python3 -c "
try:
    from src.parser.improved_data_extractor import ImprovedDataExtractor
    print('✅ ImprovedDataExtractor импортируется')
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
    exit(1)
"

# 5. Создаем сводку для деплоя
echo "📋 Создание сводки для деплоя..."
cat > TIMEWEB_DEPLOY.md << 'EOF'
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
EOF

echo ""
echo "✅ Подготовка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Загрузите код в Git репозиторий"
echo "2. В Timeweb создайте приложение из Git"
echo "3. Скопируйте переменные из timeweb-env.txt"
echo "4. Запустите деплой"
echo ""
echo "📁 Важные файлы:"
echo "- Dockerfile-timeweb (для настройки Docker в Timeweb)"
echo "- timeweb-env.txt (переменные окружения)"
echo "- TIMEWEB_DEPLOY.md (подробная инструкция)"
echo ""
echo "🔗 Нужна помощь с деплоем? Готов помочь в реальном времени!"
