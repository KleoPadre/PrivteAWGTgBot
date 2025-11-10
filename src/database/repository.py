"""
Репозиторий для работы с базой данных
"""
import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.database.models import db
from src.utils.logger import logger


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    @staticmethod
    async def create_user(
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> int:
        """
        Создание пользователя
        
        Args:
            telegram_id: Telegram ID пользователя
            username: Username пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            
        Returns:
            int: ID созданного пользователя
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, username, first_name, last_name)
            )
            await conn.commit()
            
            # Получаем ID пользователя
            cursor = await conn.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = await cursor.fetchone()
            user_id = row[0] if row else cursor.lastrowid
            
            logger.info(f"Пользователь создан/получен: telegram_id={telegram_id}, id={user_id}")
            return user_id
    
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение пользователя по Telegram ID
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    async def get_all_users() -> List[Dict[str, Any]]:
        """
        Получение всех пользователей
        
        Returns:
            List[Dict[str, Any]]: Список пользователей
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM users ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


class ConfigRepository:
    """Репозиторий для работы с конфигурациями"""
    
    @staticmethod
    async def create_config(
        user_id: int,
        device_type: str,
        client_public_key: str,
        client_private_key: str,
        client_ip: str,
        config_name: str
    ) -> int:
        """
        Создание конфигурации
        
        Args:
            user_id: ID пользователя
            device_type: Тип устройства (phone, laptop, router)
            client_public_key: Публичный ключ клиента
            client_private_key: Приватный ключ клиента
            client_ip: IP адрес клиента
            config_name: Имя конфигурационного файла
            
        Returns:
            int: ID созданной конфигурации
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                INSERT INTO configs 
                (user_id, device_type, client_public_key, client_private_key, client_ip, config_name)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, device_type, client_public_key, client_private_key, client_ip, config_name)
            )
            await conn.commit()
            
            logger.info(f"Конфигурация создана: user_id={user_id}, device_type={device_type}")
            return cursor.lastrowid
    
    @staticmethod
    async def get_config(user_id: int, device_type: str) -> Optional[Dict[str, Any]]:
        """
        Получение конфигурации пользователя для устройства
        
        Args:
            user_id: ID пользователя
            device_type: Тип устройства
            
        Returns:
            Optional[Dict[str, Any]]: Данные конфигурации или None
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM configs WHERE user_id = ? AND device_type = ?",
                (user_id, device_type)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    async def get_user_configs(user_id: int) -> List[Dict[str, Any]]:
        """
        Получение всех конфигураций пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Dict[str, Any]]: Список конфигураций
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM configs WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    async def get_all_configs() -> List[Dict[str, Any]]:
        """
        Получение всех конфигураций
        
        Returns:
            List[Dict[str, Any]]: Список всех конфигураций
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT c.*, u.telegram_id, u.username 
                FROM configs c
                JOIN users u ON c.user_id = u.id
                ORDER BY c.created_at DESC
                """
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


class RequestRepository:
    """Репозиторий для работы с историей запросов"""
    
    @staticmethod
    async def log_request(user_id: int, device_type: str, action: str) -> int:
        """
        Логирование запроса пользователя
        
        Args:
            user_id: ID пользователя
            device_type: Тип устройства
            action: Выполненное действие
            
        Returns:
            int: ID записи
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "INSERT INTO requests (user_id, device_type, action) VALUES (?, ?, ?)",
                (user_id, device_type, action)
            )
            await conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    async def get_user_requests(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получение истории запросов пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
            
        Returns:
            List[Dict[str, Any]]: История запросов
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT * FROM requests 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    async def get_all_requests(limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение всей истории запросов
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            List[Dict[str, Any]]: История запросов
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT r.*, u.telegram_id, u.username 
                FROM requests r
                JOIN users u ON r.user_id = u.id
                ORDER BY r.timestamp DESC 
                LIMIT ?
                """,
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    async def get_statistics() -> Dict[str, Any]:
        """
        Получение статистики использования бота
        
        Returns:
            Dict[str, Any]: Статистика
        """
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            # Общее количество пользователей
            cursor = await conn.execute("SELECT COUNT(*) FROM users")
            total_users = (await cursor.fetchone())[0]
            
            # Общее количество конфигураций
            cursor = await conn.execute("SELECT COUNT(*) FROM configs")
            total_configs = (await cursor.fetchone())[0]
            
            # Общее количество запросов
            cursor = await conn.execute("SELECT COUNT(*) FROM requests")
            total_requests = (await cursor.fetchone())[0]
            
            # Конфигурации по типам устройств
            cursor = await conn.execute(
                """
                SELECT device_type, COUNT(*) as count 
                FROM configs 
                GROUP BY device_type
                """
            )
            configs_by_type = {row[0]: row[1] for row in await cursor.fetchall()}
            
            return {
                "total_users": total_users,
                "total_configs": total_configs,
                "total_requests": total_requests,
                "configs_by_type": configs_by_type
            }

