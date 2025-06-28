#!/usr/bin/env python3
"""
Тест версії Gemini API для перевірки використання v1beta
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

def test_api_version():
    """Перевіряє, що використовується правильна версія API"""
    from bot.modules.gemini_enhanced import BASE_API_URL, GEMINI_API_VERSION
    
    print(f"Поточна версія API: {GEMINI_API_VERSION}")
    print(f"Базовий URL: {BASE_API_URL}")
    
    # Перевірка, що використовується v1beta за замовчуванням
    assert GEMINI_API_VERSION == "v1beta", f"Очікувалось v1beta, отримано {GEMINI_API_VERSION}"
    assert "v1beta" in BASE_API_URL, f"URL не містить v1beta: {BASE_API_URL}"
    
    print("✅ Версія API правильна - використовується v1beta (найостанніша)")

def test_version_configuration():
    """Тестує можливість зміни версії API через .env"""
    
    # Імітуємо зміну версії через змінну середовища
    original_env = os.environ.copy()
    
    try:
        # Тестуємо v1
        os.environ["GEMINI_API_VERSION"] = "v1"
        
        # Перезавантажуємо модуль
        import importlib
        from bot.modules import gemini_enhanced
        importlib.reload(gemini_enhanced)
        
        assert gemini_enhanced.GEMINI_API_VERSION == "v1"
        assert "v1" in gemini_enhanced.BASE_API_URL
        print("✅ Конфігурація версії v1 працює")
        
        # Тестуємо v1alpha
        os.environ["GEMINI_API_VERSION"] = "v1alpha"
        importlib.reload(gemini_enhanced)
        
        assert gemini_enhanced.GEMINI_API_VERSION == "v1alpha"
        assert "v1alpha" in gemini_enhanced.BASE_API_URL
        print("✅ Конфігурація версії v1alpha працює")
        
    finally:
        # Відновлюємо оригінальне середовище
        os.environ.clear()
        os.environ.update(original_env)
        
        # Перезавантажуємо з оригінальними налаштуваннями
        import importlib
        from bot.modules import gemini_enhanced
        importlib.reload(gemini_enhanced)

def main():
    """Запуск тестів версії API"""
    print("🧪 Тестування версії Gemini API...")
    
    try:
        test_api_version()
        test_version_configuration()
        print("\n🎉 Всі тести версії API пройшли успішно!")
        print("📋 Підсумок:")
        print("   • За замовчуванням використовується v1beta (найостанніша версія)")
        print("   • Можливість конфігурації через GEMINI_API_VERSION в .env")
        print("   • Підтримка v1, v1beta, v1alpha")
        
    except Exception as e:
        print(f"❌ Помилка тестування: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
