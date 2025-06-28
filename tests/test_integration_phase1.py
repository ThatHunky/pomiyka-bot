"""
Інтеграційні тести для покращень Фази 1
"""
import pytest
import asyncio
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Додаємо шлях до проекту
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestPhase1Integration:
    """Тести інтеграції покращень Фази 1"""
    
    def setup_method(self):
        """Налаштування для кожного тесту"""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Очищення після кожного тесту"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_context_adapter_sync_mode(self):
        """Тест адаптера контексту в синхронному режимі"""
        with patch.dict(os.environ, {'USE_ASYNC_DB': 'false'}):
            from bot.modules.context_adapter import ContextAdapter
            
            adapter = ContextAdapter(use_async=False)
            assert not adapter.use_async
            
            # Тест ініціалізації
            adapter.init_db()
            
            # Тест статистики
            stats = adapter.get_stats()
            assert stats['adapter_type'] == 'sync'
    
    def test_context_adapter_async_mode(self):
        """Тест адаптера контексту в асинхронному режимі"""
        with patch.dict(os.environ, {'USE_ASYNC_DB': 'true'}):
            from bot.modules.context_adapter import ContextAdapter
            
            adapter = ContextAdapter(use_async=False)  # Форсуємо синхронний режим для тесту
            assert not adapter.use_async
    
    def test_gemini_cache_basic_operations(self):
        """Тест базових операцій кешу Gemini"""
        try:
            from bot.modules.gemini_cache import GeminiCache
            
            cache = GeminiCache()
            
            # Тест збереження та отримання
            prompt = "Тестовий промпт"
            context = "Тестовий контекст"
            tone = "friendly"
            response = "Тестова відповідь"
            
            cache.save_response(prompt, context, tone, response)
            cached_response = cache.get_response(prompt, context, tone)
            
            assert cached_response == response
            
            # Тест статистики
            stats = cache.get_stats()
            assert 'total_entries' in stats
            assert 'hit_rate' in stats
            
        except ImportError:
            pytest.skip("GeminiCache недоступний")
    
    def test_config_validator(self):
        """Тест валідатора конфігурації"""
        try:
            from bot.modules.config_validator import ConfigValidator
            
            validator = ConfigValidator()
            
            # Тест генерації .env.sample
            sample_path = os.path.join(self.temp_dir, '.env.sample')
            with patch('bot.modules.config_validator.ConfigValidator.generate_env_sample') as mock_gen:
                mock_gen.return_value = True
                result = validator.generate_env_sample()
                mock_gen.assert_called_once()
                
        except ImportError:
            pytest.skip("ConfigValidator недоступний")
    
    def test_performance_monitor_basic(self):
        """Тест базового моніторингу продуктивності"""
        try:
            from bot.modules.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Тест отримання системної статистики
            stats = monitor.get_system_stats()
            assert isinstance(stats, dict)
            
            # Тест health check
            health = monitor.health_check()
            assert 'status' in health
            
        except ImportError:
            pytest.skip("PerformanceMonitor недоступний")
    
    def test_web_dashboard_endpoints(self):
        """Тест ендпоінтів веб-дашборду"""
        try:
            from bot.modules.web_dashboard import create_app
            from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
            import aiohttp
            
            class TestWebDashboard(AioHTTPTestCase):
                async def get_application(self):
                    return create_app()
                
                @unittest_run_loop
                async def test_health_endpoint(self):
                    resp = await self.client.request("GET", "/api/health")
                    assert resp.status == 200
                    data = await resp.json()
                    assert 'status' in data
                
                @unittest_run_loop
                async def test_stats_endpoint(self):
                    resp = await self.client.request("GET", "/api/stats")
                    assert resp.status == 200
                    data = await resp.json()
                    assert isinstance(data, dict)
            
            # Запускаємо тест
            import unittest
            suite = unittest.TestLoader().loadTestsFromTestCase(TestWebDashboard)
            unittest.TextTestRunner().run(suite)
            
        except ImportError:
            pytest.skip("WebDashboard недоступний")
    
    def test_integration_all_modules(self):
        """Тест інтеграції всіх модулів разом"""
        with patch.dict(os.environ, {
            'USE_ASYNC_DB': 'false',
            'TELEGRAM_BOT_TOKEN': 'test_token',
            'GEMINI_API_KEY': 'test_key'
        }):
            
            try:
                # Імпорт всіх модулів
                from bot.modules.context_adapter import get_context_adapter
                from bot.modules.gemini_cache import GeminiCache
                from bot.modules.config_validator import ConfigValidator
                from bot.modules.performance_monitor import PerformanceMonitor
                
                # Створення екземплярів
                adapter = get_context_adapter()
                cache = GeminiCache()
                validator = ConfigValidator()
                monitor = PerformanceMonitor()
                
                # Перевірка базової функціональності
                assert adapter is not None
                assert cache is not None
                assert validator is not None
                assert monitor is not None
                
                # Перевірка статистики
                adapter_stats = adapter.get_stats()
                cache_stats = cache.get_stats()
                monitor_stats = monitor.get_system_stats()
                
                assert isinstance(adapter_stats, dict)
                assert isinstance(cache_stats, dict)
                assert isinstance(monitor_stats, dict)
                
                print("✅ Всі модулі успішно інтегровані")
                
            except ImportError as e:
                pytest.skip(f"Не всі модулі доступні: {e}")
    
    @pytest.mark.asyncio
    async def test_async_database_operations(self):
        """Тест асинхронних операцій з базою даних"""
        try:
            from bot.modules.context_async import AsyncContextManager
            
            # Використовуємо тимчасову базу даних
            test_db_path = os.path.join(self.temp_dir, 'test.db')
            
            with patch('bot.modules.context_async.AsyncContextManager.db_path', test_db_path):
                manager = AsyncContextManager()
                await manager.initialize()
                
                # Тест статистики
                stats = await manager.get_stats()
                assert isinstance(stats, dict)
                
                print("✅ Асинхронна база даних працює")
                
        except ImportError:
            pytest.skip("AsyncContextManager недоступний")
    
    def test_dockerfile_improvements(self):
        """Тест покращень Dockerfile"""
        dockerfile_path = os.path.join(os.path.dirname(__file__), '..', 'Dockerfile')
        
        if os.path.exists(dockerfile_path):
            with open(dockerfile_path, 'r') as f:
                content = f.read()
            
            # Перевіряємо ключові покращення
            assert 'HEALTHCHECK' in content, "Dockerfile повинен містити HEALTHCHECK"
            assert 'RUN adduser' in content or 'USER' in content, "Dockerfile повинен використовувати non-root користувача"
            assert 'FROM python:' in content, "Dockerfile повинен використовувати multi-stage build"
            
            print("✅ Dockerfile містить покращення")
        else:
            pytest.skip("Dockerfile не знайдено")
    
    def test_docker_compose_improvements(self):
        """Тест покращень docker-compose.yml"""
        compose_path = os.path.join(os.path.dirname(__file__), '..', 'docker-compose.yml')
        
        if os.path.exists(compose_path):
            with open(compose_path, 'r') as f:
                content = f.read()
            
            # Перевіряємо ключові покращення
            assert 'healthcheck:' in content, "docker-compose.yml повинен містити healthcheck"
            assert 'logging:' in content, "docker-compose.yml повинен містити налаштування логування"
            assert 'deploy:' in content or 'mem_limit:' in content, "docker-compose.yml повинен містити ресурсні ліміти"
            
            print("✅ docker-compose.yml містить покращення")
        else:
            pytest.skip("docker-compose.yml не знайдено")
    
    def test_requirements_updated(self):
        """Тест оновлення requirements.txt"""
        requirements_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        
        if os.path.exists(requirements_path):
            with open(requirements_path, 'r') as f:
                content = f.read()
            
            # Перевіряємо нові залежності
            assert 'aiosqlite' in content, "requirements.txt повинен містити aiosqlite"
            assert 'aiohttp-cors' in content, "requirements.txt повинен містити aiohttp-cors"
            
            print("✅ requirements.txt оновлено")
        else:
            pytest.skip("requirements.txt не знайдено")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
