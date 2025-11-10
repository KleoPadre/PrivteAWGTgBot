"""
Обработчики для получения конфигураций
"""
from telegram import Update
from telegram.ext import ContextTypes

from src.services.config_generator import config_generator
from src.utils.logger import logger
from src.utils.decorators import authorized_only, log_action
from src.utils.transliterate import generate_safe_username


@authorized_only
@log_action("get_phone_config")
async def handle_phone_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик запроса конфига для телефона
    
    Args:
        update: Объект обновления
        context: Контекст бота
    """
    await _send_config(update, "phone", "📱 Телефон")


@authorized_only
@log_action("get_laptop_config")
async def handle_laptop_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик запроса конфига для ноутбука
    
    Args:
        update: Объект обновления
        context: Контекст бота
    """
    await _send_config(update, "laptop", "💻 Ноутбук")


@authorized_only
@log_action("get_router_config")
async def handle_router_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик запроса конфига для роутера
    
    Args:
        update: Объект обновления
        context: Контекст бота
    """
    await _send_config(update, "router", "🌐 Роутер")


async def _send_config(update: Update, device_type: str, device_name: str) -> None:
    """
    Генерация и отправка конфигурации пользователю
    
    Args:
        update: Объект обновления
        device_type: Тип устройства (phone, laptop, router)
        device_name: Название устройства для отображения
    """
    user = update.effective_user
    
    # Отправляем сообщение о начале генерации
    status_message = await update.message.reply_text(
        f"⏳ Генерирую конфигурацию для {device_name}...\n"
        "Это может занять несколько секунд."
    )
    
    try:
        # Генерируем безопасное имя пользователя
        safe_username = user.username or generate_safe_username(
            first_name=user.first_name,
            last_name=user.last_name,
            telegram_id=user.id
        )
        
        # Генерируем конфигурацию
        config_path = await config_generator.generate_client_config(
            telegram_id=user.id,
            username=safe_username,
            device_type=device_type,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Отправляем файл
        with open(config_path, 'rb') as config_file:
            await update.message.reply_document(
                document=config_file,
                filename=f"{user.username or f'user{user.id}'}_{device_type}.conf",
                caption=f"✅ Конфигурация для {device_name} готова!\n\n"
                        f"📝 Импортируйте этот файл в приложение AmneziaWG.\n"
                        f"🔒 Храните конфигурацию в безопасности."
            )
        
        # Удаляем сообщение о статусе
        await status_message.delete()
        
        # Удаляем временный файл
        await config_generator.cleanup_config_file(config_path)
        
        logger.info(f"Конфигурация {device_type} успешно отправлена пользователю {user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации конфигурации для {user.id}: {e}", exc_info=True)
        
        await status_message.edit_text(
            f"❌ Ошибка при генерации конфигурации.\n\n"
            f"Пожалуйста, попробуйте позже или обратитесь к администратору."
        )

