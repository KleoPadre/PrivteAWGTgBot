"""
Декораторы для бота
"""
import functools
from typing import Callable, Any
from telegram import Update
from telegram.ext import ContextTypes

from src.config.settings import settings
from src.utils.logger import logger


def admin_only(func: Callable) -> Callable:
    """
    Декоратор для проверки прав администратора
    
    Args:
        func: Асинхронная функция-обработчик
        
    Returns:
        Обернутая функция
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        
        if user_id != settings.ADMIN_ID:
            logger.warning(f"Попытка доступа к админ-функции от пользователя {user_id}")
            await update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return None
            
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def authorized_only(func: Callable) -> Callable:
    """
    Декоратор для проверки авторизованных пользователей
    
    Args:
        func: Асинхронная функция-обработчик
        
    Returns:
        Обернутая функция
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user_id = update.effective_user.id
        
        # Админ всегда имеет доступ
        if user_id == settings.ADMIN_ID or user_id in settings.USERS:
            return await func(update, context, *args, **kwargs)
        
        logger.warning(f"Попытка доступа от неавторизованного пользователя {user_id}")
        await update.message.reply_text(
            "⛔ У вас нет доступа к этому боту.\n\n"
            "Для получения доступа обратитесь к администратору."
        )
        return None
    
    return wrapper


def log_action(action_name: str) -> Callable:
    """
    Декоратор для логирования действий пользователей
    
    Args:
        action_name: Название действия для логирования
        
    Returns:
        Декоратор
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
            user_id = update.effective_user.id
            username = update.effective_user.username or "Без username"
            
            logger.info(f"Действие '{action_name}' от пользователя {user_id} (@{username})")
            
            try:
                result = await func(update, context, *args, **kwargs)
                logger.info(f"Действие '{action_name}' успешно выполнено для {user_id}")
                return result
            except Exception as e:
                logger.error(f"Ошибка при выполнении '{action_name}' для {user_id}: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator

