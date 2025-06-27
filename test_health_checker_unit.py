from bot.modules import health_checker
import time

def test_health_status():
    hc = health_checker.HealthChecker()
    hc.record_api_call(success=True)
    hc.record_api_call(success=False)
    hc.record_message()
    status = hc.get_health_status()
    assert status["status"] in ("healthy", "warning")
    assert status["messages_processed"] == 1
    assert status["api_errors"] == 1
    assert isinstance(status["uptime_hours"], float)
    assert "memory_usage" in status
    assert "uptime_formatted" in status
    assert status["last_api_call"] is not None
    # Перевірка форматування часу
    assert "г" in status["uptime_formatted"]
