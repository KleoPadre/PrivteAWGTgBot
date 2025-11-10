"""
Модели базы данных SQLite
"""
import aiosqlite
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.config.settings import settings
from src.utils.logger import logger


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = None):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path or settings.DATABASE_PATH
        
    async def init_db(self) -> None:
        """Создание таблиц базы данных"""
        # Создаем директорию для БД, если её нет
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица конфигураций
            await db.execute("""
                CREATE TABLE IF NOT EXISTS configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    device_type TEXT NOT NULL,
                    client_public_key TEXT NOT NULL,
                    client_private_key TEXT NOT NULL,
                    client_ip TEXT NOT NULL,
                    config_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, device_type)
                )
            """)
            
            # Таблица истории запросов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    device_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Индексы для оптимизации
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_telegram_id 
                ON users(telegram_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_configs_user_device 
                ON configs(user_id, device_type)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_user_timestamp 
                ON requests(user_id, timestamp)
            """)
            
            await db.commit()
            logger.info(f"База данных инициализирована: {self.db_path}")
    
    async def get_connection(self) -> aiosqlite.Connection:
        """
        Получение подключения к БД
        
        Returns:
            aiosqlite.Connection: Подключение к базе данных
        """
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn


# Глобальный экземпляр базы данных
db = Database()

