#!/usr/bin/env python3
"""
Скрипт двусторонней синхронизации между базой бота и сервером AmneziaWG
- Импортирует существующие peer'ы с сервера в базу бота
- Очищает clientsTable от "мертвых" записей
"""
import asyncio
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.repository import ConfigRepository, UserRepository
from src.services.awg_manager import awg_manager
from src.config.settings import settings
from src.utils.logger import logger


async def get_server_peers():
    """Получить список peer'ов с сервера"""
    try:
        # Читаем wg0.conf
        read_cmd = f"docker exec {settings.AWG_CONTAINER} cat {settings.AWG_CONFIG_PATH}/wg0.conf"
        stdout, stderr, code = await awg_manager._execute_command(read_cmd)
        
        if code != 0:
            logger.error(f"Ошибка чтения конфигурации: {stderr}")
            return []
        
        peers = []
        current_peer = {}
        
        for line in stdout.split('\n'):
            line = line.strip()
            
            if line.startswith('[Peer]'):
                if current_peer:
                    peers.append(current_peer)
                current_peer = {}
            elif line.startswith('PublicKey = '):
                current_peer['public_key'] = line.split('=', 1)[1].strip()
            elif line.startswith('AllowedIPs = '):
                current_peer['allowed_ips'] = line.split('=', 1)[1].strip()
            elif line.startswith('PresharedKey = '):
                current_peer['preshared_key'] = line.split('=', 1)[1].strip()
        
        if current_peer:
            peers.append(current_peer)
        
        logger.info(f"На сервере найдено {len(peers)} peer(s)")
        return peers
        
    except Exception as e:
        logger.error(f"Ошибка получения peer'ов: {e}")
        return []


async def get_clients_table():
    """Получить clientsTable"""
    try:
        read_cmd = f"docker exec {settings.AWG_CONTAINER} cat {settings.AWG_CONFIG_PATH}/clientsTable"
        stdout, stderr, code = await awg_manager._execute_command(read_cmd)
        
        if code != 0:
            return []
        
        clients = json.loads(stdout) if stdout else []
        logger.info(f"В clientsTable {len(clients)} записей")
        return clients
        
    except Exception as e:
        logger.error(f"Ошибка чтения clientsTable: {e}")
        return []


async def cleanup_clients_table():
    """Очистить clientsTable от мертвых записей"""
    logger.info("🧹 Очистка clientsTable от мертвых записей...")
    
    # Получаем реальные peer'ы
    peers = await get_server_peers()
    peer_keys = {p['public_key'] for p in peers}
    
    # Получаем clientsTable
    clients = await get_clients_table()
    
    # Фильтруем только живые
    alive_clients = [c for c in clients if c.get('clientId') in peer_keys]
    dead_clients = [c for c in clients if c.get('clientId') not in peer_keys]
    
    if not dead_clients:
        logger.info("✅ Нет мертвых записей")
        return
    
    logger.info(f"Найдено {len(dead_clients)} мертвых записей:")
    for client in dead_clients:
        name = client.get('userData', {}).get('clientName', 'Unknown')
        logger.info(f"  ❌ {name}")
    
    # Записываем только живые
    import tempfile
    import os
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(alive_clients, temp_file, indent=4, ensure_ascii=False)
    temp_file.close()
    
    copy_cmd = f"docker cp {temp_file.name} {settings.AWG_CONTAINER}:{settings.AWG_CONFIG_PATH}/clientsTable"
    stdout, stderr, code = await awg_manager._execute_command(copy_cmd)
    os.unlink(temp_file.name)
    
    if code == 0:
        logger.info(f"✅ Удалено {len(dead_clients)} мертвых записей из clientsTable")
    else:
        logger.error(f"Ошибка записи clientsTable: {stderr}")


