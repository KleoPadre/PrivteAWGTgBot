"""
Конфигурация приложения из переменных окружения
"""
import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Settings:
    """Настройки приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    USERS: List[int] = [
        int(user_id.strip()) 
        for user_id in os.getenv("USERS", "").split(",") 
        if user_id.strip()
    ]
    
    # AmneziaWG Configuration
    AWG_CONTAINER: str = os.getenv("AWG_CONTAINER", "amnezia-awg")
    AWG_CONFIG_PATH: str = os.getenv("AWG_CONFIG_PATH", "/opt/amnezia/awg")
    SERVER_ENDPOINT: str = os.getenv("SERVER_ENDPOINT", "")
    SERVER_PUBLIC_KEY: str = os.getenv("SERVER_PUBLIC_KEY", "")
    PRESHARED_KEY: str = os.getenv("PRESHARED_KEY", "")
    
    # Network Configuration
    CLIENT_NETWORK: str = os.getenv("CLIENT_NETWORK", "10.8.1.0/24")
    CLIENT_IP_START: str = os.getenv("CLIENT_IP_START", "10.8.1.17")
    
    # AmneziaWG Parameters
    JC: int = int(os.getenv("JC", "2"))
    JMIN: int = int(os.getenv("JMIN", "10"))
    JMAX: int = int(os.getenv("JMAX", "50"))
    S1: int = int(os.getenv("S1", "105"))
    S2: int = int(os.getenv("S2", "72"))
    H1: int = int(os.getenv("H1", "1632458931"))
    H2: int = int(os.getenv("H2", "1121810837"))
    H3: int = int(os.getenv("H3", "697439987"))
    H4: int = int(os.getenv("H4", "1960185003"))
    
    # DNS Servers
    DNS_SERVERS: str = os.getenv("DNS_SERVERS", "1.1.1.1,1.0.0.1")
    
    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/database.db")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка обязательных настроек"""
        required_fields = [
            ("BOT_TOKEN", cls.BOT_TOKEN),
            ("ADMIN_ID", cls.ADMIN_ID),
            ("SERVER_ENDPOINT", cls.SERVER_ENDPOINT),
            ("SERVER_PUBLIC_KEY", cls.SERVER_PUBLIC_KEY),
            ("PRESHARED_KEY", cls.PRESHARED_KEY),
        ]
        
        missing = []
        for field_name, field_value in required_fields:
            if not field_value or field_value == "0":
                missing.append(field_name)
        
        if missing:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}")
        
        return True


# Создаем глобальный экземпляр настроек
settings = Settings()

