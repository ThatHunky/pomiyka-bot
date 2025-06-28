#!/usr/bin/env python3
"""
Тест локального аналізатора для перевірки працездатності на i5-6500
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Додаємо шлях до модулів бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

async def test_local_analyzer():
    """Тестує локальний аналізатор"""
    print("🔧 Тестування локального аналізатора...")
    
    try:
        from bot.modules.local_analyzer import LocalAnalyzer, get_analyzer, analyze_text_local
        print("✅ Модуль локального аналізатора імпортовано")
        
        # Перевіряємо доступність залежностей
        try:
            from sentence_transformers import SentenceTransformer
            print("✅ sentence-transformers доступна")
            transformers_available = True
        except ImportError:
            print("❌ sentence-transformers не встановлена")
            transformers_available = False
        
        try:
            import spacy
            print("✅ spaCy доступна")
            spacy_available = True
        except ImportError:
            print("❌ spaCy не встановлена")
            spacy_available = False
        
        # Створюємо тестову директорію
        test_data_dir = "test_data"
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Ініціалізуємо аналізатор
        analyzer = LocalAnalyzer(db_path=os.path.join(test_data_dir, "test_analysis.db"))
        print("✅ Аналізатор ініціалізовано")
        
        # Тестові повідомлення
        test_messages = [
            "Привіт! Як справи? 😊",
            "Цей код на Python не працює, помоги розібратися",
            "Дуже сумно що так сталося 😢",
            "ОГО! Це неймовірно круто! 🔥",
            "Що будемо на обід готувати?",
            "Дурня, ти нічого не розумієш! 😡",
            "Думаю, це питання філософське...",
            "git push origin main не працює",
            "Дивлюся новий фільм Marvel, супер!",
            "Погода сьогодні чудова, сонячно ☀️"
        ]
        
        print("\n📊 Тестування аналізу повідомлень...")
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. Повідомлення: '{message}'")
            
            start_time = datetime.now()
            analysis = await analyzer.analyze_message(message)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            print(f"   🎭 Емоція: {analysis['emotion']} (впевненість: {analysis['confidence']:.2f})")
            print(f"   📝 Тема: {analysis['topic']}")
            print(f"   🔑 Ключові слова: {', '.join(analysis['keywords'])}")
            print(f"   ⚡ Метод: {analysis['analysis_method']}")
            print(f"   ⏱️  Час: {processing_time:.1f}мс")
        
        # Тестуємо контекстний аналіз
        print("\n📈 Тестування контекстного аналізу...")
        
        chat_history = [
            {"text": msg, "user": f"user_{i%3}", "timestamp": datetime.now().timestamp()}
            for i, msg in enumerate(test_messages)
        ]
        
        context_analysis = await analyzer.analyze_conversation_batch(chat_history, chat_id=123)
        
        print(f"📋 Підсумок розмови: {context_analysis['summary']}")
        print(f"🎭 Домінуюча емоція: {context_analysis['dominant_emotion']}")
        print(f"📚 Основні теми: {', '.join(context_analysis['main_topics'])}")
        print(f"📊 Кількість повідомлень: {context_analysis['message_count']}")
        
        # Тестуємо кеш
        print("\n💾 Тестування кешування...")
        
        start_time = datetime.now()
        cached_analysis = await analyzer.analyze_message(test_messages[0])  # Той же текст
        end_time = datetime.now()
        
        cache_time = (end_time - start_time).total_seconds() * 1000
        print(f"⚡ Час з кешу: {cache_time:.1f}мс")
        print(f"✅ Метод: {cached_analysis['analysis_method']}")
        
        # Тестуємо інтеграцію з situation_predictor
        print("\n🔗 Тестування інтеграції з situation_predictor...")
        
        try:
            from bot.modules.situation_predictor import (
                analyze_message_context_enhanced, 
                generate_enhanced_context_prompt,
                is_local_analyzer_available
            )
            
            print(f"✅ Локальний аналізатор доступний: {is_local_analyzer_available()}")
            
            enhanced_analysis = await analyze_message_context_enhanced(
                "Гряг, поясни як працює React useEffect хук",
                chat_history,
                chat_id=123
            )
            
            print(f"🎯 Тип розмови: {enhanced_analysis['type']}")
            print(f"🎭 Настрій: {enhanced_analysis['mood']}")
            print(f"📈 Рівень залученості: {enhanced_analysis['engagement_level']}/10")
            print(f"💬 Чи втручатися боту: {enhanced_analysis['should_intervene']}")
            print(f"🎨 Рекомендований тон: {enhanced_analysis['suggested_tone']}")
            
            # Тестуємо генерацію промпту
            prompt = await generate_enhanced_context_prompt(
                "Гряг, як справи?",
                123,
                chat_history
            )
            
            print(f"\n📝 Згенерований промпт:")
            print(f"'{prompt[:200]}...' (показано перші 200 символів)")
            
        except Exception as e:
            print(f"❌ Помилка інтеграції: {e}")
        
        # Статистика продуктивності
        print("\n📊 Статистика продуктивності:")
        print(f"🧠 Модель завантажена: {analyzer.model is not None}")
        print(f"📚 NLP завантажена: {analyzer.nlp is not None}")
        print(f"💾 Розмір кешу: {len(analyzer.analysis_cache)}")
        print(f"⚙️  Розмір пакету: {analyzer.batch_size}")
        
        # Рекомендації для i5-6500
        print("\n💡 Рекомендації для i5-6500:")
        
        if not transformers_available:
            print("📦 Встановіть: pip install sentence-transformers")
            print("🚀 Це значно покращить якість аналізу")
        
        if not spacy_available:
            print("📦 Встановіть: pip install spacy")
            print("📦 Потім: python -m spacy download uk_core_news_sm")
            print("🔍 Це покращить обробку української мови")
        
        print("⚡ При використанні встановіть BOT_ANALYSIS_BATCH_SIZE=5")
        print("💾 При обмеженій RAM встановіть BOT_ANALYSIS_CACHE_HOURS=12")
        print("🧹 Періодично запускайте очищення кешу")
        
        print("\n✅ Тест завершено успішно!")
        
        return True
        
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance():
    """Тест продуктивності на великому обсязі даних"""
    print("\n🚀 Тест продуктивності...")
    
    try:
        from bot.modules.local_analyzer import get_analyzer
        
        analyzer = get_analyzer()
        
        # Створюємо багато тестових повідомлень
        large_dataset = [
            "Привіт! Як справи?",
            "Цей Python код не працює",
            "Дуже сумно",
            "Неймовірно круто!",
            "Що на обід?",
        ] * 20  # 100 повідомлень
        
        print(f"📊 Обробка {len(large_dataset)} повідомлень...")
        
        start_time = datetime.now()
        
        for i, message in enumerate(large_dataset):
            await analyzer.analyze_message(message)
            if (i + 1) % 20 == 0:
                print(f"✅ Оброблено {i + 1}/{len(large_dataset)}")
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️  Загальний час: {total_time:.2f} секунд")
        print(f"⚡ Швидкість: {len(large_dataset)/total_time:.1f} повідомлень/сек")
        print(f"💾 Використання кешу: {len(analyzer.analysis_cache)} записів")
        
        # Оцінка для i5-6500
        if total_time > 60:
            print("⚠️  Швидкість низька для i5-6500")
            print("💡 Спробуйте зменшити BOT_ANALYSIS_BATCH_SIZE до 3")
        elif total_time < 30:
            print("🚀 Швидкість чудова для i5-6500!")
        else:
            print("✅ Швидкість нормальна для i5-6500")
        
    except Exception as e:
        print(f"❌ Помилка тесту продуктивності: {e}")

if __name__ == "__main__":
    print("🤖 Тест локального аналізатора для Гряг-бота")
    print("💻 Оптимізовано для Intel i5-6500, 16GB RAM")
    print("=" * 50)
    
    # Основний тест
    success = asyncio.run(test_local_analyzer())
    
    if success:
        # Тест продуктивності
        asyncio.run(test_performance())
        
        print("\n🎉 Всі тести пройдені!")
        print("\n📋 Щоб увімкнути локальний аналізатор:")
        print("1. Встановіть залежності: pip install sentence-transformers spacy")
        print("2. Встановіть BOT_LOCAL_ANALYSIS_ENABLED=true в .env")
        print("3. Перезапустіть бота")
    else:
        print("\n❌ Тести не пройдені. Перевірте налаштування.")
        sys.exit(1)
