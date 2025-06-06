#!/bin/bash
# Создание финального ZIP архива для клиента
# ============================================

echo "🚀 Создание финального пакета YCLIENTS Parser для TimeWeb..."

PROJECT_DIR="/Users/m/git/clients/yclents/yclients-parser"
FINAL_DIR="/Users/m/git/clients/yclents/yclients-parser-final-timeweb"
ZIP_NAME="yclients-parser-timeweb-ready.zip"

# Создаем чистую директорию для финального пакета
rm -rf "$FINAL_DIR" 2>/dev/null
mkdir -p "$FINAL_DIR"

echo "📁 Копирование файлов..."

# Копируем основные файлы проекта
cp -r "$PROJECT_DIR/src" "$FINAL_DIR/"
cp -r "$PROJECT_DIR/config" "$FINAL_DIR/"
cp -r "$PROJECT_DIR/tests" "$FINAL_DIR/"
cp -r "$PROJECT_DIR/scripts" "$FINAL_DIR/"

# Копируем конфигурационные файлы
cp "$PROJECT_DIR/requirements.txt" "$FINAL_DIR/"
cp "$PROJECT_DIR/docker-compose-timeweb.yml" "$FINAL_DIR/docker-compose.yml"
cp "$PROJECT_DIR/Dockerfile-timeweb" "$FINAL_DIR/Dockerfile"
cp "$PROJECT_DIR/.env.timeweb.example" "$FINAL_DIR/.env.example"
cp "$PROJECT_DIR/.gitignore" "$FINAL_DIR/"

# Копируем документацию
cp "$PROJECT_DIR/README-TIMEWEB.md" "$FINAL_DIR/README.md"
cp "$PROJECT_DIR/TIMEWEB_DEPLOYMENT_GUIDE.md" "$FINAL_DIR/"

# Копируем тестовые и вспомогательные файлы
cp "$PROJECT_DIR/test_timeweb_readiness.py" "$FINAL_DIR/"
cp "$PROJECT_DIR/vds-install.sh" "$FINAL_DIR/"

# Создаем структуру директорий
mkdir -p "$FINAL_DIR/data/export"
mkdir -p "$FINAL_DIR/logs"

# Создаем файл с URL примером
cat > "$FINAL_DIR/data/urls.txt" << EOF
# Примеры URL для парсинга YCLIENTS
# Замените на ваши реальные URL
https://yclients.com/company/111111/booking
https://yclients.com/company/222222/booking
EOF

echo "📝 Создание финальной документации..."

# Создаем файл QUICKSTART.md
cat > "$FINAL_DIR/QUICKSTART.md" << 'EOF'
# 🚀 Быстрый старт YCLIENTS Parser для TimeWeb

## 1. Создайте PostgreSQL базу данных в TimeWeb Cloud
- Зайдите в https://timeweb.cloud/my/
- Создайте PostgreSQL базу данных
- Сохраните данные подключения

## 2. Загрузите код в GitHub
```bash
git clone <ваш-репозиторий>
cd yclients-parser
git add .
git commit -m "TimeWeb deployment"
git push origin main
```

## 3. Деплой в TimeWeb Cloud Apps
- Создайте приложение типа "Docker Compose"
- Подключите GitHub репозиторий  
- Настройте переменные окружения из .env.example
- Запустите деплой

## 4. Проверьте работу
- API: https://ваше-приложение.timeweb.me/docs
- Статус: https://ваше-приложение.timeweb.me/status

Подробные инструкции: TIMEWEB_DEPLOYMENT_GUIDE.md
EOF

echo "🧪 Запуск финального тестирования..."

# Переходим в финальную директорию и тестируем
cd "$FINAL_DIR"
python3 test_timeweb_readiness.py

if [ $? -eq 0 ]; then
    echo "✅ Все тесты прошли успешно!"
    
    # Создаем ZIP архив
    cd /Users/m/git/clients/yclents/
    zip -r "$ZIP_NAME" yclients-parser-final-timeweb/ -x "*.DS_Store" "*/__pycache__/*"
    
    echo "📦 Создан архив: $ZIP_NAME"
    echo "📊 Размер архива: $(du -h "$ZIP_NAME" | cut -f1)"
    echo ""
    echo "🎉 Готово! Архив готов для передачи клиенту."
    echo ""
    echo "📋 Содержимое архива:"
    echo "- Адаптированный код для TimeWeb Cloud Apps"
    echo "- Docker конфигурация без volumes"
    echo "- Подробная инструкция по деплою"
    echo "- Автоматические тесты готовности"
    echo "- Примеры конфигурации"
    echo ""
    echo "✉️ Инструкция для клиента:"
    echo "1. Распакуйте архив"
    echo "2. Прочитайте README.md и QUICKSTART.md"
    echo "3. Следуйте TIMEWEB_DEPLOYMENT_GUIDE.md"
    echo "4. При проблемах запустите: python3 test_timeweb_readiness.py"
    
else
    echo "❌ Тесты не прошли! Проверьте ошибки выше."
    exit 1
fi
