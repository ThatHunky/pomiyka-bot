#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')

def test_realistic_scenarios():
    """Тестування реалістичних сценаріїв з українських чатів"""
    print("🇺🇦 Тестування реалістичних українських сценаріїв...")
    
    try:
        from bot.modules.enhanced_behavior import (
            analyze_conversation_context, 
            create_context_aware_prompt
        )
        
        # Реалістичні сценарії з українських чатів
        scenarios = [
            {
                "message": "Гряг, що ти думаєш про нові технології AI?",
                "expected_type": "технічне",
                "expected_engagement": "high"
            },
            {
                "message": "Блять, знову сервер упав! Хто відповідає за бекенд?",
                "expected_type": "технічне", 
                "expected_engagement": "medium"
            },
            {
                "message": "А що таке справжня дружба? Чи існує вона взагалі?",
                "expected_type": "філософське",
                "expected_engagement": "medium"
            },
            {
                "message": "Хахаха, це найкращий мем року! 😂😂😂",
                "expected_type": "веселе",
                "expected_engagement": "low"
            },
            {
                "message": "Гряг, ти дурак чи прикидаєшся?",
                "expected_type": "конфлікт",
                "expected_engagement": "high"
            },
            {
                "message": "Сьогодні так сумно... не хочеться нічого робити 😢",
                "expected_type": "емоційне",
                "expected_engagement": "low"
            },
            {
                "message": "Бот Гряг, розкажи про квантову фізику та паралельні всесвіти",
                "expected_type": "філософське",
                "expected_engagement": "high"
            },
            {
                "message": "У мене проблема з React hooks, вони не оновлюються",
                "expected_type": "технічне",
                "expected_engagement": "medium"
            }
        ]
        
        print(f"📊 Тестування {len(scenarios)} сценаріїв:")
        print("=" * 70)
        
        for i, scenario in enumerate(scenarios, 1):
            message = scenario["message"]
            analysis = analyze_conversation_context(message)
            
            print(f"\n{i}. '{message}'")
            print(f"   🎯 Тип: {analysis['type']} (очікувався: {scenario['expected_type']})")
            print(f"   😊 Настрій: {analysis['mood']}")
            print(f"   ⚡ Залученість: {analysis['engagement']}/10 ({scenario['expected_engagement']})")
            print(f"   💬 Відповісти: {analysis['should_respond']}")
            print(f"   🎨 Тон: {analysis['response_tone']}")
            
            # Перевіряємо точність
            type_correct = analysis['type'] == scenario['expected_type']
            engagement_levels = {"low": (1, 4), "medium": (5, 7), "high": (8, 10)}
            expected_range = engagement_levels[scenario['expected_engagement']]
            engagement_correct = expected_range[0] <= analysis['engagement'] <= expected_range[1]
            
            status = "✅" if type_correct and engagement_correct else "⚠️" 
            if not type_correct:
                status += f" (тип: очікувався {scenario['expected_type']})"
            if not engagement_correct:
                status += f" (залученість: очікувалась {scenario['expected_engagement']})"
            
            print(f"   {status}")
            
            # Показуємо промт для високої залученості
            if analysis['engagement'] >= 8:
                prompt = create_context_aware_prompt(message, analysis)
                print(f"   📝 Промт: {prompt[:150]}...")
        
        print("\n🎉 Тестування завершено!")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_realistic_scenarios()
