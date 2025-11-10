"""
Фильтры для Telegram бота
"""
from telegram import Update
from telegram.ext import filters

from src.config.settings import settings


class AuthorizedUsersFilter(filters.MessageFilter):
    """Фильтр для авторизованных пользователей"""
    
    def filter(self, message):
        """
        Проверка авторизации пользователя
        
        Args:
            message: Сообщение
            
        Returns:
            bool: True если пользователь авторизован
        """
        user_id = message.from_user.id
        return user_id == settings.ADMIN_ID or user_id in settings.USERS


class AdminFilter(filters.MessageFilter):
    """Фильтр для администратора"""
    
    def filter(self, message):
        """
        Проверка прав администратора
        
        Args:
            message: Сообщение
            
        Returns:
            bool: True если пользователь - администратор
        """
        return message.from_user.id == settings.ADMIN_ID


# Создаем экземпляры фильтров
authorized_users_filter = AuthorizedUsersFilter()
admin_filter = AdminFilter()

