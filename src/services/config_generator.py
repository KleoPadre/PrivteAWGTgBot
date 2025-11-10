"""
Генератор конфигурационных файлов AmneziaWG
"""
import aiofiles
from pathlib import Path
from typing import Dict, Any

from src.config.settings import settings
from src.services.awg_manager import awg_manager
from src.database.repository import UserRepository, ConfigRepository, RequestRepository
from src.utils.logger import logger


class ConfigGenerator:
    """Генератор конфигураций для клиентов"""
    
    def __init__(self):
        """Инициализация генератора"""
        self.config_dir = Path("data/configs")
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_client_config(
        self,
        telegram_id: int,
        username: str,
        device_type: str,
        first_name: str = None,
        last_name: str = None
    ) -> str:
        """
        Генерация конфигурации для клиента
        
        Args:
            telegram_id: Telegram ID пользователя
            username: Username пользователя
            device_type: Тип устройства (phone, laptop, router)
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            
        Returns:
            str: Путь к созданному конфигурационному файлу
        """
        # Создаем или получаем пользователя в БД
        user = await UserRepository.get_user_by_telegram_id(telegram_id)
        if not user:
            user_id = await UserRepository.create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
        else:
            user_id = user['id']
        
        # Проверяем, есть ли уже конфиг для этого устройства
        existing_config = await ConfigRepository.get_config(user_id, device_type)
        
        if existing_config:
            logger.info(f"Найден существующий конфиг для пользователя {telegram_id}, устройство {device_type}")
            # Генерируем файл из существующих данных
            config_path = await self._create_config_file(
                username=username,
                device_type=device_type,
                private_key=existing_config['client_private_key'],
                client_ip=existing_config['client_ip']
            )
            
            # Логируем запрос
            await RequestRepository.log_request(user_id, device_type, "existing_config")
            
            return config_path
        
        # Генерируем новые ключи
        logger.info(f"Генерируем новый конфиг для пользователя {telegram_id}, устройство {device_type}")
        private_key, public_key = await awg_manager.generate_keypair()
        
        # Получаем свободный IP
        client_ip = await awg_manager.get_next_available_ip()
        
        # Формируем имя клиента
        device_prefix = self._get_device_prefix(device_type)
        client_name = f"{username}_{device_prefix}" if username else f"user{telegram_id}_{device_prefix}"
        
        # Добавляем peer на сервер
        await awg_manager.add_peer_to_server(
            client_public_key=public_key,
            client_ip=client_ip,
            client_name=client_name
        )
        
        # Сохраняем конфиг в БД
        config_name = f"{username}_{device_type}.conf" if username else f"user{telegram_id}_{device_type}.conf"
        await ConfigRepository.create_config(
            user_id=user_id,
            device_type=device_type,
            client_public_key=public_key,
            client_private_key=private_key,
            client_ip=client_ip,
            config_name=config_name
        )
        
        # Создаем конфигурационный файл
        config_path = await self._create_config_file(
            username=username or f"user{telegram_id}",
            device_type=device_type,
            private_key=private_key,
            client_ip=client_ip
        )
        
        # Логируем запрос
        await RequestRepository.log_request(user_id, device_type, "new_config")
        
        logger.info(f"Конфиг успешно создан: {config_path}")
        return config_path
    
    def _get_device_prefix(self, device_type: str) -> str:
        """
        Получение префикса для типа устройства
        
        Args:
            device_type: Тип устройства
            
        Returns:
            str: Префикс
        """
        prefixes = {
            "phone": "phone",
            "laptop": "laptop",
            "router": "router"
        }
        return prefixes.get(device_type, device_type)
    
    async def _create_config_file(
        self,
        username: str,
        device_type: str,
        private_key: str,
        client_ip: str
    ) -> str:
        """
        Создание конфигурационного файла
        
        Args:
            username: Username пользователя
            device_type: Тип устройства
            private_key: Приватный ключ клиента
            client_ip: IP адрес клиента
            
        Returns:
            str: Путь к созданному файлу
        """
        # Формируем имя файла
        filename = f"{username}_{device_type}.conf"
        config_path = self.config_dir / filename
        
        # Формируем содержимое конфига
        config_content = f"""[Interface]
PrivateKey = {private_key}
Address = {client_ip}/32
DNS = {settings.DNS_SERVERS}
Jc = {settings.JC}
Jmin = {settings.JMIN}
Jmax = {settings.JMAX}
S1 = {settings.S1}
S2 = {settings.S2}
H1 = {settings.H1}
H2 = {settings.H2}
H3 = {settings.H3}
H4 = {settings.H4}

[Peer]
PublicKey = {settings.SERVER_PUBLIC_KEY}
PresharedKey = {settings.PRESHARED_KEY}
Endpoint = {settings.SERVER_ENDPOINT}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
        
        # Записываем файл асинхронно
        async with aiofiles.open(config_path, 'w', encoding='utf-8') as f:
            await f.write(config_content)
        
        logger.info(f"Конфигурационный файл создан: {config_path}")
        return str(config_path)
    
    async def cleanup_config_file(self, config_path: str) -> None:
        """
        Удаление временного конфигурационного файла
        
        Args:
            config_path: Путь к файлу
        """
        try:
            Path(config_path).unlink(missing_ok=True)
            logger.debug(f"Временный конфиг удален: {config_path}")
        except Exception as e:
            logger.error(f"Ошибка удаления временного конфига: {e}")


# Глобальный экземпляр генератора
config_generator = ConfigGenerator()

