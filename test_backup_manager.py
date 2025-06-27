import os
import shutil
import pytest
from bot.modules import backup_manager
from bot.bot_config import DB_PATH

def test_backup_and_restore(tmp_path):
    """Тестуємо резервне копіювання та відновлення бази даних"""
    # Створюємо тестову базу
    test_db = tmp_path / "context.db"
    test_db.write_text("testdata")
    
    # Підміняємо DB_PATH
    orig_db_path = backup_manager.DB_PATH
    backup_manager.DB_PATH = str(test_db)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    # Тестуємо backup
    backup_path = backup_manager.backup_database(str(backup_dir))
    assert os.path.exists(backup_path)
    
    # Псуємо базу
    test_db.write_text("corrupted")
    
    # Відновлюємо
    backup_file = os.path.basename(backup_path)
    backup_manager.restore_database(backup_file, str(backup_dir))
    assert test_db.read_text() == "testdata"
    
    # Повертаємо DB_PATH
    backup_manager.DB_PATH = orig_db_path

def test_list_backups(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    (backup_dir / "context_1.db").write_text("")
    (backup_dir / "context_2.db").write_text("")
    files = backup_manager.list_backups(str(backup_dir))
    assert "context_1.db" in files
    assert "context_2.db" in files
