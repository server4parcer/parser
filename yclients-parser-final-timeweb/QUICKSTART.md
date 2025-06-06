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
