# Модуль для резервного копіювання бази даних
import os
import shutil
import time
import logging
from typing import List
from bot.bot_config import DB_PATH

def backup_database(backup_dir: str = "data/backups") -> str:
    """Створює резервну копію бази даних SQLite"""
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"context_{timestamp}.db")
    try:
        shutil.copy(DB_PATH, backup_path)
        logging.info(f"Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        raise

def list_backups(backup_dir: str = "data/backups") -> List[str]:
    """Повертає список резервних копій"""
    if not os.path.exists(backup_dir):
        return []
    return sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')])

def restore_database(backup_file: str, backup_dir: str = "data/backups") -> None:
    """Відновлює базу даних з резервної копії"""
    backup_path = os.path.join(backup_dir, backup_file)
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    shutil.copy(backup_path, DB_PATH)
    logging.info(f"Database restored from: {backup_path}")
