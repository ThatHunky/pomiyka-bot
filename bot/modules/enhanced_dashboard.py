"""
Фаза 3: Покращений веб-дашборд з інтерактивними елементами
"""

from aiohttp import web, web_request
import aiohttp_cors
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class EnhancedWebDashboard:
    """Покращений веб-дашборд з інтерактивними функціями"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.websockets = set()  # Для real-time оновлень
        self._setup_routes()
        self._setup_cors()
        self._setup_static()
    
    def _setup_routes(self):
        """Налаштування маршрутів"""
        # API endpoints
        self.app.router.add_get('/api/dashboard/stats', self.api_dashboard_stats)
        self.app.router.add_get('/api/chats/list', self.api_chats_list)
        self.app.router.add_get('/api/chats/{chat_id}/messages', self.api_chat_messages)
        self.app.router.add_get('/api/users/stats', self.api_users_stats)
        self.app.router.add_get('/api/analytics/trends', self.api_analytics_trends)
        self.app.router.add_post('/api/bot/command', self.api_bot_command)
        
        # WebSocket для real-time
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # Dashboard UI
        self.app.router.add_get('/', self.dashboard_page)
        self.app.router.add_get('/chats', self.chats_page)
        self.app.router.add_get('/analytics', self.analytics_page)
        self.app.router.add_get('/settings', self.settings_page)
    
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
        
        # Додаємо CORS до всіх маршрутів
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    def _setup_static(self):
        """Налаштування статичних файлів"""
        static_dir = Path(__file__).parent.parent.parent / "static"
        static_dir.mkdir(exist_ok=True)
        self.app.router.add_static('/static/', path=static_dir, name='static')
    
    async def api_dashboard_stats(self, request: web_request.BaseRequest) -> web.Response:
        """Статистика для головного дашборду"""
        try:
            from bot.modules.context_async import get_database_stats, get_chat_stats
            from bot.modules.performance_monitor import get_health_status
            from bot.modules.gemini_cache import get_cache_stats
            
            # Збираємо статистику
            db_stats = await get_database_stats()
            chat_stats = await get_chat_stats()
            health = get_health_status()
            cache_stats = get_cache_stats()
            
            stats = {
                'timestamp': datetime.now().isoformat(),
                'database': db_stats,
                'chats': chat_stats,
                'health': health,
                'cache': cache_stats,
                'system': {
                    'uptime': str(datetime.now() - datetime.fromtimestamp(0)),
                    'status': 'healthy' if health.get('status') == 'healthy' else 'warning'
                }
            }
            
            return web.json_response(stats)
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_chats_list(self, request: web_request.BaseRequest) -> web.Response:
        """Список активних чатів"""
        try:
            from bot.modules.context_async import get_connection
            
            conn = await get_connection()
            
            # Отримуємо список чатів з статистикою
            async with conn.execute('''
                SELECT 
                    chat_id,
                    COUNT(*) as message_count,
                    COUNT(DISTINCT user_id) as user_count,
                    MAX(timestamp) as last_activity,
                    MIN(timestamp) as first_activity
                FROM messages 
                WHERE timestamp > ?
                GROUP BY chat_id
                ORDER BY last_activity DESC
                LIMIT 50
            ''', (datetime.now() - timedelta(days=30),)) as cursor:
                rows = await cursor.fetchall()
            
            chats = []
            for row in rows:
                chats.append({
                    'chat_id': row[0],
                    'message_count': row[1],
                    'user_count': row[2],
                    'last_activity': row[3],
                    'first_activity': row[4],
                    'activity_score': row[1] * row[2]  # Простий скор активності
                })
            
            return web.json_response({'chats': chats})
            
        except Exception as e:
            logger.error(f"Error getting chats list: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_chat_messages(self, request: web_request.BaseRequest) -> web.Response:
        """Повідомлення з конкретного чату"""
        try:
            chat_id = int(request.match_info['chat_id'])
            limit = int(request.query.get('limit', 100))
            offset = int(request.query.get('offset', 0))
            
            from bot.modules.context_async import get_connection
            
            conn = await get_connection()
            
            # Отримуємо повідомлення
            async with conn.execute('''
                SELECT 
                    user_id, username, full_name, message_text, 
                    timestamp, message_type, media_description
                FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (chat_id, limit, offset)) as cursor:
                rows = await cursor.fetchall()
            
            messages = []
            for row in rows:
                messages.append({
                    'user_id': row[0],
                    'username': row[1],
                    'full_name': row[2],
                    'message_text': row[3],
                    'timestamp': row[4],
                    'message_type': row[5],
                    'media_description': row[6]
                })
            
            return web.json_response({
                'chat_id': chat_id,
                'messages': list(reversed(messages)),  # Хронологічний порядок
                'count': len(messages)
            })
            
        except Exception as e:
            logger.error(f"Error getting chat messages: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_users_stats(self, request: web_request.BaseRequest) -> web.Response:
        """Статистика користувачів"""
        try:
            from bot.modules.context_async import get_connection
            
            conn = await get_connection()
            
            # Топ користувачів по активності
            async with conn.execute('''
                SELECT 
                    user_id, username, full_name,
                    COUNT(*) as message_count,
                    COUNT(DISTINCT chat_id) as chat_count,
                    MAX(timestamp) as last_activity
                FROM messages 
                WHERE timestamp > ?
                GROUP BY user_id
                ORDER BY message_count DESC
                LIMIT 20
            ''', (datetime.now() - timedelta(days=7),)) as cursor:
                rows = await cursor.fetchall()
            
            users = []
            for row in rows:
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'full_name': row[2],
                    'message_count': row[3],
                    'chat_count': row[4],
                    'last_activity': row[5]
                })
            
            return web.json_response({'top_users': users})
            
        except Exception as e:
            logger.error(f"Error getting users stats: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_analytics_trends(self, request: web_request.BaseRequest) -> web.Response:
        """Аналітика трендів"""
        try:
            days = int(request.query.get('days', 7))
            
            from bot.modules.context_async import get_connection
            
            conn = await get_connection()
            
            # Активність по днях
            async with conn.execute('''
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as message_count,
                    COUNT(DISTINCT user_id) as user_count,
                    COUNT(DISTINCT chat_id) as chat_count
                FROM messages 
                WHERE timestamp > ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT ?
            ''', (datetime.now() - timedelta(days=days), days)) as cursor:
                daily_stats = await cursor.fetchall()
            
            # Активність по годинах
            async with conn.execute('''
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as message_count
                FROM messages 
                WHERE timestamp > ?
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            ''', (datetime.now() - timedelta(days=1),)) as cursor:
                hourly_stats = await cursor.fetchall()
            
            trends = {
                'daily_activity': [
                    {
                        'date': row[0],
                        'messages': row[1],
                        'users': row[2],
                        'chats': row[3]
                    }
                    for row in daily_stats
                ],
                'hourly_activity': [
                    {
                        'hour': int(row[0]),
                        'messages': row[1]
                    }
                    for row in hourly_stats
                ]
            }
            
            return web.json_response(trends)
            
        except Exception as e:
            logger.error(f"Error getting analytics trends: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_bot_command(self, request: web_request.BaseRequest) -> web.Response:
        """Виконання команд бота через API"""
        try:
            data = await request.json()
            command = data.get('command')
            
            if not command:
                return web.json_response({'error': 'Command is required'}, status=400)
            
            # Тут можна додати виконання команд
            # Наразі просто логуємо
            logger.info(f"Bot command received: {command}")
            
            return web.json_response({
                'success': True,
                'command': command,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error executing bot command: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def websocket_handler(self, request: web_request.BaseRequest) -> web.WebSocketResponse:
        """WebSocket для real-time оновлень"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        logger.info("WebSocket connection established")
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    # Обробка WebSocket повідомлень
                    await self._handle_websocket_message(ws, data)
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websockets.discard(ws)
            logger.info("WebSocket connection closed")
        
        return ws
    
    async def _handle_websocket_message(self, ws: web.WebSocketResponse, data: Dict[str, Any]):
        """Обробка WebSocket повідомлень"""
        message_type = data.get('type')
        
        if message_type == 'ping':
            await ws.send_str(json.dumps({'type': 'pong', 'timestamp': datetime.now().isoformat()}))
        elif message_type == 'subscribe':
            # Підписка на оновлення
            await ws.send_str(json.dumps({'type': 'subscribed', 'status': 'success'}))
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Відправка оновлень всім підключеним WebSocket"""
        if not self.websockets:
            return
        
        message = json.dumps({
            'type': 'update',
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Відправляємо всім активним підключенням
        disconnected = set()
        for ws in self.websockets:
            try:
                await ws.send_str(message)
            except ConnectionResetError:
                disconnected.add(ws)
        
        # Видаляємо відключені
        self.websockets -= disconnected
    
    # HTML сторінки
    async def dashboard_page(self, request: web_request.BaseRequest) -> web.Response:
        """Головна сторінка дашборду"""
        html = self._get_dashboard_html()
        return web.Response(text=html, content_type='text/html')
    
    async def chats_page(self, request: web_request.BaseRequest) -> web.Response:
        """Сторінка чатів"""
        html = self._get_chats_html()
        return web.Response(text=html, content_type='text/html')
    
    async def analytics_page(self, request: web_request.BaseRequest) -> web.Response:
        """Сторінка аналітики"""
        html = self._get_analytics_html()
        return web.Response(text=html, content_type='text/html')
    
    async def settings_page(self, request: web_request.BaseRequest) -> web.Response:
        """Сторінка налаштувань"""
        html = self._get_settings_html()
        return web.Response(text=html, content_type='text/html')
    
    def _get_dashboard_html(self) -> str:
        """HTML для головного дашборду"""
        return """
        <!DOCTYPE html>
        <html lang="uk">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Гряг-бот Дашборд</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header { text-align: center; color: #333; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
                .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 20px; color: #667eea; text-decoration: none; }
                .status-healthy { color: #28a745; }
                .status-warning { color: #ffc107; }
                .loading { text-align: center; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="header">🤖 Гряг-бот Дашборд</h1>
                
                <nav class="nav">
                    <a href="/">Дашборд</a>
                    <a href="/chats">Чати</a>
                    <a href="/analytics">Аналітика</a>
                    <a href="/settings">Налаштування</a>
                </nav>
                
                <div id="stats" class="loading">Завантаження статистики...</div>
            </div>
            
            <script>
                async function loadStats() {
                    try {
                        const response = await fetch('/api/dashboard/stats');
                        const data = await response.json();
                        
                        const statsHtml = `
                            <div class="stats-grid">
                                <div class="stat-card">
                                    <h3>📊 База даних</h3>
                                    <p>Повідомлень: ${data.database.total_messages || 0}</p>
                                    <p>Чатів: ${data.database.unique_chats || 0}</p>
                                    <p>Користувачів: ${data.database.unique_users || 0}</p>
                                </div>
                                <div class="stat-card">
                                    <h3>🚀 Система</h3>
                                    <p>Статус: <span class="status-${data.system.status}">${data.system.status}</span></p>
                                    <p>CPU: ${data.health.cpu_percent || 'N/A'}%</p>
                                    <p>RAM: ${data.health.memory_percent || 'N/A'}%</p>
                                </div>
                                <div class="stat-card">
                                    <h3>💾 Кеш</h3>
                                    <p>Записів: ${data.cache.total_entries || 0}</p>
                                    <p>Попадань: ${data.cache.hits || 0}</p>
                                    <p>Промахів: ${data.cache.misses || 0}</p>
                                </div>
                                <div class="stat-card">
                                    <h3>💬 Активні чати</h3>
                                    <p>Всього: ${data.chats.active_chats || 0}</p>
                                    <p>Оновлено: ${new Date(data.timestamp).toLocaleString('uk-UA')}</p>
                                </div>
                            </div>
                        `;
                        
                        document.getElementById('stats').innerHTML = statsHtml;
                    } catch (error) {
                        document.getElementById('stats').innerHTML = `<div class="card">❌ Помилка завантаження: ${error.message}</div>`;
                    }
                }
                
                // Завантажуємо статистику при завантаженні сторінки
                loadStats();
                
                // Оновлюємо кожні 30 секунд
                setInterval(loadStats, 30000);
            </script>
        </body>
        </html>
        """
    
    def _get_chats_html(self) -> str:
        """HTML для сторінки чатів"""
        return """
        <!DOCTYPE html>
        <html lang="uk">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Чати - Гряг-бот</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 20px; color: #667eea; text-decoration: none; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; }
                tr:hover { background-color: #f5f5f5; }
                .loading { text-align: center; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💬 Активні чати</h1>
                
                <nav class="nav">
                    <a href="/">Дашборд</a>
                    <a href="/chats">Чати</a>
                    <a href="/analytics">Аналітика</a>
                    <a href="/settings">Налаштування</a>
                </nav>
                
                <div class="card">
                    <div id="chats" class="loading">Завантаження чатів...</div>
                </div>
            </div>
            
            <script>
                async function loadChats() {
                    try {
                        const response = await fetch('/api/chats/list');
                        const data = await response.json();
                        
                        if (data.chats && data.chats.length > 0) {
                            const chatsHtml = `
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Chat ID</th>
                                            <th>Повідомлень</th>
                                            <th>Користувачів</th>
                                            <th>Остання активність</th>
                                            <th>Активність</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.chats.map(chat => `
                                            <tr>
                                                <td>${chat.chat_id}</td>
                                                <td>${chat.message_count}</td>
                                                <td>${chat.user_count}</td>
                                                <td>${new Date(chat.last_activity).toLocaleString('uk-UA')}</td>
                                                <td>${chat.activity_score}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            `;
                            
                            document.getElementById('chats').innerHTML = chatsHtml;
                        } else {
                            document.getElementById('chats').innerHTML = '<p>Немає активних чатів</p>';
                        }
                    } catch (error) {
                        document.getElementById('chats').innerHTML = `<p>❌ Помилка завантаження: ${error.message}</p>`;
                    }
                }
                
                loadChats();
            </script>
        </body>
        </html>
        """
    
    def _get_analytics_html(self) -> str:
        """HTML для сторінки аналітики"""
        return """
        <!DOCTYPE html>
        <html lang="uk">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Аналітика - Гряг-бот</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 20px; color: #667eea; text-decoration: none; }
                .loading { text-align: center; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📈 Аналітика</h1>
                
                <nav class="nav">
                    <a href="/">Дашборд</a>
                    <a href="/chats">Чати</a>
                    <a href="/analytics">Аналітика</a>
                    <a href="/settings">Налаштування</a>
                </nav>
                
                <div class="card">
                    <h3>Щоденна активність</h3>
                    <div id="daily-analytics" class="loading">Завантаження...</div>
                </div>
                
                <div class="card">
                    <h3>Погодинна активність</h3>
                    <div id="hourly-analytics" class="loading">Завантаження...</div>
                </div>
            </div>
            
            <script>
                async function loadAnalytics() {
                    try {
                        const response = await fetch('/api/analytics/trends?days=7');
                        const data = await response.json();
                        
                        // Щоденна активність
                        if (data.daily_activity) {
                            const dailyHtml = data.daily_activity.map(day => `
                                <p>${day.date}: ${day.messages} повідомлень, ${day.users} користувачів</p>
                            `).join('');
                            document.getElementById('daily-analytics').innerHTML = dailyHtml;
                        }
                        
                        // Погодинна активність
                        if (data.hourly_activity) {
                            const hourlyHtml = data.hourly_activity.map(hour => `
                                <p>${hour.hour}:00 - ${hour.messages} повідомлень</p>
                            `).join('');
                            document.getElementById('hourly-analytics').innerHTML = hourlyHtml;
                        }
                        
                    } catch (error) {
                        document.getElementById('daily-analytics').innerHTML = `❌ Помилка: ${error.message}`;
                        document.getElementById('hourly-analytics').innerHTML = `❌ Помилка: ${error.message}`;
                    }
                }
                
                loadAnalytics();
            </script>
        </body>
        </html>
        """
    
    def _get_settings_html(self) -> str:
        """HTML для сторінки налаштувань"""
        return """
        <!DOCTYPE html>
        <html lang="uk">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Налаштування - Гряг-бот</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 20px; color: #667eea; text-decoration: none; }
                .form-group { margin-bottom: 15px; }
                .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
                .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .btn:hover { background: #5a67d8; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚙️ Налаштування</h1>
                
                <nav class="nav">
                    <a href="/">Дашборд</a>
                    <a href="/chats">Чати</a>
                    <a href="/analytics">Аналітика</a>
                    <a href="/settings">Налаштування</a>
                </nav>
                
                <div class="card">
                    <h3>Налаштування бота</h3>
                    <form id="settings-form">
                        <div class="form-group">
                            <label>Шанс на відповідь (%)</label>
                            <input type="number" id="reply-chance" value="5" min="0" max="100">
                        </div>
                        <div class="form-group">
                            <label>Максимум відповідей на годину</label>
                            <input type="number" id="max-replies" value="2" min="1" max="10">
                        </div>
                        <div class="form-group">
                            <label>Мінімальна пауза (хвилини)</label>
                            <input type="number" id="min-pause" value="20" min="5" max="120">
                        </div>
                        <button type="submit" class="btn">Зберегти</button>
                    </form>
                </div>
                
                <div class="card">
                    <h3>Команди бота</h3>
                    <div>
                        <button class="btn" onclick="executeCommand('/stats')">Отримати статистику</button>
                        <button class="btn" onclick="executeCommand('/backup')">Створити backup</button>
                        <button class="btn" onclick="executeCommand('/health')">Перевірити здоров'я</button>
                    </div>
                </div>
            </div>
            
            <script>
                async function executeCommand(command) {
                    try {
                        const response = await fetch('/api/bot/command', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ command })
                        });
                        
                        const result = await response.json();
                        alert(`Команда виконана: ${result.command}`);
                    } catch (error) {
                        alert(`Помилка: ${error.message}`);
                    }
                }
                
                document.getElementById('settings-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    alert('Налаштування збережено (функція в розробці)');
                });
            </script>
        </body>
        </html>
        """
    
    async def start(self):
        """Запуск сервера"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Enhanced Web Dashboard started on http://{self.host}:{self.port}")
        return runner

# Глобальний екземпляр
enhanced_dashboard = EnhancedWebDashboard()

async def start_enhanced_dashboard():
    """Запуск покращеного дашборду"""
    return await enhanced_dashboard.start()

def create_enhanced_app():
    """Створення застосунку для зовнішнього використання"""
    return enhanced_dashboard.app
