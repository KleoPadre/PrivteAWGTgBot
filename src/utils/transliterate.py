"""
Утилита для транслитерации кириллицы в латиницу
"""

# Словарь транслитерации
CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    
    ' ': '_', '-': '_', '.': '_', ',': '_'
}


def transliterate(text: str) -> str:
    """
    Транслитерация текста из кириллицы в латиницу
    
    Args:
        text: Исходный текст
        
    Returns:
        str: Транслитерированный текст
    """
    if not text:
        return ''
    
    result = []
    for char in text:
        # Транслитерируем кириллицу
        if char in CYRILLIC_TO_LATIN:
            result.append(CYRILLIC_TO_LATIN[char])
        # Оставляем латиницу, цифры и подчеркивание
        elif char.isalnum() or char == '_':
            result.append(char)
        # Пропускаем остальные символы
    
    # Убираем повторяющиеся подчеркивания
    final = ''.join(result)
    while '__' in final:
        final = final.replace('__', '_')
    
    # Убираем подчеркивания с краев
    final = final.strip('_')
    
    return final


def generate_safe_username(first_name: str = None, last_name: str = None, telegram_id: int = None) -> str:
    """
    Генерация безопасного имени пользователя для конфигурации
    
    Args:
        first_name: Имя пользователя
        last_name: Фамилия пользователя
        telegram_id: Telegram ID
        
    Returns:
        str: Безопасное имя для использования в конфигурации
    """
    # Собираем полное имя
    parts = []
    if first_name:
        parts.append(transliterate(first_name))
    if last_name:
        parts.append(transliterate(last_name))
    
    if parts:
        username = '_'.join(parts)
        # Ограничиваем длину
        if len(username) > 30:
            username = username[:30]
        return username
    
    # Если имени нет, используем ID
    if telegram_id:
        return f"user{telegram_id}"
    
    return "unknown_user"

