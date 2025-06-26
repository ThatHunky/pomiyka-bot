#!/usr/bin/env python3
"""
Скрипт для створення релізу Гряг-бота
"""
import os
import zipfile
from pathlib import Path

def create_release():
    """Створює архів з релізом бота"""
    
    # Версія з CHANGELOG
    version = "v2.4"
    
    # Поточна директорія
    current_dir = Path(__file__).parent
    
    # Назва архіву
    archive_name = f"gryag-bot-release-{version}.zip"
    archive_path = current_dir / archive_name
    
    # Файли та папки для включення в реліз
    include_files = [
        "bot/",
        "requirements.txt", 
        "start.py",
        "README.md",
        "CHANGELOG.md",
        "Dockerfile",
        "docker-compose.yml",
        ".env.example"
    ]
    
    # Файли та папки для виключення
    exclude_patterns = [
        "__pycache__",
        ".git",
        ".env",
        "data/",
        "*.pyc",
        "*.pyo",
        "test_bot.py",
        "create_release.py",
        "gryag-bot-release*.zip",
        "gryag-bot-release*.tar.gz"
    ]
    
    print(f"Створюю реліз {version}...")
    
    try:
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in include_files:
                item_path = current_dir / item
                
                if item_path.is_file():
                    # Додаємо файл
                    zipf.write(item_path, item)
                    print(f"Додано файл: {item}")
                    
                elif item_path.is_dir():
                    # Додаємо всі файли з директорії
                    for root, dirs, files in os.walk(item_path):
                        # Виключаємо небажані директорії
                        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                        
                        for file in files:
                            # Виключаємо небажані файли
                            if any(pattern in file for pattern in exclude_patterns):
                                continue
                                
                            file_path = Path(root) / file
                            arc_path = file_path.relative_to(current_dir)
                            zipf.write(file_path, arc_path)
                            print(f"Додано файл: {arc_path}")
                            
        print(f"\n✅ Реліз успішно створено: {archive_name}")
        print(f"📁 Розмір архіву: {archive_path.stat().st_size / 1024:.1f} KB")
        
        # Перевіряємо вміст архіву
        print(f"\n📋 Вміст архіву:")
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            for name in sorted(zipf.namelist()):
                print(f"  {name}")
                
    except Exception as e:
        print(f"❌ Помилка при створенні архіву: {e}")
        return False
        
    return True

if __name__ == "__main__":
    create_release()
