"""
Фаза 2: Покращений backup manager з автоматизацією
"""

import os
import shutil
import zipfile
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
import hashlib

logger = logging.getLogger(__name__)

class AdvancedBackupManager:
    """Покращений менеджер резервного копіювання"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Конфігурація
        self.max_backups = int(os.getenv('BACKUP_MAX_COUNT', '10'))
        self.backup_interval_hours = int(os.getenv('BACKUP_INTERVAL_HOURS', '6'))
        self.compression_level = 6
        
        # Файли та папки для backup
        self.backup_targets = [
            "data/",
            "bot/bot_config.py", 
            ".env",
            "requirements.txt",
            "docker-compose.yml",
            "Dockerfile"
        ]
        
        # Файли для виключення
        self.exclude_patterns = [
            "*.pyc",
            "__pycache__",
            "*.log",
            "*.tmp"
        ]
    
    async def create_backup(self, backup_type: str = "auto") -> Optional[str]:
        """
        Створення резервної копії
        
        Args:
            backup_type: тип backup ('auto', 'manual', 'pre-deploy')
        
        Returns:
            шлях до створеного backup файлу або None при помилці
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"gryag_backup_{backup_type}_{timestamp}.zip"
            backup_path = self.backup_dir / backup_name
            
            print(f"📦 Створення backup: {backup_name}")
            
            # Створюємо metadata
            metadata = await self._create_metadata(backup_type)
            
            # Створюємо zip архів
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, 
                               compresslevel=self.compression_level) as zipf:
                
                # Додаємо metadata
                zipf.writestr("backup_metadata.json", 
                            json.dumps(metadata, indent=2, ensure_ascii=False))
                
                # Додаємо файли та папки
                for target in self.backup_targets:
                    await self._add_to_backup(zipf, target)
            
            # Перевіряємо целостность
            if await self._verify_backup(backup_path):
                # Очищуємо старі backup
                await self._cleanup_old_backups()
                
                file_size = backup_path.stat().st_size / (1024 * 1024)  # MB
                print(f"✅ Backup створено: {backup_name} ({file_size:.1f} MB)")
                
                # Логуємо успішний backup
                await self._log_backup_event("created", backup_name, metadata)
                
                return str(backup_path)
            else:
                print(f"❌ Backup пошкоджено: {backup_name}")
                backup_path.unlink(missing_ok=True)
                return None
                
        except Exception as e:
            logger.error(f"Помилка створення backup: {e}")
            print(f"💥 Помилка backup: {e}")
            return None
    
    async def restore_backup(self, backup_path: str, 
                           restore_targets: Optional[List[str]] = None) -> bool:
        """
        Відновлення з резервної копії
        
        Args:
            backup_path: шлях до backup файлу
            restore_targets: список файлів для відновлення (None = всі)
        
        Returns:
            True якщо відновлення успішне
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                print(f"❌ Backup файл не знайдено: {backup_path}")
                return False
            
            # Перевіряємо целостность
            if not await self._verify_backup(backup_file):
                print(f"❌ Backup пошкоджено: {backup_path}")
                return False
            
            print(f"🔄 Відновлення з backup: {backup_file.name}")
            
            # Створюємо backup поточного стану перед відновленням
            pre_restore_backup = await self.create_backup("pre-restore")
            
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Читаємо metadata
                metadata = json.loads(zipf.read("backup_metadata.json"))
                print(f"📋 Backup створено: {metadata['timestamp']}")
                print(f"📋 Тип: {metadata['backup_type']}")
                
                # Відновлюємо файли
                files_to_restore = restore_targets or zipf.namelist()
                
                for file_name in files_to_restore:
                    if file_name == "backup_metadata.json":
                        continue
                    
                    try:
                        # Створюємо директорії якщо потрібно
                        target_path = Path(file_name)
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Відновлюємо файл
                        zipf.extract(file_name, ".")
                        print(f"✅ Відновлено: {file_name}")
                        
                    except Exception as e:
                        print(f"⚠️  Помилка відновлення {file_name}: {e}")
            
            await self._log_backup_event("restored", backup_file.name, metadata)
            print(f"🎉 Відновлення завершено!")
            
            if pre_restore_backup:
                print(f"💾 Pre-restore backup: {Path(pre_restore_backup).name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Помилка відновлення backup: {e}")
            print(f"💥 Помилка відновлення: {e}")
            return False
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """Список доступних backup"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                # Читаємо metadata
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    metadata = json.loads(zipf.read("backup_metadata.json"))
                
                file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
                
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size_mb': round(file_size, 1),
                    'created': metadata['timestamp'],
                    'type': metadata['backup_type'],
                    'bot_version': metadata.get('bot_version', 'Unknown'),
                    'file_count': metadata.get('file_count', 0)
                })
                
            except Exception as e:
                logger.warning(f"Не вдалося прочитати metadata для {backup_file}: {e}")
        
        # Сортуємо за датою створення
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    async def get_backup_stats(self) -> Dict[str, Any]:
        """Статистика backup"""
        backups = await self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size_mb': 0,
                'latest_backup': None,
                'backup_types': {}
            }
        
        total_size = sum(b['size_mb'] for b in backups)
        backup_types = {}
        
        for backup in backups:
            backup_type = backup['type']
            backup_types[backup_type] = backup_types.get(backup_type, 0) + 1
        
        return {
            'total_backups': len(backups),
            'total_size_mb': round(total_size, 1),
            'latest_backup': backups[0],
            'backup_types': backup_types,
            'max_backups': self.max_backups,
            'backup_interval_hours': self.backup_interval_hours
        }
    
    async def auto_backup_check(self) -> bool:
        """Перевірка чи потрібен автоматичний backup"""
        backups = await self.list_backups()
        
        if not backups:
            return True  # Немає жодного backup
        
        # Знаходимо останній auto backup
        auto_backups = [b for b in backups if b['type'] == 'auto']
        if not auto_backups:
            return True
        
        # Перевіряємо чи пройшов інтервал
        latest_auto = datetime.fromisoformat(auto_backups[0]['created'])
        interval = timedelta(hours=self.backup_interval_hours)
        
        return datetime.now() - latest_auto >= interval
    
    async def _create_metadata(self, backup_type: str) -> Dict[str, Any]:
        """Створення metadata для backup"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'backup_type': backup_type,
            'bot_version': '3.0',  # Можна отримати з конфігурації
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            'targets': self.backup_targets,
            'file_count': 0,
            'checksum': ''
        }
        
        # Додаємо інформацію про середовище
        try:
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_content = f.read()
                    # Не зберігаємо чутливі дані, тільки список ключів
                    env_keys = [line.split('=')[0] for line in env_content.split('\n') 
                              if '=' in line and not line.startswith('#')]
                    metadata['env_keys'] = env_keys
        except Exception:
            pass
        
        return metadata
    
    async def _add_to_backup(self, zipf: zipfile.ZipFile, target: str):
        """Додавання файлу/папки до backup"""
        target_path = Path(target)
        
        if not target_path.exists():
            print(f"⚠️  Пропущено (не існує): {target}")
            return
        
        if target_path.is_file():
            # Додаємо файл
            zipf.write(target_path, target_path.name)
            
        elif target_path.is_dir():
            # Додаємо всю папку
            for file_path in target_path.rglob('*'):
                if file_path.is_file():
                    # Перевіряємо чи не виключений файл
                    if not self._should_exclude(file_path):
                        # Зберігаємо відносний шлях
                        arc_name = file_path.relative_to(target_path.parent)
                        zipf.write(file_path, str(arc_name))
    
    def _should_exclude(self, file_path: Path) -> bool:
        """Перевірка чи потрібно виключити файл"""
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return True
        return False
    
    async def _verify_backup(self, backup_path: Path) -> bool:
        """Перевірка целостности backup"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Перевіряємо чи можемо прочитати всі файли
                test_result = zipf.testzip()
                if test_result:
                    logger.error(f"Backup corrupted: {test_result}")
                    return False
                
                # Перевіряємо наявність metadata
                if "backup_metadata.json" not in zipf.namelist():
                    logger.error("Backup missing metadata")
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    async def _cleanup_old_backups(self):
        """Очищення старих backup"""
        backups = await self.list_backups()
        
        if len(backups) <= self.max_backups:
            return
        
        # Видаляємо найстаріші backup
        backups_to_delete = backups[self.max_backups:]
        
        for backup in backups_to_delete:
            try:
                Path(backup['path']).unlink()
                print(f"🗑️  Видалено старий backup: {backup['filename']}")
            except Exception as e:
                logger.error(f"Не вдалося видалити backup {backup['filename']}: {e}")
    
    async def _log_backup_event(self, event_type: str, backup_name: str, metadata: Dict[str, Any]):
        """Логування подій backup"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'backup_name': backup_name,
            'metadata': metadata
        }
        
        # Зберігаємо в лог файл
        log_file = self.backup_dir / "backup_log.json"
        
        try:
            # Читаємо існуючий лог
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
            else:
                log_data = []
            
            # Додаємо новий запис
            log_data.append(log_entry)
            
            # Зберігаємо тільки останні 100 записів
            if len(log_data) > 100:
                log_data = log_data[-100:]
            
            # Записуємо лог
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Не вдалося записати backup лог: {e}")

# Глобальний екземпляр
backup_manager = AdvancedBackupManager()

# Функції для зворотної сумісності
async def create_backup(backup_type: str = "manual") -> Optional[str]:
    """Швидке створення backup"""
    return await backup_manager.create_backup(backup_type)

def backup_database():
    """Синхронна версія для зворотної сумісності"""
    try:
        return asyncio.run(create_backup("auto"))
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None

async def auto_backup_if_needed():
    """Автоматичний backup якщо потрібен"""
    if await backup_manager.auto_backup_check():
        return await backup_manager.create_backup("auto")
    return None

if __name__ == "__main__":
    # Тестування backup manager
    async def test_backup():
        print("🧪 Тестування backup manager...")
        
        # Створення backup
        backup_path = await backup_manager.create_backup("test")
        if backup_path:
            print(f"✅ Backup створено: {backup_path}")
            
            # Список backup
            backups = await backup_manager.list_backups()
            print(f"📋 Знайдено {len(backups)} backup")
            
            # Статистика
            stats = await backup_manager.get_backup_stats()
            print(f"📊 Всього backup: {stats['total_backups']}")
            print(f"📊 Загальний розмір: {stats['total_size_mb']} MB")
        
    asyncio.run(test_backup())
