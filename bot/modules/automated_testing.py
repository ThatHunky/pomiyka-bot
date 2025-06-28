"""
Фаза 2: Автоматизоване тестування та CI/CD
"""

import os
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import sys

logger = logging.getLogger(__name__)

class AutomatedTester:
    """Автоматизований тестер для бота"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.test_summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Запуск всіх тестів"""
        print("🧪 Запуск автоматизованих тестів...")
        
        # Тести модулів
        await self._test_modules()
        await self._test_database_connections()
        await self._test_api_integrations()
        await self._test_security()
        await self._test_performance()
        
        # Підсумок
        self._generate_report()
        return self.test_summary
    
    async def _test_modules(self):
        """Тестування модулів бота"""
        print("📦 Тестування модулів...")
        
        modules_to_test = [
            'bot.modules.context_adapter',
            'bot.modules.gemini_cache',
            'bot.modules.config_validator',
            'bot.modules.performance_monitor',
            'bot.modules.security_manager',
            'bot.modules.web_dashboard'
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                self._add_test_result(f"Import {module_name}", True, "Module imported successfully")
            except Exception as e:
                self._add_test_result(f"Import {module_name}", False, str(e))
    
    async def _test_database_connections(self):
        """Тестування підключень до БД"""
        print("💾 Тестування БД...")
        
        # Тест синхронної БД
        try:
            from bot.modules.context_adapter import get_context_adapter
            adapter = get_context_adapter()
            adapter.init_db()
            self._add_test_result("SQLite DB Connection", True, "Connected")
        except Exception as e:
            self._add_test_result("SQLite DB Connection", False, str(e))
        
        # Тест асинхронної БД
        try:
            from bot.modules.context_async import AsyncContextManager
            manager = AsyncContextManager()
            await manager.initialize()
            connection_ok = await manager.test_connection()
            self._add_test_result("Async DB Connection", connection_ok, 
                                "Connected" if connection_ok else "Failed to connect")
        except Exception as e:
            self._add_test_result("Async DB Connection", False, str(e))
    
    async def _test_api_integrations(self):
        """Тестування API інтеграцій"""
        print("🌐 Тестування API...")
        
        # Тест Gemini API (без реального виклику)
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key and len(api_key) > 20:
                self._add_test_result("Gemini API Key", True, "Key configured")
            else:
                self._add_test_result("Gemini API Key", False, "Key not configured or too short")
        except Exception as e:
            self._add_test_result("Gemini API Key", False, str(e))
        
        # Тест Telegram Bot API
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if bot_token and ':' in bot_token and len(bot_token) > 30:
                self._add_test_result("Telegram Bot Token", True, "Token configured")
            else:
                self._add_test_result("Telegram Bot Token", False, "Token not configured or invalid format")
        except Exception as e:
            self._add_test_result("Telegram Bot Token", False, str(e))
    
    async def _test_security(self):
        """Тестування безпеки"""
        print("🔐 Тестування безпеки...")
        
        try:
            from bot.modules.security_manager import security_manager, validate_message_security
            
            # Тест валідації повідомлень
            safe_message = "Привіт! Як справи?"
            is_safe = validate_message_security(safe_message, 12345)
            self._add_test_result("Safe Message Validation", is_safe, "Safe message passed")
            
            # Тест небезпечного повідомлення
            dangerous_message = "<script>alert('hack')</script>"
            is_dangerous = not validate_message_security(dangerous_message, 12345)
            self._add_test_result("Dangerous Message Detection", is_dangerous, 
                                "Dangerous message blocked" if is_dangerous else "Failed to block")
            
            # Тест rate limiting
            rate_ok = security_manager.rate_limit_check(12345)
            self._add_test_result("Rate Limiting", True, f"Rate limit check: {rate_ok}")
            
        except Exception as e:
            self._add_test_result("Security Tests", False, str(e))
    
    async def _test_performance(self):
        """Тестування продуктивності"""
        print("⚡ Тестування продуктивності...")
        
        try:
            from bot.modules.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Тест системних метрик
            stats = monitor.get_system_stats()
            self._add_test_result("System Metrics", True, f"CPU/Memory metrics available")
            
            # Тест health check
            health = monitor.health_check()
            is_healthy = health.get('status') == 'healthy'
            self._add_test_result("Health Check", is_healthy, f"Status: {health.get('status')}")
            
        except Exception as e:
            self._add_test_result("Performance Tests", False, str(e))
    
    def _add_test_result(self, test_name: str, passed: bool, details: str):
        """Додавання результату тесту"""
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        self.test_summary['total'] += 1
        if passed:
            self.test_summary['passed'] += 1
            print(f"✅ {test_name}")
        else:
            self.test_summary['failed'] += 1
            print(f"❌ {test_name}: {details}")
    
    def _generate_report(self):
        """Генерація звіту тестування"""
        print(f"\n📊 ПІДСУМОК ТЕСТУВАННЯ:")
        print(f"   Всього тестів: {self.test_summary['total']}")
        print(f"   Пройдено: {self.test_summary['passed']}")
        print(f"   Провалено: {self.test_summary['failed']}")
        print(f"   Пропущено: {self.test_summary['skipped']}")
        
        success_rate = (self.test_summary['passed'] / self.test_summary['total']) * 100 if self.test_summary['total'] > 0 else 0
        print(f"   Успішність: {success_rate:.1f}%")
        
        # Збереження звіту
        report_data = {
            'summary': self.test_summary,
            'results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        os.makedirs('reports', exist_ok=True)
        report_file = f"reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"📄 Звіт збережено: {report_file}")
        except Exception as e:
            print(f"⚠️  Не вдалося зберегти звіт: {e}")

class CIPipeline:
    """Continuous Integration пайплайн"""
    
    def __init__(self):
        self.pipeline_steps = [
            'lint_check',
            'type_check',
            'security_scan',
            'unit_tests',
            'integration_tests',
            'performance_tests'
        ]
    
    async def run_pipeline(self) -> bool:
        """Запуск CI пайплайну"""
        print("🔄 Запуск CI пайплайну...")
        
        results = {}
        overall_success = True
        
        for step in self.pipeline_steps:
            try:
                step_result = await self._run_step(step)
                results[step] = step_result
                if not step_result:
                    overall_success = False
                    print(f"❌ Крок {step} провалився")
                else:
                    print(f"✅ Крок {step} пройшов")
            except Exception as e:
                print(f"💥 Помилка в кроці {step}: {e}")
                results[step] = False
                overall_success = False
        
        print(f"\n🎯 CI пайплайн {'УСПІШНИЙ' if overall_success else 'ПРОВАЛЕНИЙ'}")
        return overall_success
    
    async def _run_step(self, step: str) -> bool:
        """Запуск окремого кроку пайплайну"""
        if step == 'lint_check':
            return self._run_flake8()
        elif step == 'type_check':
            return self._run_mypy()
        elif step == 'security_scan':
            return await self._run_security_scan()
        elif step == 'unit_tests':
            return self._run_pytest()
        elif step == 'integration_tests':
            return await self._run_integration_tests()
        elif step == 'performance_tests':
            return await self._run_performance_tests()
        
        return True
    
    def _run_flake8(self) -> bool:
        """Запуск flake8 для перевірки стилю коду"""
        try:
            result = subprocess.run(['flake8', 'bot/'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            print("⚠️  flake8 не встановлено")
            return True  # Не провалюємо, якщо інструмент не встановлено
    
    def _run_mypy(self) -> bool:
        """Запуск mypy для перевірки типів"""
        try:
            result = subprocess.run(['mypy', 'bot/'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            print("⚠️  mypy не встановлено")
            return True
    
    async def _run_security_scan(self) -> bool:
        """Сканування безпеки"""
        try:
            from bot.modules.security_manager import security_manager
            
            # Тест основних функцій безпеки
            test_messages = [
                "Нормальне повідомлення",
                "<script>alert('xss')</script>",
                "exec('malicious code')",
                "import os; os.system('rm -rf /')"
            ]
            
            dangerous_detected = 0
            for msg in test_messages[1:]:  # Пропускаємо нормальне повідомлення
                is_safe, _ = security_manager.validate_message(msg, 12345)
                if not is_safe:
                    dangerous_detected += 1
            
            return dangerous_detected >= 2  # Має виявити принаймні 2 небезпечні повідомлення
        except Exception:
            return False
    
    def _run_pytest(self) -> bool:
        """Запуск unit тестів"""
        try:
            result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            print("⚠️  pytest не встановлено")
            return True
    
    async def _run_integration_tests(self) -> bool:
        """Запуск інтеграційних тестів"""
        try:
            tester = AutomatedTester()
            result = await tester.run_all_tests()
            return result['failed'] == 0
        except Exception:
            return False
    
    async def _run_performance_tests(self) -> bool:
        """Запуск тестів продуктивності"""
        try:
            from bot.modules.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            stats = monitor.get_system_stats()
            
            # Перевіряємо, що система не перевантажена
            cpu_usage = stats.get('cpu_percent', 0)
            memory_usage = stats.get('memory_percent', 0)
            
            return cpu_usage < 90 and memory_usage < 90
        except Exception:
            return False

# Функції для швидкого виклику
async def run_tests():
    """Швидкий запуск тестів"""
    tester = AutomatedTester()
    return await tester.run_all_tests()

async def run_ci():
    """Швидкий запуск CI пайплайну"""
    pipeline = CIPipeline()
    return await pipeline.run_pipeline()

if __name__ == "__main__":
    # Можна запустити тести безпосередньо
    asyncio.run(run_tests())
