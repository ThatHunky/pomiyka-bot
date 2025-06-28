# Простий веб-дашборд для моніторингу бота
from aiohttp import web, web_request
import aiohttp_cors
import json
import logging
from datetime import datetime
from typing import Dict, Any
import os

from bot.modules.performance_monitor import get_health_status
from bot.modules.gemini_cache import get_cache_stats
from bot.modules.context_async import get_chat_stats
from bot.bot_config import PERSONA

logger = logging.getLogger(__name__)

class WebDashboard:
    """Веб-дашборд для моніторингу бота"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()
        self._setup_cors()
    
    def _setup_routes(self):
        """Налаштування маршрутів"""
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/status', self.status_handler)
        self.app.router.add_get('/metrics', self.metrics_handler)
        self.app.router.add_get('/cache', self.cache_handler)
        self.app.router.add_get('/config', self.config_handler)
        self.app.router.add_get('/', self.dashboard_handler)
        
        # API endpoints
        self.app.router.add_get('/api/health', self.api_health)
        self.app.router.add_get('/api/metrics', self.api_metrics)
        self.app.router.add_get('/api/cache', self.api_cache)
        
    def _setup_cors(self):
        """Налаштування CORS"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def health_handler(self, request: web_request.Request) -> web.Response:
        """Simple health check"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": "running"
        })
    
    async def status_handler(self, request: web_request.Request) -> web.Response:
        """Детальний статус бота"""
        try:
            health_status = get_health_status()
            return web.json_response(health_status)
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return web.json_response({
                "error": "Failed to get status",
                "message": str(e)
            }, status=500)
    
    async def metrics_handler(self, request: web_request.Request) -> web.Response:
        """Метрики в Prometheus форматі"""
        try:
            health_status = get_health_status()
            metrics_text = self._format_prometheus_metrics(health_status)
            return web.Response(text=metrics_text, content_type='text/plain')
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return web.Response(text="# Error generating metrics", status=500)
    
    async def cache_handler(self, request: web_request.Request) -> web.Response:
        """Статистика кешу"""
        try:
            cache_stats = await get_cache_stats()
            return web.json_response(cache_stats)
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return web.json_response({
                "error": "Failed to get cache stats",
                "message": str(e)
            }, status=500)
    
    async def config_handler(self, request: web_request.Request) -> web.Response:
        """Поточна конфігурація (без секретів)"""
        safe_config = {
            "persona_name": PERSONA.get("name"),
            "context_limit": PERSONA.get("context_limit"),
            "max_replies_per_hour": PERSONA.get("max_replies_per_hour"),
            "autonomous_mode": PERSONA.get("autonomous_mode"),
            "spam_threshold": PERSONA.get("spam_threshold"),
            "cache_enabled": os.getenv("GEMINI_ENABLE_CACHE", "true"),
            "async_db": os.getenv("USE_ASYNC_DB", "false"),
            "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        }
        return web.json_response(safe_config)
    
    async def dashboard_handler(self, request: web_request.Request) -> web.Response:
        """HTML дашборд"""
        html = self._generate_dashboard_html()
        return web.Response(text=html, content_type='text/html')
    
    # API endpoints
    async def api_health(self, request: web_request.Request) -> web.Response:
        """API: Health check"""
        return await self.health_handler(request)
    
    async def api_metrics(self, request: web_request.Request) -> web.Response:
        """API: Metrics"""
        return await self.status_handler(request)
    
    async def api_cache(self, request: web_request.Request) -> web.Response:
        """API: Cache stats"""
        return await self.cache_handler(request)
    
    def _format_prometheus_metrics(self, health_status: Dict[str, Any]) -> str:
        """Форматує метрики для Prometheus"""
        lines = [
            "# HELP gryag_bot_uptime_seconds Bot uptime in seconds",
            "# TYPE gryag_bot_uptime_seconds counter",
            f"gryag_bot_uptime_seconds {health_status.get('uptime_hours', 0) * 3600}",
            "",
            "# HELP gryag_bot_memory_usage_percent Memory usage percentage",
            "# TYPE gryag_bot_memory_usage_percent gauge",
            f"gryag_bot_memory_usage_percent {health_status.get('system_metrics', {}).get('process', {}).get('memory_percent', 0)}",
            "",
            "# HELP gryag_bot_cpu_usage_percent CPU usage percentage",
            "# TYPE gryag_bot_cpu_usage_percent gauge",
            f"gryag_bot_cpu_usage_percent {health_status.get('system_metrics', {}).get('process', {}).get('cpu_percent', 0)}",
            "",
            "# HELP gryag_bot_messages_processed_total Total messages processed",
            "# TYPE gryag_bot_messages_processed_total counter",
            f"gryag_bot_messages_processed_total {health_status.get('performance_stats', {}).get('messages_processed', 0)}",
            "",
            "# HELP gryag_bot_cache_hit_rate Cache hit rate percentage",
            "# TYPE gryag_bot_cache_hit_rate gauge",
            f"gryag_bot_cache_hit_rate {health_status.get('performance_stats', {}).get('cache_hit_rate', 0)}",
        ]
        return "\n".join(lines)
    
    def _generate_dashboard_html(self) -> str:
        """Генерує HTML для дашборду"""
        return '''
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Гряг-бот - Дашборд</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; }
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .refresh-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Гряг-бот - Дашборд моніторингу</h1>
            <button class="refresh-btn" onclick="loadData()">🔄 Оновити</button>
            <p>Останнє оновлення: <span id="lastUpdate">-</span></p>
        </div>
        
        <div class="card">
            <h2>📊 Загальний статус</h2>
            <div id="status">Завантаження...</div>
        </div>
        
        <div class="card">
            <h2>📈 Основні метрики</h2>
            <div class="metrics-grid" id="metrics">
                Завантаження метрик...
            </div>
        </div>
        
        <div class="card">
            <h2>💾 Кеш статистика</h2>
            <div id="cache">Завантаження...</div>
        </div>
        
        <div class="card">
            <h2>⚙️ Конфігурація</h2>
            <div id="config">Завантаження...</div>
        </div>
    </div>

    <script>
        async function loadData() {
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString('uk-UA');
            
            try {
                // Загальний статус
                const statusResponse = await fetch('/api/health');
                const statusData = await statusResponse.json();
                const statusClass = statusData.status === 'healthy' ? 'status-healthy' : 
                                  statusData.status === 'warning' ? 'status-warning' : 'status-critical';
                document.getElementById('status').innerHTML = 
                    `<h3 class="${statusClass}">Статус: ${statusData.status}</h3>`;
                
                // Метрики
                const metricsResponse = await fetch('/api/metrics');
                const metricsData = await metricsResponse.json();
                
                const metricsHtml = `
                    <div class="metric">
                        <div>Час роботи</div>
                        <div class="metric-value">${(metricsData.uptime_hours || 0).toFixed(1)}h</div>
                    </div>
                    <div class="metric">
                        <div>Повідомлень оброблено</div>
                        <div class="metric-value">${metricsData.performance_stats?.messages_processed || 0}</div>
                    </div>
                    <div class="metric">
                        <div>Cache Hit Rate</div>
                        <div class="metric-value">${(metricsData.performance_stats?.cache_hit_rate || 0).toFixed(1)}%</div>
                    </div>
                    <div class="metric">
                        <div>Пам'ять</div>
                        <div class="metric-value">${(metricsData.system_metrics?.process?.memory_percent || 0).toFixed(1)}%</div>
                    </div>
                `;
                document.getElementById('metrics').innerHTML = metricsHtml;
                
                // Кеш
                const cacheResponse = await fetch('/api/cache');
                const cacheData = await cacheResponse.json();
                document.getElementById('cache').innerHTML = `<pre>${JSON.stringify(cacheData, null, 2)}</pre>`;
                
                // Конфігурація
                const configResponse = await fetch('/config');
                const configData = await configResponse.json();
                document.getElementById('config').innerHTML = `<pre>${JSON.stringify(configData, null, 2)}</pre>`;
                
            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('status').innerHTML = '<p class="status-critical">Помилка завантаження даних</p>';
            }
        }
        
        // Автоматичне оновлення кожні 30 секунд
        setInterval(loadData, 30000);
        
        // Завантажуємо дані при завантаженні сторінки
        loadData();
    </script>
</body>
</html>
        '''
    
    async def start(self):
        """Запускає веб-сервер"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Веб-дашборд запущено на http://{self.host}:{self.port}")
        return runner

# Глобальний екземпляр дашборду
dashboard = WebDashboard()

async def start_web_dashboard():
    """Запускає веб-дашборд"""
    return await dashboard.start()

def create_app():
    """Створює додаток aiohttp для веб-дашборду"""
    dashboard_instance = WebDashboard()
    return dashboard_instance.app

def start_dashboard():
    """Синхронна функція для запуску дашборду"""
    print("🌐 Веб-дашборд готовий до запуску")
    print("   Використовуйте: python -m bot.modules.web_dashboard")
    print("   Або: make monitor")
    return True

if __name__ == "__main__":
    import asyncio
    
    async def main():
        await start_web_dashboard()
        print("Дашборд запущено на http://localhost:8080")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Зупинка дашборду...")
    
    asyncio.run(main())
