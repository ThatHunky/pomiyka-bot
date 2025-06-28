#!/usr/bin/env python3
"""
Тест для перевірки нового дружелюбного тону бота
"""
import sys
import os

# Додаємо шлях до модулів бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

def test_tone_instructions():
    """Тестує нові інструкції тону"""
    print("=== Тестування нових інструкцій тону ===")
    
    try:
        from bot.modules.enhanced_behavior import get_tone_instruction, analyze_conversation_context
        
        # Тестові повідомлення
        test_messages = [
            ("Привіт, як справи?", "побутове"),
            ("Допоможи з кодом", "технічне"), 
            ("Ха-ха, смішно!", "веселе"),
            ("Мені сумно...", "емоційне"),
            ("Що таке життя?", "філософське")
        ]
        
        for message, expected_type in test_messages:
            analysis = analyze_conversation_context(message)
            tone_instruction = get_tone_instruction(analysis)
            
            print(f"\nПовідомлення: '{message}'")
            print(f"Тип розмови: {analysis['type']} (очікувалось: {expected_type})")
            print(f"Настрій: {analysis['mood']}")
            print(f"Тон відповіді: {analysis['response_tone']}")
            print(f"Інструкція: {tone_instruction}")
            
            # Перевіряємо чи інструкція містить слова про нормальність
            if "нормальн" in tone_instruction.lower() or "зрозумі" in tone_instruction.lower() or "адекватн" in tone_instruction.lower():
                print("✅ Інструкція містить вказівки на нормальність")
            else:
                print("⚠️  Інструкція може не містити достатньо вказівок на нормальність")
                
    except ImportError as e:
        print(f"❌ Помилка імпорту: {e}")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    print("\n=== Тест Gemini промпту ===")
    
    try:
        from bot.modules.gemini import _build_persona_prompt
        
        # Тестуємо базовий промпт
        base_prompt = _build_persona_prompt("В чаті звичайна активність.")
        print(f"Базовий промпт:\n{base_prompt}")
        
        if "нормальні, зрозумілі слова" in base_prompt:
            print("✅ Базовий промпт містить інструкції про нормальність")
        else:
            print("⚠️  Базовий промпт може не містити достатньо інструкцій")
            
        # Тестуємо з тон-інструкцією
        tone_prompt = _build_persona_prompt("В чаті звичайна активність.", "Будь дружелюбним та корисним.")
        print(f"\nПромпт з тоном:\n{tone_prompt}")
        
    except ImportError as e:
        print(f"❌ Помилка імпорту Gemini модуля: {e}")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    print("\n=== Тест завершено ===")

if __name__ == "__main__":
    test_tone_instructions()
