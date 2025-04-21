#!/bin/bash
# Скрипт установки и настройки парсера YCLIENTS

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия необходимых утилит
check_dependencies() {
    print_message "Проверка наличия необходимых утилит..."
    
    REQUIRED_TOOLS=("git" "python3" "pip" "docker" "docker-compose")
    MISSING_TOOLS=()
    
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            MISSING_TOOLS+=("$tool")
        fi
    done
    
    if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
        print_error "Отсутствуют следующие утилиты: ${MISSING_TOOLS[*]}"
        print_message "Пожалуйста, установите их перед продолжением."
        
        if [ "$OSTYPE" == "linux-gnu"* ]; then
            print_message "Для Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y ${MISSING_TOOLS[*]}"
            print_message "Для CentOS/RHEL: sudo yum install -y ${MISSING_TOOLS[*]}"
        elif [ "$OSTYPE" == "darwin"* ]; then
            print_message "Для macOS с Homebrew: brew install ${MISSING_TOOLS[*]}"
        fi
        
        exit 1
    fi
    
    print_message "Все необходимые утилиты установлены."
}

# Клонирование репозитория
clone_repository() {
    if [ -d "yclients-parser" ]; then
        print_warning "Директория 'yclients-parser' уже существует."
        read -p "Желаете удалить и склонировать заново? (y/N): " response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_message "Удаление существующей директории..."
            rm -rf yclients-parser
        else
            print_message "Используем существующую директорию."
            return
        fi
    fi
    
    print_message "Клонирование репозитория..."
    git clone https://github.com/your-username/yclients-parser.git
    
    if [ $? -ne 0 ]; then
        print_error "Не удалось склонировать репозиторий."
        exit 1
    fi
    
    print_message "Репозиторий успешно склонирован."
}

# Настройка переменных окружения
setup_environment() {
    print_message "Настройка переменных окружения..."
    
    cd yclients-parser
    
    if [ ! -f ".env.example" ]; then
        print_error "Файл .env.example не найден."
        exit 1
    fi
    
    if [ -f ".env" ]; then
        print_warning "Файл .env уже существует."
        read -p "Желаете создать новый файл? (y/N): " response
        
        if ! [[ "$response" =~ ^[Yy]$ ]]; then
            print_message "Используем существующий файл .env."
            return
        fi
    fi
    
    cp .env.example .env
    
    # Настройка базовых переменных
    read -p "Введите API-ключ (по умолчанию 'yclients_parser_api_key'): " api_key
    api_key=${api_key:-yclients_parser_api_key}
    
    read -p "Введите URL для парсинга (через запятую): " parse_urls
    
    read -p "Введите интервал обновления в секундах (по умолчанию 600): " parse_interval
    parse_interval=${parse_interval:-600}
    
    # Настройка базы данных
    read -p "Введите хост базы данных (по умолчанию 'localhost'): " db_host
    db_host=${db_host:-localhost}
    
    read -p "Введите порт базы данных (по умолчанию '5432'): " db_port
    db_port=${db_port:-5432}
    
    read -p "Введите имя базы данных (по умолчанию 'yclients_parser'): " db_name
    db_name=${db_name:-yclients_parser}
    
    read -p "Введите пользователя базы данных (по умолчанию 'postgres'): " db_user
    db_user=${db_user:-postgres}
    
    read -p "Введите пароль базы данных (по умолчанию 'postgres'): " db_password
    db_password=${db_password:-postgres}
    
    # Настройка Supabase (опционально)
    read -p "Желаете настроить Supabase? (y/N): " setup_supabase
    
    if [[ "$setup_supabase" =~ ^[Yy]$ ]]; then
        read -p "Введите URL Supabase: " supabase_url
        read -p "Введите ключ Supabase: " supabase_key
    fi
    
    # Запись переменных в файл .env
    sed -i.bak "s/API_KEY=.*/API_KEY=$api_key/" .env
    sed -i.bak "s/PARSE_URLS=.*/PARSE_URLS=$parse_urls/" .env
    sed -i.bak "s/PARSE_INTERVAL=.*/PARSE_INTERVAL=$parse_interval/" .env
    
    sed -i.bak "s/DB_HOST=.*/DB_HOST=$db_host/" .env
    sed -i.bak "s/DB_PORT=.*/DB_PORT=$db_port/" .env
    sed -i.bak "s/DB_NAME=.*/DB_NAME=$db_name/" .env
    sed -i.bak "s/DB_USER=.*/DB_USER=$db_user/" .env
    sed -i.bak "s/DB_PASSWORD=.*/DB_PASSWORD=$db_password/" .env
    
    if [[ "$setup_supabase" =~ ^[Yy]$ ]]; then
        sed -i.bak "s/SUPABASE_URL=.*/SUPABASE_URL=$supabase_url/" .env
        sed -i.bak "s/SUPABASE_KEY=.*/SUPABASE_KEY=$supabase_key/" .env
    fi
    
    # Удаляем резервную копию
    rm -f .env.bak
    
    print_message "Переменные окружения настроены."
}

# Установка через Docker
install_docker() {
    print_message "Установка через Docker..."
    
    cd yclients-parser
    
    # Проверка наличия docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        print_error "Файл docker-compose.yml не найден."
        exit 1
    fi
    
    # Запуск контейнеров
    print_message "Запуск контейнеров..."
    docker-compose up -d
    
    if [ $? -ne 0 ]; then
        print_error "Не удалось запустить контейнеры."
        exit 1
    fi
    
    print_message "Контейнеры успешно запущены."
    print_message "API-сервер доступен по адресу: http://localhost:8000"
    print_message "Документация API: http://localhost:8000/docs"
}

# Ручная установка
install_manual() {
    print_message "Ручная установка..."
    
    cd yclients-parser
    
    # Создание виртуального окружения
    print_message "Создание виртуального окружения..."
    python3 -m venv venv
    
    # Активация виртуального окружения
    if [ "$OSTYPE" == "linux-gnu"* ] || [ "$OSTYPE" == "darwin"* ]; then
        source venv/bin/activate
    else
        source venv/Scripts/activate
    fi
    
    # Установка зависимостей
    print_message "Установка зависимостей..."
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        print_error "Не удалось установить зависимости."
        exit 1
    fi
    
    # Установка Playwright
    print_message "Установка Playwright..."
    playwright install chromium
    playwright install-deps chromium
    
    if [ $? -ne 0 ]; then
        print_error "Не удалось установить Playwright."
        exit 1
    fi
    
    # Создание необходимых директорий
    print_message "Создание необходимых директорий..."
    mkdir -p data/export
    mkdir -p logs
    
    print_message "Установка завершена."
    print_message "Для запуска парсера выполните:"
    print_message "python src/main.py --mode all"
}

# Основная функция
main() {
    print_message "Установка и настройка парсера YCLIENTS..."
    
    # Проверка зависимостей
    check_dependencies
    
    # Клонирование репозитория
    clone_repository
    
    # Настройка переменных окружения
    setup_environment
    
    # Выбор способа установки
    echo ""
    echo "Выберите способ установки:"
    echo "1. Установка через Docker (рекомендуется)"
    echo "2. Ручная установка"
    read -p "Выберите вариант (1/2): " install_option
    
    case $install_option in
        1)
            install_docker
            ;;
        2)
            install_manual
            ;;
        *)
            print_error "Неверный выбор."
            exit 1
            ;;
    esac
    
    print_message "Установка и настройка парсера YCLIENTS завершена."
}

# Запуск основной функции
main