async def import_peers_to_database():
    """Импортировать peer'ы с сервера в базу бота"""
    logger.info("📥 Импорт peer'ов в базу бота...")
    
    # Получаем peer'ы с сервера
    peers = await get_server_peers()
    
    # Получаем clientsTable для имен
    clients = await get_clients_table()
    clients_dict = {c.get('clientId'): c for c in clients}
    
    # Получаем конфиги из базы
    configs = await ConfigRepository.get_all_configs()
    existing_keys = {c['client_public_key'] for c in configs}
    
    imported = 0
    skipped = 0
    
    for peer in peers:
        public_key = peer.get('public_key')
        
        # Пропускаем уже импортированные
        if public_key in existing_keys:
            skipped += 1
            continue
        
        # Получаем имя клиента
        client = clients_dict.get(public_key, {})
        client_name = client.get('userData', {}).get('clientName', 'Unknown')
        
        # Пропускаем Admin
        if 'Admin' in client_name or 'admin' in client_name.lower():
            logger.info(f"⏭️  Пропуск админского peer: {client_name}")
            skipped += 1
            continue
        
        # Парсим имя: username_device
        parts = client_name.split('_')
        if len(parts) >= 2:
            username = '_'.join(parts[:-1])
            device_type = parts[-1]
        else:
            username = client_name
            device_type = 'phone'
        
        # Ищем или создаем пользователя
        users = await UserRepository.get_all_users()
        user = next((u for u in users if u.get('username') == username), None)
        
        if not user:
            logger.warning(f"⚠️  Пользователь {username} не найден в базе, пропуск {client_name}")
            skipped += 1
            continue
        
        # Импортируем конфиг
        client_ip = peer.get('allowed_ips', '').split('/')[0]
        
        # Создаем запись в базе (без приватного ключа, т.к. он недоступен)
        try:
            await ConfigRepository.create_config(
                user_id=user['id'],
                device_type=device_type,
                client_public_key=public_key,
                client_private_key='IMPORTED_NO_PRIVATE_KEY',  # Приватный ключ недоступен
                client_ip=client_ip,
                config_name=f"{username}_{device_type}.conf"
            )
            logger.info(f"✅ Импортирован: {client_name} ({client_ip})")
            imported += 1
        except Exception as e:
            logger.error(f"Ошибка импорта {client_name}: {e}")
    
    logger.info(f"\n📊 Итого: импортировано {imported}, пропущено {skipped}")


async def show_sync_status():
    """Показать статус синхронизации"""
    print("\n" + "="*70)
    print("📊 СТАТУС СИНХРОНИЗАЦИИ")
    print("="*70 + "\n")
    
    # Сервер
    peers = await get_server_peers()
    print(f"🔧 На сервере WireGuard: {len(peers)} peer(s)")
    for peer in peers:
        ip = peer.get('allowed_ips', 'N/A')
        print(f"   • {peer.get('public_key', 'N/A')[:20]}... ({ip})")
    
    # ClientsTable
    clients = await get_clients_table()
    print(f"\n📋 В clientsTable: {len(clients)} записей")
    peer_keys = {p['public_key'] for p in peers}
    for client in clients:
        name = client.get('userData', {}).get('clientName', 'Unknown')
        key = client.get('clientId')
        status = "✅" if key in peer_keys else "❌"
        print(f"   {status} {name}")
    
    # База бота
    configs = await ConfigRepository.get_all_configs()
    print(f"\n💾 В базе бота: {len(configs)} конфигураций")
    for config in configs:
        print(f"   • {config['config_name']} ({config['client_ip']})")
    
    # Несоответствия
    dead_clients = [c for c in clients if c.get('clientId') not in peer_keys]
    missing_in_db = [p for p in peers if p['public_key'] not in {c['client_public_key'] for c in configs}]
    
    print(f"\n⚠️  НЕСООТВЕТСТВИЯ:")
    print(f"   • Мертвых записей в clientsTable: {len(dead_clients)}")
    print(f"   • Peer'ов без записи в базе: {len(missing_in_db)}")
    
    print("\n" + "="*70 + "\n")


async def main():
    parser = argparse.ArgumentParser(description='Двусторонняя синхронизация базы бота и сервера')
    parser.add_argument('--status', action='store_true', help='Показать статус синхронизации')
    parser.add_argument('--cleanup', action='store_true', help='Очистить clientsTable от мертвых записей')
    parser.add_argument('--import', dest='import_peers', action='store_true', help='Импортировать peer\'ы в базу бота')
    parser.add_argument('--full-sync', action='store_true', help='Полная синхронизация (cleanup + import)')
    
    args = parser.parse_args()
    
    if args.status:
        await show_sync_status()
    elif args.cleanup:
        await cleanup_clients_table()
        print("\n✅ Очистка завершена")
    elif args.import_peers:
        await import_peers_to_database()
        print("\n✅ Импорт завершен")
    elif args.full_sync:
        await cleanup_clients_table()
        await import_peers_to_database()
        print("\n✅ Полная синхронизация завершена")
        await show_sync_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Прервано")
        sys.exit(0)

