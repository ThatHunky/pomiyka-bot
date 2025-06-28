#!/usr/bin/env python3
"""
Скрипт для створення архіву з актуальною версією Гряг-бота.
Включає лише необхідні файли для production deployment.
"""

import zipfile
import os
from pathlib import Path
from datetime import datetime

def create_bot_archive():
    """Створити архів з актуальною версією бота."""
    
    # Визначити кореневу директорію проєкту
    root_dir = Path(__file__).parent
    
    # Ім'я архіву з актуальною датою та версією
    version = "v2.8-docker-optimized"
    archive_name = f"gryag-bot-{version}-{datetime.now().strftime('%Y%m%d')}.zip"
    archive_path = root_dir / archive_name
    
    # Файли та директорії для включення в архів
    files_to_include = [
        # Основні файли
        "requirements.txt",
        "start.py",
        "Dockerfile", 
        "docker-compose.yml",
        "docker-compose.prod.yml",
        ".dockerignore",
        "README.md",
        "CHANGELOG.md",
        
        # Документація
        "GEMINI_ENHANCED_INTEGRATION.md",
        "GEMINI_INTEGRATION_COMPLETION_REPORT.md", 
        "API_VERSION_UPDATE_REPORT.md",
        "PROJECT_ANALYSIS.md",
        "AGENTS.md",
        "DEPLOYMENT.md",
        
        # Конфігурація (приклад)
        ".env.sample",
        
        # Тести (критичні)
        "test_integration_gemini.py",
        "test_api_version.py",
        "test_enhanced_behavior_unit.py",
        "test_health_checker_unit.py",
        "test_backup_manager.py",
        "test_rate_limiter_unit.py",
        
        # Весь модуль бота
        "bot/",
    ]
    
    # Файли та директорії для виключення
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo", 
        "*.db",
        "*.json",
        ".env",
        "data/",
        "*.zip",
        "*.tar.gz"
    ]
    
    # Винятки з виключень (файли, які потрібно включити навіть якщо вони підпадають під фільтр)
    include_exceptions = [
        "test_integration_gemini.py",
        "test_api_version.py",
        ".env.sample",
        ".env.example"
    ]
    
    def should_exclude(file_path: Path) -> bool:
        """Перевірити, чи потрібно виключити файл."""
        # Завжди включати файли з винятків
        if file_path.name in include_exceptions:
            return False
            
        file_str = str(file_path)
        for pattern in exclude_patterns:
            if pattern in file_str or file_path.name.startswith(pattern.replace("*", "")):
                return True
        return False
    
    print(f"🚀 Створюємо архív: {archive_name}")
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        files_added = 0
        
        for item in files_to_include:
            item_path = root_dir / item
            
            if item_path.is_file():
                # Додати файл
                if not should_exclude(item_path):
                    zipf.write(item_path, item)
                    files_added += 1
                    print(f"✅ Додано файл: {item}")
                else:
                    print(f"⚠️  Пропущено файл: {item} (виключено)")
                    
            elif item_path.is_dir():
                # Додати всю директорію рекурсивно
                for root, dirs, files in os.walk(item_path):
                    # Виключити небажані директорії
                    dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
                    
                    for file in files:
                        file_path = Path(root) / file
                        if not should_exclude(file_path):
                            # Відносний шлях в архіві
                            arcname = file_path.relative_to(root_dir)
                            zipf.write(file_path, arcname)
                            files_added += 1
                            print(f"✅ Додано: {arcname}")
                        else:
                            print(f"⚠️  Пропущено: {file_path} (виключено)")
            else:
                print(f"❌ Не знайдено: {item}")
    
    # Інформація про створений архів
    archive_size = archive_path.stat().st_size
    print(f"\n🎉 Архів створено успішно!")
    print(f"📁 Файл: {archive_path}")
    print(f"📊 Розмір: {archive_size / 1024:.1f} KB")
    print(f"📋 Файлів додано: {files_added}")
    
    return archive_path

if __name__ == "__main__":
    try:
        archive = create_bot_archive()
        print(f"\n✨ Готово! Архів збережено: {archive}")
    except Exception as e:
        print(f"❌ Помилка при створенні архіву: {e}")
        exit(1)
