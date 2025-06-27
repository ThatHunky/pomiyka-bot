# Health Checker модуль для моніторингу стану бота
import time
import os
import logging
from datetime import datetime
from typing import Dict, Any

class HealthChecker:
    def __init__(self):
        self.start_time = time.time()
        self.last_api_call = None
        self.api_errors = 0
        self.message_count = 0
        
    def record_api_call(self, success: bool = True):
        """Записує виклик API"""
        self.last_api_call = time.time()
        if not success:
            self.api_errors += 1
    
    def record_message(self):
        """Записує обробку повідомлення"""
        self.message_count += 1
    
    def get_uptime(self) -> float:
        """Повертає час роботи в секундах"""
        return time.time() - self.start_time
    
    def get_health_status(self) -> Dict[str, Any]:
        """Повертає статус здоров'я бота"""
        uptime_seconds = self.get_uptime()
        uptime_hours = uptime_seconds / 3600
        
        return {
            "status": "healthy" if self.api_errors < 10 else "warning",
            "uptime_hours": round(uptime_hours, 2),
            "uptime_formatted": self.format_uptime(uptime_seconds),
            "messages_processed": self.message_count,
            "api_errors": self.api_errors,
            "last_api_call": self.last_api_call,
            "memory_usage": self.get_memory_usage()
        }
    
    def format_uptime(self, seconds: float) -> str:
        """Форматує час роботи"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}г {minutes}хв"
    
    def get_memory_usage(self) -> str:
        """Повертає використання пам'яті (приблизно)"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            return f"{memory_mb:.1f} MB"
        except ImportError:
            return "N/A (psutil not installed)"
        except Exception:
            return "N/A"

# Глобальний instance
health_checker = HealthChecker()
