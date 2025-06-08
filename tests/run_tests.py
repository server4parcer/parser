#!/usr/bin/env python
"""
Скрипт для запуска тестов парсера YCLIENTS.

Запускает все или выбранные тесты из директории tests.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


# Добавляем корневую директорию проекта в sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))


def parse_arguments():
    """
    Парсинг аргументов командной строки.
    
    Returns:
        argparse.Namespace: Аргументы командной строки
    """
    parser = argparse.ArgumentParser(description="Запуск тестов парсера YCLIENTS")
    
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Тип тестов: unit (модульные), integration (интеграционные), all (все)"
    )
    
    parser.add_argument(
        "--module",
        help="Название модуля для тестирования (например, parser, database)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Подробный вывод"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Отчет о покрытии кода тестами"
    )
    
    return parser.parse_args()


def run_tests(test_type="all", module=None, verbose=False, coverage=False):
    """
    Запуск тестов.
    
    Args:
        test_type: Тип тестов
        module: Название модуля
        verbose: Подробный вывод
        coverage: Отчет о покрытии кода
    
    Returns:
        int: Код возврата (0 - успех, 1 - ошибка)
    """
    # Определяем путь к тестам
    tests_dir = Path(__file__).resolve().parent.parent / "tests"
    
    # Формируем команду для запуска тестов
    command = ["pytest"]
    
    # Добавляем параметры
    if verbose:
        command.append("-v")
    
    if coverage:
        command.extend(["--cov=src", "--cov-report=term", "--cov-report=html"])
    
    # Определяем тесты для запуска
    if test_type == "unit":
        # Модульные тесты не содержат в имени "integration"
        test_path = [str(f) for f in tests_dir.glob("test_*.py") 
                   if "integration" not in f.name.lower()]
    elif test_type == "integration":
        # Интеграционные тесты содержат в имени "integration"
        test_path = [str(f) for f in tests_dir.glob("test_*integration*.py")]
    else:  # all
        test_path = [str(tests_dir)]
    
    # Если указан модуль, фильтруем тесты
    if module:
        module_test_path = [str(f) for f in tests_dir.glob(f"test_{module}*.py")]
        
        # Если найдены тесты для указанного модуля, используем их
        if module_test_path:
            test_path = module_test_path
        else:
            print(f"Предупреждение: Тесты для модуля '{module}' не найдены")
            return 1
    
    # Добавляем путь к тестам в команду
    command.extend(test_path)
    
    # Выводим информацию о запуске
    print(f"Запуск тестов: {' '.join(command)}")
    
    # Запускаем тесты
    result = subprocess.run(command)
    
    return result.returncode


def main():
    """Основная функция."""
    # Парсим аргументы командной строки
    args = parse_arguments()
    
    # Запускаем тесты
    return run_tests(args.type, args.module, args.verbose, args.coverage)


if __name__ == "__main__":
    # Запускаем основную функцию
    sys.exit(main())
