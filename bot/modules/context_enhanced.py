# Модуль для покращеного формування контексту
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sqlite3
from bot.bot_config import DB_PATH, PERSONA
from .context_sqlite import get_recent_messages, add_message_to_context

def analyze_text_sentiment(text: str):
    """Простий аналіз настрою тексту як fallback"""
    positive_words = ["добре", "чудово", "класно", "супер", "відмінно"]
    negative_words = ["погано", "жахливо", "сумно", "дратує", "бісить"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return {"sentiment": "позитивний", "score": 0.7}
    elif negative_count > positive_count:
        return {"sentiment": "негативний", "score": 0.3}
    else:
        return {"sentiment": "нейтральний", "score": 0.5}

def build_enhanced_context(chat_id: int, recent_messages: List[Dict[str, Any]]) -> str:
    """
    Покращена логіка формування контексту з багаторівневою агрегацією
    """
    if not recent_messages:
        return ""
    
    # 1. Фільтрування повідомлень
    filtered_messages = filter_relevant_messages(recent_messages)
    
    # 2. Оцінка важливості повідомлень
    scored_messages = score_messages(filtered_messages)
    
    # 3. Отримання summary по годинах
    hourly_summaries = get_hourly_summaries(chat_id)
    
    # 4. Аналіз настрою та теми
    mood_summary = analyze_chat_mood_and_topic(filtered_messages)
    
    # 5. Збирання контексту
    context_parts = []
    
    if mood_summary:
        context_parts.append(f"Настрій чату: {mood_summary}")
    
    if hourly_summaries:
        context_parts.append(f"Останні теми: {'; '.join(hourly_summaries[-3:])}")
    
    # Додаємо найважливіші повідомлення
    important_messages = [msg for msg in scored_messages if msg['score'] >= 7]
    if important_messages:
        context_parts.append("Важливі повідомлення:")
        for msg in important_messages[-5:]:  # Останні 5 важливих
            context_parts.append(f"- {msg['text'][:100]}...")
    
    # Додаємо останні повідомлення
    recent_texts = [msg['text'] for msg in scored_messages[-10:]]
    if recent_texts:
        context_parts.append("Останні повідомлення:")
        context_parts.extend([f"- {text[:80]}..." for text in recent_texts])
    
    final_context = "\n".join(context_parts)
    
    # Обмежуємо розмір контексту
    max_size = PERSONA.get("max_context_size", 5000)
    if len(final_context) > max_size:
        final_context = final_context[:max_size] + "...[обрізано]"
    
    return final_context

def build_context(chat_id: int, limit: int) -> str:
    """
    Формує контекст як діалог з іменами користувачів.

    Args:
        chat_id: ID чату.
        limit: Кількість останніх повідомлень для включення.

    Returns:
        Відформатований рядок контексту.
    """
    messages = get_recent_messages(chat_id, limit)
    if not messages:
        return "Історія повідомлень порожня."

    dialogue = []
    for msg in messages:
        # Отримуємо ім'я користувача, або "Невідомий", якщо даних немає
        user_name = msg.get('full_name') or msg.get('username') or 'Невідомий'
        text = msg.get('text', '')

        # Форматуємо рядок діалогу
        dialogue.append(f"{user_name}: {text}")

    return "\n".join(dialogue)

async def get_enhanced_context(chat_id: int, message_text: str, user_name: str, limit: int = 50) -> str:
    """
    Створює розширений контекст з аналізом настрою та діалогом.
    """
    # Використовуємо нову функцію для побудови діалогу
    dialogue_history = build_context(chat_id, limit)

    # Формуємо фінальний промпт для Gemini
    final_context = (
        f"Поточний настрій у чаті: {mood}.\n"
        f"Ось остання історія діалогу:\n"
        f"--- (початок історії) ---\n"
        f"{dialogue_history}\n"
        f"--- (кінець історії) ---\n"
        f"Користувач '{user_name}' щойно написав: {message_text}"
    )
    return final_context

def filter_relevant_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Фільтрує релевантні повідомлення"""
    filtered = []
    seen_texts = set()
    
    for msg in messages:
        text = msg.get('text', '').strip()
        
        # Пропускаємо порожні, дублікати та службові
        if not text or len(text) < 3:
            continue
        if text in seen_texts:
            continue
        if text.startswith('/') and len(text.split()) == 1:  # Команди
            continue
        
        seen_texts.add(text)
        filtered.append(msg)
    
    return filtered

def score_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Оцінює важливість повідомлень"""
    for msg in messages:
        score = 5  # Базовий рейтинг
        text = msg.get('text', '').lower()
        
        # Бонуси за важливість
        if any(trigger in text for trigger in ['гряг', 'бот', '@gryag_bot']):
            score += 3
        if '?' in text:
            score += 2
        if len(text) > 50:
            score += 1
        if any(word in text for word in ['важливо', 'допомога', 'проблема']):
            score += 2
        
        msg['score'] = score
    
    return messages

def get_hourly_summaries(chat_id: int) -> List[str]:
    """Отримує резюме за останні години"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Отримуємо повідомлення за останні 24 години
        yesterday = datetime.now() - timedelta(hours=24)
        c.execute("""
            SELECT text, timestamp 
            FROM messages 
            WHERE chat_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (chat_id, yesterday.isoformat()))
        
        messages = c.fetchall()
        conn.close()
        
        if not messages:
            return []
        
        # Групуємо за годинами та створюємо summary
        hourly_groups = {}
        for text, timestamp in messages:
            try:
                hour = datetime.fromisoformat(timestamp).hour
                if hour not in hourly_groups:
                    hourly_groups[hour] = []
                hourly_groups[hour].append(text)
            except:
                continue
        
        summaries = []
        for hour in sorted(hourly_groups.keys(), reverse=True)[:6]:  # Останні 6 годин
            texts = hourly_groups[hour]
            # Створюємо простий summary
            common_words = extract_common_themes(texts)
            if common_words:
                summaries.append(f"{hour}:00 - {', '.join(common_words[:3])}")
        
        return summaries
        
    except Exception as e:
        print(f"Помилка отримання hourly summaries: {e}")
        return []

