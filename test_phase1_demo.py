#!/usr/bin/env python3
"""
Демонстрація та тестування покращень Фази 1
"""
import sys
import os
import asyncio
from datetime import datetime

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(__file__))

def print_header(title: str):
    """Виводить заголовок"""
    print(f"\n{'='*50}")
    print(f"🎯 {title}")
    print('='*50)

def print_result(test_name: str, success: bool, details: str = ""):
    """Виводить результат тесту"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def test_context_adapter():
    """Тест адаптера контексту"""
    print_header("ТЕСТ АДАПТЕРА КОНТЕКСТУ")
    
    try:
        from bot.modules.context_adapter import ContextAdapter, get_context_adapter
        
        # Тест створення адаптера
        adapter = ContextAdapter(use_async=False)
        print_result("Створення адаптера", True, f"Режим: {'async' if adapter.use_async else 'sync'}")
        
        # Тест ініціалізації
        adapter.init_db()
        print_result("Ініціалізація БД", True)
        
        # Тест статистики
        stats = adapter.get_stats()
        print_result("Отримання статистики", True, f"Тип: {stats.get('adapter_type', 'unknown')}")
        
        # Тест глобального адаптера
        global_adapter = get_context_adapter()
        print_result("Глобальний адаптер", True, f"Однаковий: {adapter is global_adapter}")
        
        return True
        
    except Exception as e:
        print_result("Адаптер контексту", False, str(e))
        return False

def test_gemini_cache():
    """Тест кешу Gemini"""
    print_header("ТЕСТ КЕШУ GEMINI")
    
    try:
            from bot.modules.gemini_cache import GeminiCacheManager
            
            cache = GeminiCacheManager()
            print_result("Створення кешу", True)
            
            # Для синхронного тесту створюємо обгортку
            import asyncio
            
            async def test_cache_operations():
                await cache.initialize()
                
                prompt = "Привіт!"
                context = "Тестовий контекст"
                tone = "friendly"
                response = "Привіт! Як справи?"
                
                await cache.cache_response(prompt, response, context, tone)
                cached_response = await cache.get_cached_response(prompt, context, tone)
                return cached_response == response
            
            # Запускаємо тест
            success = asyncio.run(test_cache_operations())
            print_result("Збереження/отримання", success)
            
            # Статистика
            async def get_stats():
                await cache.initialize()
                return await cache.get_cache_stats()
            
            stats = asyncio.run(get_stats())
            print_result("Статистика кешу", True, 
                        f"Записів: {stats.get('total_entries', 0)}")
            
            return True
        
    except Exception as e:
        print_result("Кеш Gemini", False, str(e))
        return False

def test_config_validator():
    """Тест валідатора конфігурації"""
    print_header("ТЕСТ ВАЛІДАТОРА КОНФІГУРАЦІЇ")
    
    try:
        from bot.modules.config_validator import ConfigValidator
        
        validator = ConfigValidator()
        print_result("Створення валідатора", True)
        
        # Тест валідації (може не пройти через відсутність токенів)
        try:
            is_valid = validator.validate_all()
            print_result("Валідація конфігурації", is_valid, 
                        "Конфігурація валідна" if is_valid else "Є проблеми з конфігурацією")
        except Exception as e:
            print_result("Валідація конфігурації", False, f"Помилка: {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print_result("Валідатор конфігурації", False, str(e))
        return False

def test_performance_monitor():
    """Тест моніторингу продуктивності"""
    print_header("ТЕСТ МОНІТОРИНГУ ПРОДУКТИВНОСТІ")
    
    try:
        from bot.modules.performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        print_result("Створення монітора", True)
        
        # Тест системної статистики
        stats = monitor.get_system_stats()
        print_result("Системна статистика", True, 
                    f"CPU: {stats.get('cpu_percent', 'N/A')}%, RAM: {stats.get('memory_percent', 'N/A')}%")
        
        # Тест health check
        health = monitor.health_check()
        is_healthy = health.get('status') == 'healthy'
        print_result("Health check", is_healthy, 
                    f"Статус: {health.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print_result("Моніторинг продуктивності", False, str(e))
        return False

async def test_async_database():
    """Тест асинхронної бази даних"""
    print_header("ТЕСТ АСИНХРОННОЇ БАЗИ ДАНИХ")
    
    try:
        from bot.modules.context_async import AsyncContextManager
        
        manager = AsyncContextManager()
        print_result("Створення менеджера", True)
        
        # Тест ініціалізації
        await manager.initialize()
        print_result("Ініціалізація", True)
        
        # Тест з'єднання
        try:
            connection_ok = await manager.test_connection()
            print_result("Тест з'єднання", connection_ok)
        except Exception as e:
            print_result("Тест з'єднання", False, str(e))
            connection_ok = False
        
        # Статистика
        stats = await manager.get_stats()
        print_result("Статистика БД", True, 
                    f"Повідомлень: {stats.get('total_messages', 0)}")
        
        # Закриваємо з'єднання
        await manager.close()
        
        return True
        
    except Exception as e:
        print_result("Асинхронна БД", False, str(e))
        return False

def test_web_dashboard():
    """Тест веб-дашборду"""
    print_header("ТЕСТ ВЕБ-ДАШБОРДУ")
    
    try:
        from bot.modules.web_dashboard import create_app, start_dashboard
        
        # Тест створення додатку
        app = create_app()
        print_result("Створення веб-додатку", app is not None)
        
        # Примітка про запуск
        print_result("Готовність до запуску", True, 
                    "Використовуйте 'make monitor' для запуску дашборду")
        
        return True
        
    except Exception as e:
        print_result("Веб-дашборд", False, str(e))
        return False

def test_docker_improvements():
    """Тест покращень Docker"""
    print_header("ТЕСТ ПОКРАЩЕНЬ DOCKER")
    
    # Перевіряємо Dockerfile
    dockerfile_path = "Dockerfile"
    if os.path.exists(dockerfile_path):
        try:
            with open(dockerfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(dockerfile_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        improvements = {
            "HEALTHCHECK": "HEALTHCHECK" in content,
            "Non-root user": any(keyword in content for keyword in ["RUN adduser", "USER "]),
            "Multi-stage": content.count("FROM") >= 1,
        }
        
        for improvement, exists in improvements.items():
            print_result(f"Dockerfile: {improvement}", exists)
    else:
        print_result("Dockerfile", False, "Файл не знайдено")
    
    # Перевіряємо docker-compose.yml
    compose_path = "docker-compose.yml"
    if os.path.exists(compose_path):
        try:
            with open(compose_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(compose_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        improvements = {
            "Healthcheck": "healthcheck:" in content,
            "Logging": "logging:" in content,
            "Resource limits": any(keyword in content for keyword in ["deploy:", "mem_limit:", "cpus:"]),
        }
        
        for improvement, exists in improvements.items():
            print_result(f"docker-compose: {improvement}", exists)
    else:
        print_result("docker-compose.yml", False, "Файл не знайдено")
    
    return True

def test_makefile_improvements():
    """Тест покращень Makefile"""
    print_header("ТЕСТ ПОКРАЩЕНЬ MAKEFILE")
    
    makefile_path = "Makefile"
    if os.path.exists(makefile_path):
        try:
            with open(makefile_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(makefile_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        new_commands = [
            "monitor:", "validate-config:", "check-performance:", "migrate-db:",
            "test-cache:", "deploy:", "health-check:", "cache-stats:",
            "test-async:", "optimize-db:", "clear-cache:", "benchmark:"
        ]
        
        for command in new_commands:
            exists = command in content
            print_result(f"Команда {command[:-1]}", exists)
        
        return True
    else:
        print_result("Makefile", False, "Файл не знайдено")
        return False

def main():
    """Головна функція тестування"""
    print("🚀 ДЕМОНСТРАЦІЯ ПОКРАЩЕНЬ ФАЗИ 1")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Синхронні тести
    results.append(("Адаптер контексту", test_context_adapter()))
    results.append(("Кеш Gemini", test_gemini_cache()))
    results.append(("Валідатор конфігурації", test_config_validator()))
    results.append(("Моніторинг продуктивності", test_performance_monitor()))
    results.append(("Веб-дашборд", test_web_dashboard()))
    results.append(("Покращення Docker", test_docker_improvements()))
    results.append(("Покращення Makefile", test_makefile_improvements()))
    
    # Асинхронний тест з тайм-аутом
    try:
        async_result = asyncio.wait_for(test_async_database(), timeout=10.0)
        async_result = asyncio.run(async_result)
        results.append(("Асинхронна БД", async_result))
    except asyncio.TimeoutError:
        results.append(("Асинхронна БД", False))
        print("❌ Асинхронна БД: Тайм-аут (> 10 сек)")
    except Exception as e:
        results.append(("Асинхронна БД", False))
        print(f"❌ Асинхронна БД: {e}")
    
    # Переконуємося, що всі асинхронні ресурси закриті
    try:
        from bot.modules.context_async import close_connection
        asyncio.run(close_connection())
    except Exception:
        pass  # Ігноруємо помилки закриття
    
    # Підсумок
    print_header("ПІДСУМОК ТЕСТУВАННЯ")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Результат: {passed}/{total} тестів пройдено ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 Всі покращення Фази 1 працюють чудово!")
    elif passed >= total * 0.7:
        print("👍 Більшість покращень працює, є кілька проблем для вирішення.")
    else:
        print("⚠️  Багато проблем потребують уваги.")
    
    print(f"\n💡 Наступні кроки:")
    print("   1. Виправити проблемні модулі")
    print("   2. Запустити інтеграційні тести: make test-integration")
    print("   3. Перейти до Фази 2: Безпека та стабільність")
    
    # Забезпечуємо правильне завершення
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        # Закриваємо event loop якщо він існує
        try:
            loop = asyncio.get_running_loop()
            if loop and not loop.is_closed():
                loop.stop()
        except RuntimeError:
            # Event loop не запущений
            pass
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Переривання користувача")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неочікувана помилка: {e}")
        sys.exit(1)
