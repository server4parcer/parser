#!/bin/bash
# YCLIENTS Parser - Автоматическая установка на VDS
# Альтернативный вариант деплоя для TimeWeb VDS
# =====================================================

set -e  # Остановка при ошибке

echo "🚀 YCLIENTS Parser - Установка на VDS"
echo "====================================="

# Проверка системы
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Запустите скрипт с sudo"
    exit 1
fi

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Функция установки Docker
install_docker() {
    print_status "Установка Docker..."
    
    # Удаление старых версий
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Обновление пакетов
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Добавление GPG ключа Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Добавление репозитория Docker
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Установка Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Запуск Docker
    systemctl start docker
    systemctl enable docker
    
    print_status "Docker установлен успешно"
}

# Функция установки Docker Compose
install_docker_compose() {
    print_status "Установка Docker Compose..."
    
    # Установка через pip для лучшей совместимости
    apt-get install -y python3-pip
    pip3 install docker-compose
    
    print_status "Docker Compose установлен"
}

# Функция настройки firewall
configure_firewall() {
    print_status "Настройка firewall..."
    
    # Установка ufw если не установлен
    apt-get install -y ufw
    
    # Базовые правила
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    
    # Разрешение SSH
    ufw allow ssh
    ufw allow 22
    
    # Разрешение портов приложения
    ufw allow 8000/tcp  # API порт
    ufw allow 5432/tcp  # PostgreSQL порт
    
    print_status "Firewall настроен"
}

# Функция создания пользователя
create_app_user() {
    print_status "Создание пользователя приложения..."
    
    # Создание пользователя yclients
    useradd -m -s /bin/bash yclients 2>/dev/null || true
    
    # Добавление в группу docker
    usermod -aG docker yclients
    
    print_status "Пользователь yclients создан"
}