def analyze_chat_mood_and_topic(messages: List[Dict[str, Any]]) -> str:
    """Аналізує настрій та тему чату"""
    if not messages:
        return "спокійний"
    
    all_text = " ".join([msg.get('text', '') for msg in messages[-10:]]).lower()
    
    # Аналіз настрою
    positive_words = ['добре', 'класно', 'супер', 'круто', 'весело', '😊', '😄', '👍', '❤️']
    negative_words = ['погано', 'сумно', 'жахливо', 'проблема', '😢', '😞', '👎']
    question_words = ['що', 'як', 'коли', 'де', 'чому', '?']
    
    positive_count = sum(word in all_text for word in positive_words)
    negative_count = sum(word in all_text for word in negative_words)
    question_count = sum(word in all_text for word in question_words)
    
    if positive_count > negative_count + 1:
        mood = "позитивний"
    elif negative_count > positive_count + 1:
        mood = "негативний"
    elif question_count > 2:
        mood = "допитливий"
    else:
        mood = "нейтральний"
    
    return mood

def extract_common_themes(texts: List[str]) -> List[str]:
    """Витягує основні теми з текстів"""
    words = []
    for text in texts:
        # Витягуємо слова довжиною 4+ символи
        text_words = [word.lower() for word in text.split() if len(word) >= 4 and word.isalpha()]
        words.extend(text_words)
    
    # Рахуємо частотність
    from collections import Counter
    word_counts = Counter(words)
    
    # Повертаємо топ слова, виключаючи стоп-слова
    stop_words = {'який', 'яка', 'яке', 'цей', 'ця', 'це', 'той', 'та', 'те', 'мене', 'тебе'}
    common_themes = [word for word, count in word_counts.most_common(10) 
                    if word not in stop_words and count > 1]
    
    return common_themes[:5]
