#!/usr/bin/env python3
"""
Створення архіву emergency fix для Гряг-бота
Включає всі необхідні файли для швидкого деплою
"""
import os
import zipfile
import shutil
from datetime import datetime

def create_emergency_archive():
    """Створює архів з emergency fix файлами"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"gryag-bot-emergency-fix-{timestamp}.zip"
    
    print("📦 Створення emergency архіву...")
    print("=" * 60)
    
    # Файли що включаємо в архів
    files_to_include = [
        # Emergency основні файли
        ("bot/main_emergency.py", "bot/main_emergency.py"),
        ("docker-compose.emergency.yml", "docker-compose.emergency.yml"),
        (".env.emergency", ".env.emergency"),
        
        # Оновлені конфігурації
        ("bot/bot_config.py", "bot/bot_config.py"),
        (".env", ".env.example"),  # Як приклад
        ("docker-compose.yml", "docker-compose.yml"),
        
        # Документація
        ("EMERGENCY_FIX_REPORT.md", "EMERGENCY_FIX_REPORT.md"),
        ("README.md", "README.md"),
        
        # Тести
        ("test_old_messages_fix.py", "test_old_messages_fix.py"),
        
        # Dockerfile для збірки
        ("Dockerfile", "Dockerfile"),
        ("requirements.txt", "requirements.txt"),
        
        # Важливі модулі (якщо є)
        ("bot/modules/gemini_enhanced.py", "bot/modules/gemini_enhanced.py"),
        ("bot/modules/smart_behavior.py", "bot/modules/smart_behavior.py"),
        ("bot/modules/context.py", "bot/modules/context.py"),
        ("bot/modules/reactions.py", "bot/modules/reactions.py"),
        ("bot/modules/management.py", "bot/modules/management.py"),
    ]
    
    # Створюємо архів
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        
        # Додаємо основні файли
        for source_path, archive_path in files_to_include:
            if os.path.exists(source_path):
                zipf.write(source_path, archive_path)
                print(f"✅ Додано: {source_path} -> {archive_path}")
            else:
                print(f"⚠️ Пропущено (не знайдено): {source_path}")
        
        # Додаємо всі файли з bot/modules/ якщо директорія існує
        if os.path.exists("bot/modules"):
            for root, dirs, files in os.walk("bot/modules"):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        archive_path = file_path.replace("\\", "/")  # Нормалізуємо шляхи
                        if file_path not in [item[0] for item in files_to_include]:
                            zipf.write(file_path, archive_path)
                            print(f"📁 Додано модуль: {file_path}")
        
        # Створюємо README для архіву
        readme_content = f"""# 🚨 EMERGENCY FIX АРХІВ - Гряг-бот
Створено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚀 ШВИДКИЙ DEPLOY

1. **Розпакуйте архів:**
   ```bash
   unzip {archive_name}
   cd emergency-deploy/
   ```

2. **Налаштуйте токени:**
   ```bash
   cp .env.emergency .env
   # Відредагуйте .env - додайте ваші токени!
   ```

3. **Запустіть emergency версію:**
   ```bash
   # Зупиніть старий бот
   docker-compose down
   
   # Запустіть новий
   docker-compose -f docker-compose.emergency.yml up -d
   ```

4. **Перевірте логи:**
   ```bash
   docker-compose -f docker-compose.emergency.yml logs -f
   ```

## ✅ ЩО ВИПРАВЛЕНО

- ❌ **НЕ БУДЕ** спаму старими повідомленнями при запуску
- ✅ **БУДЕ** якісніші відповіді (Gemini 2.5 Flash)
- ✅ **БУДЕ** менше випадкових відповідей (проти спаму)
- ✅ **БУДЕ** працювати на порту 1488

## 📋 ВМІСТ АРХІВУ

- `bot/main_emergency.py` - основний файл з виправленнями
- `docker-compose.emergency.yml` - Docker конфігурація
- `.env.emergency` - налаштування для продакшн
- `EMERGENCY_FIX_REPORT.md` - детальний звіт
- `test_old_messages_fix.py` - тест логіки ігнорування

