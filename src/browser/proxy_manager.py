"""
Proxy Manager - Управление прокси-серверами для обхода блокировок.

Этот модуль предоставляет функциональность для:
1. Загрузки и управления списком прокси-серверов
2. Ротации прокси-серверов для избежания блокировок
3. Проверки работоспособности прокси-серверов
"""
import asyncio
import aiohttp
import logging
import os
import random
import time
from typing import Dict, List, Optional, Tuple, Set
import json
from pathlib import Path

from config.settings import (
    PROXY_LIST_PATH,
    PROXY_CHECK_URL,
    PROXY_TIMEOUT,
    PROXY_CHECK_INTERVAL,
    MAX_FAILED_ATTEMPTS
)


logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Управление списком прокси-серверов с периодической проверкой работоспособности.
    """

    def __init__(self):
        """Инициализация менеджера прокси."""
        self.proxies: List[Dict[str, str]] = []
        self.working_proxies: List[Dict[str, str]] = []
        self.failed_proxies: Dict[str, int] = {}  # Прокси и количество неудачных попыток
        self.last_check_time = 0
        self.current_index = 0
        self.recently_used: Set[str] = set()  # Недавно использованные прокси
        self.max_recently_used = 5  # Количество прокси в списке недавно использованных
        self._load_proxies()

    def _load_proxies(self) -> None:
        """
        Загрузка списка прокси из файла или переменных окружения.

        Формат файла: JSON-массив объектов с полями server, username, password, port

        Пример:
        [
            {
                "server": "proxy1.example.com",
                "username": "user1",
                "password": "pass1",
                "port": 8080
            },
            ...
        ]

        Альтернативно, можно указать переменные окружения:
        PROXY_SERVERS - разделенный запятыми список серверов
        PROXY_USERNAMES - разделенный запятыми список пользователей
        PROXY_PASSWORDS - разделенный запятыми список паролей
        PROXY_PORTS - разделенный запятыми список портов
        """
        try:
            # Сначала пытаемся загрузить из файла
            proxy_path = Path(PROXY_LIST_PATH)

            if proxy_path.exists():
                with open(proxy_path, 'r', encoding='utf-8') as f:
                    self.proxies = json.load(f)
                logger.info(f"Загружено {len(self.proxies)} прокси из файла {PROXY_LIST_PATH}")

            # Если файл не существует или список пуст, пытаемся получить из переменных окружения
            elif not self.proxies:
                proxy_servers = os.environ.get('PROXY_SERVERS', '').split(',')
                proxy_usernames = os.environ.get('PROXY_USERNAMES', '').split(',')
                proxy_passwords = os.environ.get('PROXY_PASSWORDS', '').split(',')
                proxy_ports = os.environ.get('PROXY_PORTS', '').split(',')

                # Проверяем, что у нас есть хотя бы один сервер
                if proxy_servers and proxy_servers[0]:
                    # Заполняем значения, если они короче списка серверов
                    usernames = proxy_usernames + [''] * (len(proxy_servers) - len(proxy_usernames))
                    passwords = proxy_passwords + [''] * (len(proxy_servers) - len(proxy_passwords))
                    ports = proxy_ports + ['80'] * (len(proxy_servers) - len(proxy_ports))

                    # Создаем список прокси
                    self.proxies = [
                        {
                            "server": server.strip(),
                            "username": usernames[i].strip() if usernames[i] else None,
                            "password": passwords[i].strip() if passwords[i] else None,
                            "port": int(ports[i].strip()) if ports[i] else 80
                        }
                        for i, server in enumerate(proxy_servers) if server.strip()
                    ]
                    logger.info(f"Загружено {len(self.proxies)} прокси из переменных окружения")

            # Если все еще нет прокси, добавляем прямое соединение (без прокси)
            if not self.proxies:
                logger.warning("Не найдены прокси, будет использоваться прямое соединение")
                self.proxies = [{}]  # Пустой словарь означает прямое соединение

            # Инициализация рабочих прокси
            self.working_proxies = self.proxies.copy()

        except Exception as e:
            logger.error(f"Ошибка при загрузке прокси: {str(e)}")
            # В случае ошибки используем прямое соединение
            self.proxies = [{}]
            self.working_proxies = [{}]

    async def check_proxy(self, proxy: Dict[str, str]) -> bool:
        """
        Проверка работоспособности прокси.

        Args:
            proxy: Словарь с настройками прокси

        Returns:
            bool: True если прокси работает, False в противном случае
        """
        # Если пустой словарь (прямое соединение), считаем работающим
        if not proxy:
            return True

        # Форматируем URL прокси
        proxy_url = self._format_proxy_url(proxy)

        try:
            async with aiohttp.ClientSession() as session:
                # Устанавливаем таймаут для запроса
                timeout = aiohttp.ClientTimeout(total=PROXY_TIMEOUT)

                # Отправляем запрос через прокси
                async with session.get(
                    PROXY_CHECK_URL,
                    proxy=proxy_url,
                    timeout=timeout,
                    ssl=False  # Отключаем проверку SSL для тестирования
                ) as response:
                    # Если статус успешный, считаем прокси работающим
                    if response.status == 200:
                        return True
                    else:
                        logger.warning(f"Прокси {proxy_url} вернул статус {response.status}")
                        return False

        except asyncio.TimeoutError:
            logger.warning(f"Таймаут при проверке прокси {proxy_url}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке прокси {proxy_url}: {str(e)}")
            return False

    async def check_all_proxies(self) -> None:
        """
        Проверка работоспособности всех прокси в списке.
        Обновляет список working_proxies.
        """
        logger.info("Начинаем проверку всех прокси")
        new_working_proxies = []

        # Создаем задачи для проверки каждого прокси
        tasks = [self.check_proxy(proxy) for proxy in self.proxies]

        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обрабатываем результаты
        for i, result in enumerate(results):
            proxy = self.proxies[i]

            if isinstance(result, bool) and result:
                # Прокси работает
                new_working_proxies.append(proxy)

                # Если прокси был в списке неудачных, удаляем его
                proxy_url = self._format_proxy_url(proxy)
                if proxy_url in self.failed_proxies:
                    del self.failed_proxies[proxy_url]
            else:
                # Прокси не работает или произошла ошибка
                proxy_url = self._format_proxy_url(proxy)
                self.failed_proxies[proxy_url] = self.failed_proxies.get(proxy_url, 0) + 1
                logger.warning(f"Прокси {proxy_url} не работает, попыток: {self.failed_proxies[proxy_url]}")

        # Обновляем список рабочих прокси
        self.working_proxies = new_working_proxies

        # Если нет рабочих прокси, используем прямое соединение
        if not self.working_proxies:
            logger.warning("Нет рабочих прокси, используем прямое соединение")
            self.working_proxies = [{}]

        self.last_check_time = time.time()
        logger.info(f"Проверка прокси завершена. Рабочих прокси: {len(self.working_proxies)}")

    def _format_proxy_url(self, proxy: Dict[str, str]) -> str:
        """
        Форматирование словаря прокси в URL-строку.

        Args:
            proxy: Словарь с настройками прокси

        Returns:
            str: URL прокси в формате http://username:password@server:port
        """
        if not proxy:
            return ""

        server = proxy.get("server", "")
        port = proxy.get("port", 80)
        username = proxy.get("username", "")
        password = proxy.get("password", "")

        if not server:
            return ""

        # Форматируем строку прокси
        if username and password:
            return f"http://{username}:{password}@{server}:{port}"
        else:
            return f"http://{server}:{port}"

    def get_next_proxy(self) -> Dict[str, str]:
        """
        Получение следующего прокси из списка рабочих.
        С учетом ротации и проверки работоспособности.

        Returns:
            Dict[str, str]: Словарь с настройками прокси или пустой словарь для прямого соединения
        """
        # Периодически проверяем все прокси
        current_time = time.time()
        if current_time - self.last_check_time > PROXY_CHECK_INTERVAL:
            # Запускаем асинхронную проверку в фоне, но только если есть запущенный event loop
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.check_all_proxies())
            except RuntimeError:
                # No running event loop, skip creating task
                logger.debug("No running event loop, skipping proxy check")

        # Если нет рабочих прокси, возвращаем прямое соединение
        if not self.working_proxies:
            logger.warning("Нет рабочих прокси, используем прямое соединение")
            return {}

        # Выбираем следующий прокси, стараясь избегать недавно использованных
        for _ in range(len(self.working_proxies)):
            proxy = self.working_proxies[self.current_index]
            proxy_url = self._format_proxy_url(proxy)

            # Переходим к следующему индексу
            self.current_index = (self.current_index + 1) % len(self.working_proxies)

            # Если прокси не был недавно использован или у нас нет выбора, возвращаем его
            if proxy_url not in self.recently_used or len(self.working_proxies) <= 1:
                # Добавляем в список недавно использованных
                self.recently_used.add(proxy_url)

                # Если список переполнен, удаляем самый старый элемент
                if len(self.recently_used) > self.max_recently_used:
                    self.recently_used.pop()

                logger.info(f"Используем прокси: {proxy_url or 'прямое соединение'}")
                return proxy

        # Если все прокси недавно использовались, сбрасываем список и выбираем первый
        logger.info("Все прокси недавно использовались, сбрасываем список")
        self.recently_used.clear()
        return self.working_proxies[0]

    def get_random_proxy(self) -> Dict[str, str]:
        """
        Получение случайного прокси из списка рабочих.

        Returns:
            Dict[str, str]: Словарь с настройками прокси или пустой словарь для прямого соединения
        """
        # Если нет рабочих прокси, возвращаем прямое соединение
        if not self.working_proxies:
            return {}

        # Выбираем случайный прокси, исключая недавно использованные
        available_proxies = [
            p for p in self.working_proxies
            if self._format_proxy_url(p) not in self.recently_used
        ]

        # Если нет доступных прокси, берем любой из рабочих
        if not available_proxies:
            available_proxies = self.working_proxies

        # Выбираем случайный прокси
        proxy = random.choice(available_proxies)
        proxy_url = self._format_proxy_url(proxy)

        # Добавляем в список недавно использованных
        self.recently_used.add(proxy_url)

        # Если список переполнен, удаляем самый старый элемент
        if len(self.recently_used) > self.max_recently_used:
            self.recently_used.pop()

        logger.info(f"Используем случайный прокси: {proxy_url or 'прямое соединение'}")
        return proxy

    def mark_proxy_failed(self, proxy: Dict[str, str]) -> None:
        """
        Отметка прокси как неработающего.
        Увеличивает счетчик неудачных попыток для прокси.
        Если счетчик превышает MAX_FAILED_ATTEMPTS, прокси удаляется из списка рабочих.

        Args:
            proxy: Словарь с настройками прокси
        """
        # Если пустой словарь (прямое соединение), ничего не делаем
        if not proxy:
            return

        proxy_url = self._format_proxy_url(proxy)

        # Увеличиваем счетчик неудачных попыток
        self.failed_proxies[proxy_url] = self.failed_proxies.get(proxy_url, 0) + 1
        logger.warning(f"Прокси {proxy_url} отмечен как неработающий, попыток: {self.failed_proxies[proxy_url]}")

        # Если счетчик превышает максимальное значение, удаляем из списка рабочих
        if self.failed_proxies[proxy_url] >= MAX_FAILED_ATTEMPTS:
            logger.warning(f"Прокси {proxy_url} удален из списка рабочих после {MAX_FAILED_ATTEMPTS} неудачных попыток")

            # Удаляем из списка рабочих
            self.working_proxies = [p for p in self.working_proxies if self._format_proxy_url(p) != proxy_url]

            # Если список рабочих прокси пуст, используем прямое соединение
            if not self.working_proxies:
                logger.warning("Все прокси не работают, используем прямое соединение")
                self.working_proxies = [{}]

    def mark_proxy_working(self, proxy: Dict[str, str]) -> None:
        """
        Отметка прокси как работающего.
        Сбрасывает счетчик неудачных попыток для прокси.

        Args:
            proxy: Словарь с настройками прокси
        """
        # Если пустой словарь (прямое соединение), ничего не делаем
        if not proxy:
            return

        proxy_url = self._format_proxy_url(proxy)

        # Если прокси был в списке неудачных, удаляем его
        if proxy_url in self.failed_proxies:
            del self.failed_proxies[proxy_url]
            logger.info(f"Прокси {proxy_url} отмечен как работающий")

        # Если прокси не в списке рабочих, добавляем его
        if proxy not in self.working_proxies:
            self.working_proxies.append(proxy)
            logger.info(f"Прокси {proxy_url} добавлен в список рабочих")

    def get_proxy_count(self) -> Tuple[int, int]:
        """
        Получение количества всех и рабочих прокси.

        Returns:
            Tuple[int, int]: (Общее количество прокси, количество рабочих прокси)
        """
        all_count = len(self.proxies)
        working_count = len(self.working_proxies)

        # Если используется прямое соединение, считаем его как 0
        if working_count == 1 and not self.working_proxies[0]:
            working_count = 0

        return all_count, working_count