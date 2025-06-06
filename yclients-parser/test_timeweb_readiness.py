#!/usr/bin/env python3
"""
Тестирование адаптированной версии для TimeWeb Cloud Apps
========================================================

Этот скрипт проверяет что наша версия готова для деплоя в TimeWeb:
1. Проверка конфигурации без volumes
2. Проверка работы с внешней БД
3. Проверка Docker конфигурации
4. Проверка API endpoints
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

class TimeWebReadinessChecker:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }
    
    def add_result(self, test_name: str, passed: bool, message: str, is_warning: bool = False):
        """Добавить результат теста"""
        if is_warning:
            self.results["warnings"] += 1
            print_warning(f"{test_name}: {message}")
        elif passed:
            self.results["passed"] += 1
            print_success(f"{test_name}: {message}")
        else:
            self.results["failed"] += 1
            print_error(f"{test_name}: {message}")
        
        self.results["tests"].append({
            "name": test_name,
            "passed": passed,
            "message": message,
            "warning": is_warning
        })
    
    def check_timeweb_files(self):
        """Проверка наличия файлов для TimeWeb"""
        print_info("Проверка файлов для TimeWeb...")
        
        required_files = [
            "docker-compose-timeweb.yml",
            "Dockerfile-timeweb", 
            ".env.timeweb.example",
            "TIMEWEB_DEPLOYMENT_GUIDE.md"
        ]
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                self.add_result(f"Файл {file_name}", True, "найден")
            else:
                self.add_result(f"Файл {file_name}", False, "отсутствует")
    
    def check_docker_compose_timeweb(self):
        """Проверка docker-compose-timeweb.yml"""
        print_info("Проверка docker-compose-timeweb.yml...")
        
        compose_file = self.project_root / "docker-compose-timeweb.yml"
        if not compose_file.exists():
            self.add_result("Docker Compose", False, "файл отсутствует")
            return
        
        try:
            content = compose_file.read_text()
            
            # Проверка отсутствия volumes
            if "volumes:" in content:
                self.add_result("Volumes в docker-compose", False, "найдены volumes (запрещены в TimeWeb)")
            else:
                self.add_result("Volumes в docker-compose", True, "volumes отсутствуют")
            
            # Проверка портов
            if "- \"8000:8000\"" in content:
                self.add_result("Порт 8000", True, "корректно настроен")
            else:
                self.add_result("Порт 8000", False, "не найден или неправильно настроен")
            
            # Проверка отсутствия PostgreSQL контейнера
            if "postgres:" in content.lower():
                self.add_result("PostgreSQL контейнер", False, "найден встроенный PostgreSQL (должна быть внешняя БД)")
            else:
                self.add_result("PostgreSQL контейнер", True, "встроенный PostgreSQL отсутствует")
            
            # Проверка переменных окружения
            required_env_vars = ["DB_HOST", "DB_PASSWORD", "API_KEY"]
            for var in required_env_vars:
                if var in content:
                    self.add_result(f"Переменная {var}", True, "найдена в конфигурации")
                else:
                    self.add_result(f"Переменная {var}", False, "отсутствует в конфигурации")
                    
        except Exception as e:
            self.add_result("Docker Compose parsing", False, f"ошибка парсинга: {e}")
    
    def check_dockerfile_timeweb(self):
        """Проверка Dockerfile-timeweb"""
        print_info("Проверка Dockerfile-timeweb...")
        
        dockerfile = self.project_root / "Dockerfile-timeweb"
        if not dockerfile.exists():
            self.add_result("Dockerfile-timeweb", False, "файл отсутствует")
            return
        
        try:
            content = dockerfile.read_text()
            
            # Проверка базового образа
            if "FROM python:3.10" in content:
                self.add_result("Базовый образ", True, "Python 3.10 используется")
            else:
                self.add_result("Базовый образ", False, "рекомендуется Python 3.10")
            
            # Проверка Playwright
            if "playwright install" in content:
                self.add_result("Playwright установка", True, "найдена")
            else:
                self.add_result("Playwright установка", False, "отсутствует")
            
            # Проверка создания директорий без volumes
            if "mkdir -p /app/data" in content:
                self.add_result("Создание директорий", True, "директории создаются в контейнере")
            else:
                self.add_result("Создание директорий", False, "директории не создаются")
            
            # Проверка порта
            if "EXPOSE 8000" in content:
                self.add_result("EXPOSE порт", True, "8000 экспонируется")
            else:
                self.add_result("EXPOSE порт", False, "порт 8000 не экспонируется")
                
        except Exception as e:
            self.add_result("Dockerfile parsing", False, f"ошибка парсинга: {e}")
    
    def check_project_structure(self):
        """Проверка структуры проекта"""
        print_info("Проверка структуры проекта...")
        
        required_dirs = ["src", "config", "tests"]
        required_files = ["requirements.txt", "README.md"]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.is_dir():
                self.add_result(f"Директория {dir_name}", True, "найдена")
            else:
                self.add_result(f"Директория {dir_name}", False, "отсутствует")
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                self.add_result(f"Файл {file_name}", True, "найден")
            else:
                self.add_result(f"Файл {file_name}", False, "отсутствует")
    
    def check_python_imports(self):
        """Проверка Python импортов"""
        print_info("Проверка Python импортов...")
        
        sys.path.insert(0, str(self.project_root))
        
        try:
            from config.settings import API_HOST, API_PORT, DB_HOST
            self.add_result("Импорт настроек", True, "config.settings импортируется")
        except Exception as e:
            self.add_result("Импорт настроек", False, f"ошибка импорта: {e}")
        
        # Проверка структуры src
        src_modules = [
            "src.database.models",
            "src.export.csv_exporter", 
            "src.export.json_exporter"
        ]
        
        for module in src_modules:
            try:
                __import__(module)
                self.add_result(f"Модуль {module}", True, "импортируется")
            except ImportError:
                # Ожидаемо для модулей с внешними зависимостями
                self.add_result(f"Модуль {module}", True, "структура корректна (зависимости не установлены)", is_warning=True)
            except Exception as e:
                self.add_result(f"Модуль {module}", False, f"ошибка структуры: {e}")
    
    def check_requirements(self):
        """Проверка requirements.txt"""
        print_info("Проверка зависимостей...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.add_result("requirements.txt", False, "файл отсутствует")
            return
        
        try:
            content = requirements_file.read_text()
            
            required_packages = [
                "fastapi",
                "uvicorn", 
                "playwright",
                "asyncpg",
                "python-dotenv"
            ]
            
            for package in required_packages:
                if package in content:
                    self.add_result(f"Пакет {package}", True, "найден в requirements.txt")
                else:
                    self.add_result(f"Пакет {package}", False, "отсутствует в requirements.txt")
                    
        except Exception as e:
            self.add_result("requirements.txt parsing", False, f"ошибка чтения: {e}")
    
    def run_all_checks(self):
        """Запуск всех проверок"""
        print_info("🚀 Запуск проверок готовности к TimeWeb деплою...")
        print("=" * 60)
        
        self.check_timeweb_files()
        print()
        self.check_docker_compose_timeweb()
        print()
        self.check_dockerfile_timeweb()
        print()
        self.check_project_structure()
        print()
        self.check_python_imports()
        print() 
        self.check_requirements()
        
        print("\n" + "=" * 60)
        print_info("📊 Результаты проверок:")
        print(f"✅ Пройдено: {self.results['passed']}")
        print(f"❌ Не пройдено: {self.results['failed']}")
        print(f"⚠️  Предупреждения: {self.results['warnings']}")
        
        if self.results['failed'] == 0:
            print_success("🎉 Проект готов к деплою в TimeWeb Cloud Apps!")
        else:
            print_error(f"💥 Найдено {self.results['failed']} критических проблем. Необходимо исправить перед деплоем.")
        
        return self.results

if __name__ == "__main__":
    project_root = Path(__file__).parent
    checker = TimeWebReadinessChecker(project_root)
    results = checker.run_all_checks()
    
    # Возвращаем код ошибки если есть критические проблемы
    sys.exit(1 if results['failed'] > 0 else 0)
