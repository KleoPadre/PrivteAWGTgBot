"""
Обработчики админ-команд
"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from src.database.repository import UserRepository, ConfigRepository, RequestRepository
from src.utils.logger import logger
from src.utils.decorators import admin_only, log_action


@admin_only
@log_action("admin_stats")
async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик запроса статистики
    
    Args:
        update: Объект обновления
        context: Контекст бота
    """
    try:
        # Получаем статистику
        stats = await RequestRepository.get_statistics()
        
        # Формируем сообщение
        stats_text = "📊 <b>Статистика использования бота</b>\n\n"
        stats_text += f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        stats_text += f"📝 Всего конфигураций: <b>{stats['total_configs']}</b>\n"
        stats_text += f"📊 Всего запросов: <b>{stats['total_requests']}</b>\n\n"
        
        if stats['configs_by_type']:
            stats_text += "<b>Конфигурации по типам:</b>\n"
            device_icons = {
                "phone": "📱",
                "laptop": "💻",
                "router": "🌐"
            }
            for device_type, count in stats['configs_by_type'].items():
                icon = device_icons.get(device_type, "📄")
                stats_text += f"{icon} {device_type}: {count}\n"
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
        
        logger.info(f"Статистика отправлена администратору {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ошибка при получении статистики.\n"
            "Попробуйте позже."
        )


@admin_only
@log_action("admin_users")
async def handle_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик запроса списка пользователей
    
    Args:
        update: Объект обновления
        context: Контекст бота
    """
    try:
        # Получаем всех пользователей
        users = await UserRepository.get_all_users()
        
        if not users:
            await update.message.reply_text("📭 Пользователей пока нет.")
            return
        
        # Формируем сообщение
        users_text = f"👥 <b>Список пользователей ({len(users)})</b>\n\n"
        
        for user in users:
            # Получаем конфиги пользователя
            configs = await ConfigRepository.get_user_configs(user['id'])
            
            username = user['username'] or "без username"
            user_name = user['first_name'] or "Без имени"
            
            users_text += f"👤 <b>{user_name}</b> (@{username})\n"
            users_text += f"   ID: <code>{user['telegram_id']}</code>\n"
            users_text += f"   Конфигов: {len(configs)}\n"
            
            if configs:
                devices = [c['device_type'] for c in configs]
                device_icons = {
                    "phone": "📱",
                    "laptop": "💻",
                    "router": "🌐"
                }
                devices_str = " ".join([f"{device_icons.get(d, '📄')}{d}" for d in devices])
                users_text += f"   Устройства: {devices_str}\n"
            
            # Дата регистрации
            created_at = user.get('created_at', '')
            if created_at:
                users_text += f"   Создан: {created_at}\n"
            
            users_text += "\n"
        
        # Отправляем сообщение (может быть длинным)
        if len(users_text) > 4096:
            # Разбиваем на части
            for i in range(0, len(users_text), 4096):
                await update.message.reply_text(
                    users_text[i:i+4096],
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(users_text, parse_mode='HTML')
        
        logger.info(f"Список пользователей отправлен администратору {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ошибка при получении списка пользователей.\n"
            "Попробуйте позже."
        )


@admin_only
@log_action("admin_stats_command")
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /stats
    
    Args:
        update: Объект обновления
        context: Контекст бота
    """
    await handle_stats(update, context)


@admin_only
@log_action("admin_users_command")
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /users
    
    Args:
        update: Объект обновления
        context: Контекст бота
    """
    await handle_users(update, context)

