# Розширений модуль моніторингу та аналітики
import asyncio
import logging
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Моніторинг продуктивності бота в реальному часі"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics: Dict[str, Any] = {
            'api_calls': defaultdict(int),
            'api_response_times': defaultdict(list),
            'errors': defaultdict(int),
            'messages_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'db_queries': 0,
            'spontaneous_messages': 0,
        }
        
        # Буфери для метрик часу
        self.response_time_buffer: deque = deque(maxlen=1000)
        self.memory_usage_buffer: deque = deque(maxlen=100)
        self.cpu_usage_buffer: deque = deque(maxlen=100)
        
        # Лічильники по часу
        self.hourly_stats = defaultdict(lambda: defaultdict(int))
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        
    def record_api_call(self, api_name: str, response_time: float, success: bool = True):
        """Записує виклик API з часом відповіді"""
        self.metrics['api_calls'][api_name] += 1
        self.metrics['api_response_times'][api_name].append(response_time)
        self.response_time_buffer.append(response_time)
        
        if not success:
            self.metrics['errors'][api_name] += 1
        
        # Статистика по годинах
        hour = datetime.now().strftime('%Y-%m-%d_%H')
        self.hourly_stats[hour][f'{api_name}_calls'] += 1
        if not success:
            self.hourly_stats[hour][f'{api_name}_errors'] += 1
    
    def record_message_processed(self, chat_id: int, processing_time: float):
        """Записує обробку повідомлення"""
        self.metrics['messages_processed'] += 1
        
        hour = datetime.now().strftime('%Y-%m-%d_%H')
        self.hourly_stats[hour]['messages_processed'] += 1
        
    def record_cache_event(self, hit: bool):
        """Записує подію кешу"""
        if hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
    
    def record_db_query(self, query_time: float):
        """Записує запит до БД"""
        self.metrics['db_queries'] += 1
        
    def record_spontaneous_message(self):
        """Записує спонтанне повідомлення"""
        self.metrics['spontaneous_messages'] += 1
        
        hour = datetime.now().strftime('%Y-%m-%d_%H')
        self.hourly_stats[hour]['spontaneous_messages'] += 1
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Отримує метрики системи"""
        process = psutil.Process()
        
        # Використання пам'яті
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Використання CPU
        cpu_percent = process.cpu_percent()
        
        # Системні метрики
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent(interval=1)
        
        # Записуємо в буфери
        self.memory_usage_buffer.append(memory_percent)
        self.cpu_usage_buffer.append(cpu_percent)
        
        return {
            'process': {
                'memory_mb': round(memory_info.rss / 1024 / 1024, 2),
                'memory_percent': round(memory_percent, 2),
                'cpu_percent': round(cpu_percent, 2),
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
            },
            'system': {
                'memory_percent': system_memory.percent,
                'memory_available_gb': round(system_memory.available / 1024**3, 2),
                'cpu_percent': system_cpu,
                'cpu_count': psutil.cpu_count(),
            }
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Отримує статистику продуктивності"""
        uptime = time.time() - self.start_time
        
        # API статистика
        api_stats = {}
        for api_name, times in self.metrics['api_response_times'].items():
            if times:
                api_stats[api_name] = {
                    'calls': self.metrics['api_calls'][api_name],
                    'errors': self.metrics['errors'][api_name],
                    'avg_response_time': round(sum(times) / len(times), 3),
                    'min_response_time': round(min(times), 3),
                    'max_response_time': round(max(times), 3),
                    'success_rate': round((1 - self.metrics['errors'][api_name] / self.metrics['api_calls'][api_name]) * 100, 2)
                }
        
        # Кеш статистика
        total_cache_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = (self.metrics['cache_hits'] / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        # Загальна статистика
        messages_per_hour = (self.metrics['messages_processed'] / uptime * 3600) if uptime > 0 else 0
        
        return {
            'uptime_seconds': round(uptime, 2),
            'uptime_hours': round(uptime / 3600, 2),
            'messages_processed': self.metrics['messages_processed'],
            'messages_per_hour': round(messages_per_hour, 2),
            'cache_hit_rate': round(cache_hit_rate, 2),
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'db_queries': self.metrics['db_queries'],
            'spontaneous_messages': self.metrics['spontaneous_messages'],
            'api_stats': api_stats,
        }
    
    def get_recent_trends(self) -> Dict[str, Any]:
        """Отримує тренди за останній час"""
        return {
            'avg_response_time_recent': round(sum(list(self.response_time_buffer)[-10:]) / min(10, len(self.response_time_buffer)), 3) if self.response_time_buffer else 0,
            'avg_memory_usage': round(sum(self.memory_usage_buffer) / len(self.memory_usage_buffer), 2) if self.memory_usage_buffer else 0,
            'avg_cpu_usage': round(sum(self.cpu_usage_buffer) / len(self.cpu_usage_buffer), 2) if self.cpu_usage_buffer else 0,
        }
    
    def get_hourly_report(self, hours_back: int = 24) -> Dict[str, Any]:
        """Генерує погодинний звіт"""
        report = {}
        current_time = datetime.now()
        
        for i in range(hours_back):
            hour_key = (current_time - timedelta(hours=i)).strftime('%Y-%m-%d_%H')
            if hour_key in self.hourly_stats:
                report[hour_key] = dict(self.hourly_stats[hour_key])
            else:
                report[hour_key] = {}
        
        return report
    
    def export_metrics(self, filepath: str = None) -> bool:
        """Експортує метрики у JSON файл"""
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"data/metrics_export_{timestamp}.json"
        
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'performance_stats': self.get_performance_stats(),
                'system_metrics': self.get_system_metrics(),
                'recent_trends': self.get_recent_trends(),
                'hourly_report': self.get_hourly_report(24),
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Метрики експортовано до {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Помилка експорту метрик: {e}")
            return False
    
    # Псевдоніми для зворотної сумісності
    def get_system_stats(self) -> Dict[str, Any]:
        """Псевдонім для get_system_metrics"""
        return self.get_system_metrics()
    
    def health_check(self) -> Dict[str, Any]:
        """Перевірка здоров'я системи"""
        return get_health_status()
    
    def start_monitoring(self):
        """Запуск моніторингу (логування)"""
        logger.info("Моніторинг ініціалізовано")
    
    def stop_monitoring(self):
        """Зупинка моніторингу (логування)"""
        logger.info("Моніторинг зупинено")

class AlertManager:
    """Менеджер алертів для критичних подій"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.thresholds = {
            'high_memory_usage': 80.0,  # %
            'high_cpu_usage': 90.0,     # %
            'slow_api_response': 5.0,   # seconds
            'high_error_rate': 10.0,    # %
            'low_cache_hit_rate': 50.0, # %
        }
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 хвилин між алертами
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Перевіряє умови для алертів"""
        alerts = []
        current_time = time.time()
        
        # Перевірка використання пам'яті
        system_metrics = self.monitor.get_system_metrics()
        memory_usage = system_metrics['process']['memory_percent']
        
        if memory_usage > self.thresholds['high_memory_usage']:
            alert_key = 'high_memory_usage'
            if self._should_send_alert(alert_key, current_time):
                alerts.append({
                    'type': 'warning',
                    'message': f'Високе використання пам\'яті: {memory_usage:.1f}%',
                    'metric': 'memory_usage',
                    'value': memory_usage,
                    'threshold': self.thresholds['high_memory_usage']
                })
        
        # Перевірка CPU
        cpu_usage = system_metrics['process']['cpu_percent']
        if cpu_usage > self.thresholds['high_cpu_usage']:
            alert_key = 'high_cpu_usage'
            if self._should_send_alert(alert_key, current_time):
                alerts.append({
                    'type': 'critical',
                    'message': f'Високе використання CPU: {cpu_usage:.1f}%',
                    'metric': 'cpu_usage',
                    'value': cpu_usage,
                    'threshold': self.thresholds['high_cpu_usage']
                })
        
        # Перевірка швидкості API
        trends = self.monitor.get_recent_trends()
        avg_response_time = trends['avg_response_time_recent']
        if avg_response_time > self.thresholds['slow_api_response']:
            alert_key = 'slow_api_response'
            if self._should_send_alert(alert_key, current_time):
                alerts.append({
                    'type': 'warning',
                    'message': f'Повільні API відповіді: {avg_response_time:.1f}s',
                    'metric': 'api_response_time',
                    'value': avg_response_time,
                    'threshold': self.thresholds['slow_api_response']
                })
        
        # Перевірка cache hit rate
        perf_stats = self.monitor.get_performance_stats()
        cache_hit_rate = perf_stats['cache_hit_rate']
        if cache_hit_rate < self.thresholds['low_cache_hit_rate'] and perf_stats['cache_hits'] + perf_stats['cache_misses'] > 10:
            alert_key = 'low_cache_hit_rate'
            if self._should_send_alert(alert_key, current_time):
                alerts.append({
                    'type': 'info',
                    'message': f'Низький cache hit rate: {cache_hit_rate:.1f}%',
                    'metric': 'cache_hit_rate',
                    'value': cache_hit_rate,
                    'threshold': self.thresholds['low_cache_hit_rate']
                })
        
        return alerts
    
    def _should_send_alert(self, alert_key: str, current_time: float) -> bool:
        """Перевіряє чи потрібно надсилати алерт (cooldown)"""
        last_alert_time = self.last_alerts.get(alert_key, 0)
        if current_time - last_alert_time > self.alert_cooldown:
            self.last_alerts[alert_key] = current_time
            return True
        return False

# Глобальний екземпляр монітора
performance_monitor = PerformanceMonitor()
alert_manager = AlertManager(performance_monitor)

# Функції для легкого використання
def record_api_call(api_name: str, response_time: float, success: bool = True):
    """Записує виклик API"""
    performance_monitor.record_api_call(api_name, response_time, success)

def record_message_processed(chat_id: int, processing_time: float):
    """Записує обробку повідомлення"""
    performance_monitor.record_message_processed(chat_id, processing_time)

def record_cache_hit():
    """Записує попадання в кеш"""
    performance_monitor.record_cache_event(True)

def record_cache_miss():
    """Записує промах кешу"""
    performance_monitor.record_cache_event(False)

def get_health_status() -> Dict[str, Any]:
    """Отримує статус здоров'я бота"""
    system_metrics = performance_monitor.get_system_metrics()
    performance_stats = performance_monitor.get_performance_stats()
    alerts = alert_manager.check_alerts()
    
    # Визначаємо загальний статус
    if any(alert['type'] == 'critical' for alert in alerts):
        overall_status = 'critical'
    elif any(alert['type'] == 'warning' for alert in alerts):
        overall_status = 'warning'
    else:
        overall_status = 'healthy'
    
    return {
        'status': overall_status,
        'uptime_hours': performance_stats['uptime_hours'],
        'system_metrics': system_metrics,
        'performance_stats': performance_stats,
        'alerts': alerts,
        'timestamp': datetime.now().isoformat()
    }

async def start_monitoring_task():
    """Запускає фонове завдання моніторингу"""
    logger.info("Запуск моніторингу продуктивності")
    
    while True:
        try:
            # Перевіряємо алерти кожні 60 секунд
            alerts = alert_manager.check_alerts()
            
            for alert in alerts:
                logger.warning(f"ALERT [{alert['type'].upper()}]: {alert['message']}")
            
            # Експортуємо метрики кожну годину
            if datetime.now().minute == 0:
                performance_monitor.export_metrics()
            
            await asyncio.sleep(60)  # Перевірка кожну хвилину
            
        except Exception as e:
            logger.error(f"Помилка в моніторингу: {e}")
            await asyncio.sleep(60)