## 🆘 ПІДТРИМКА

У разі проблем перевірте:
1. Чи правильно вказані токени в .env
2. Чи зупинений старий контейнер
3. Чи доступний порт 1488

---
**Emergency Fix v1.0** | Гряг-бот Project
"""
        
        # Додаємо README в архів
        zipf.writestr("README_EMERGENCY.md", readme_content)
        print("📋 Додано: README_EMERGENCY.md")
        
        # Додаємо скрипт швидкого деплою
        deploy_script = """#!/bin/bash
# 🚨 EMERGENCY DEPLOY SCRIPT

echo "🚨 EMERGENCY DEPLOY - Гряг-бот"
echo "=============================="

# Перевіряємо чи є .env
if [ ! -f ".env" ]; then
    echo "⚠️ Копіюємо .env.emergency -> .env"
    cp .env.emergency .env
    echo "❗ ВАЖЛИВО: Відредагуйте .env та додайте ваші токени!"
    echo "❗ Натисніть Enter коли будете готові..."
    read
fi

# Зупиняємо старий бот
echo "🛑 Зупиняємо старий бот..."
docker-compose down 2>/dev/null || true

# Запускаємо emergency версію
echo "🚀 Запускаємо emergency версію..."
docker-compose -f docker-compose.emergency.yml up -d

# Показуємо логи
echo "📋 Логи (Ctrl+C для виходу):"
sleep 2
docker-compose -f docker-compose.emergency.yml logs -f
"""
        
        zipf.writestr("emergency_deploy.sh", deploy_script)
        print("🚀 Додано: emergency_deploy.sh")
        
        # Додаємо Windows bat файл
        deploy_bat = """@echo off
REM Emergency Deploy Script for Windows

echo 🚨 EMERGENCY DEPLOY - Гряг-бот
echo ==============================

REM Перевіряємо чи є .env
if not exist ".env" (
    echo ⚠️ Копіюємо .env.emergency -^> .env
    copy .env.emergency .env
    echo ❗ ВАЖЛИВО: Відредагуйте .env та додайте ваші токени!
    echo ❗ Натисніть Enter коли будете готові...
    pause
)

REM Зупиняємо старий бот
echo 🛑 Зупиняємо старий бот...
docker-compose down 2>nul

REM Запускаємо emergency версію
echo 🚀 Запускаємо emergency версію...
docker-compose -f docker-compose.emergency.yml up -d

REM Показуємо логи
echo 📋 Логи (Ctrl+C для виходу):
timeout /t 2 >nul
docker-compose -f docker-compose.emergency.yml logs -f
"""
        
        zipf.writestr("emergency_deploy.bat", deploy_bat)
        print("🖥️ Додано: emergency_deploy.bat")
    
    print("\n🎉 АРХІВ СТВОРЕНО!")
    print("=" * 60)
    print(f"📦 Файл: {archive_name}")
    print(f"📏 Розмір: {os.path.getsize(archive_name) / 1024:.1f} KB")
    
    # Перевіряємо вміст архіву
    with zipfile.ZipFile(archive_name, 'r') as zipf:
        file_count = len(zipf.namelist())
        print(f"📁 Файлів в архіві: {file_count}")
        
        print("\n📋 ВМІСТ АРХІВУ:")
        for file_name in sorted(zipf.namelist()):
            file_info = zipf.getinfo(file_name)
            size_kb = file_info.file_size / 1024
            print(f"   {file_name} ({size_kb:.1f} KB)")
    
    print(f"\n🚀 ДЛЯ ВИКОРИСТАННЯ:")
    print(f"1. Завантажте {archive_name} на сервер")
    print(f"2. unzip {archive_name}")
    print(f"3. cd emergency-deploy/")
    print(f"4. ./emergency_deploy.sh (Linux) або emergency_deploy.bat (Windows)")
    print("=" * 60)
    
    return archive_name

if __name__ == "__main__":
    try:
        archive_name = create_emergency_archive()
        print(f"✅ УСПІШНО! Архів створено: {archive_name}")
    except Exception as e:
        print(f"❌ ПОМИЛКА: {e}")
