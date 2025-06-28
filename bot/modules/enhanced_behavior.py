# Покращений модуль для розумної поведінки та передбачення ситуацій
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re
from typing import Dict, List, Any, Optional, Tuple
from aiogram.types import Message
from bot.bot_config import PERSONA
from . import context_sqlite
from .token_counter import token_counter
import logging

# Налаштування логування для модуля
logger = logging.getLogger(__name__)

# Розширені патерни для аналізу розмов
CONVERSATION_PATTERNS = {
    "технічне": [
        "код", "програма", "алгоритм", "функція", "баг", "сервер", "API", "git", 
        "python", "javascript", "react", "hooks", "помилка", "підключення", "інтернет", 
        "комп'ютер", "технічн", "програмув", "розробк", "бекенд", "фронтенд", "база", 
        "данних", "sql", "backend", "frontend", "upав", "оновлюються", "технологі", 
        "ai", "штучний", "інтелект", "нейронн", "мережі"
    ],
    "філософське": [
        "життя", "смерть", "любов", "сенс", "мета", "що таке", "чому", "як думаєш", 
        "буття", "душа", "розум", "свідомість", "реальність", "істина", "віра", 
        "справжн", "дружба", "існує", "взагалі", "квантов", "фізика", "паралельн", 
        "всесвіт", "філософ", "мудрість", "істин"
    ],
    "веселе": [
        "хаха", "лол", "😂", "жарт", "прикол", "смішно", "ору", "мем", "кек", "ржу", 
        "хахаха", "найкращий", "року", "весело", "😄", "😆", "🤣"
    ],
    "емоційне": [
        "😢", "😭", "😡", "💔", "сумно", "весело", "злий", "радій", "переживаю", 
        "болить", "страждаю", "щасливий", "так сумно", "не хочеться", "нічого", 
        "робити", "настрій", "почуття", "емоці"
    ],
    "побутове": [
        "їжа", "робота", "навчання", "погода", "дім", "сім'я", "плани", "вчора", 
        "сьогодні", "завтра", "обід", "вечеря", "магазин", "покупк"
    ],
    "конфлікт": [
        "дурень", "ідіот", "не згоден", "неправий", "фігня", "лайно", "😡", "🤬", 
        "мудак", "кретин", "дурак", "прикидаєшся", "тупий", "блять"
    ]
}

# Емоційні маркери
MOOD_INDICATORS = {
    "позитив": ["класно", "супер", "круто", "дякую", "молодець", "вау", "ого", "❤️", "😍", "😊", "👍", "🔥"],
    "негатив": ["погано", "сумно", "злий", "лайно", "біда", "😢", "😭", "😡", "👎", "💩"],
    "нейтрал": ["думаю", "мабуть", "можливо", "цікаво", "🤔", "🧐"],
    "енергія": ["ого", "вау", "капець", "неймовірно", "🤯", "⚡", "🎉"]
}

# Історія для аналізу трендів  
chat_analysis_history: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
last_intervention: Dict[int, float] = defaultdict(float)

# Додані системи для розумної обробки спаму та контексту
chat_message_frequency: Dict[int, deque[float]] = defaultdict(deque)  # Частота повідомлень по чатах
context_compression_cache: Dict[int, Dict[str, Any]] = defaultdict(dict)  # Кеш стисненого контексту
spam_detection_scores: Dict[int, Dict[str, float]] = defaultdict(lambda: defaultdict(float))  # Оцінки спаму

def analyze_conversation_context(message_text: str, recent_messages: Optional[List[str]] = None) -> Dict[str, Any]:
    """Аналізує текст повідомлення та визначає тип, настрій та залученість."""
    conv_type = detect_conversation_type(message_text)
    mood = detect_mood(message_text)
    engagement = calculate_engagement_level(message_text, conv_type, mood)
    keywords = extract_keywords(message_text)
    
    return {
        "type": conv_type,
        "mood": mood,
        "engagement": engagement,
        "keywords": keywords,
        "should_respond": should_bot_respond(message_text, conv_type, mood, engagement)
    }

def detect_conversation_type(text: str) -> str:
    """Визначає тип розмови за ключовими словами."""
    scores: Dict[str, int] = defaultdict(int)
    text_lower = text.lower()
    for conv_type, patterns in CONVERSATION_PATTERNS.items():
        for pattern in patterns:
            if pattern in text_lower:
                scores[conv_type] += 1
    
    # Додаткові правила для точності
    if "?" in text and scores.get("технічне", 0) > 0:
        scores["технічне"] = scores.get("технічне", 0) + 2

    if "як думаєш" in text_lower and scores.get("філософське", 0) > 0:
        scores["філософське"] = scores.get("філософське", 0) + 2

    if len(re.findall(r'[😂🤣😄😆]', text)) > 1:
        scores["веселе"] = scores.get("веселе", 0) + 1.5

    if scores:
        return max(scores, key=scores.get) if scores else 'побутове'
    return 'побутове'

def detect_mood(text: str) -> str:
    """Визначає настрій повідомлення."""
    scores: Dict[str, int] = defaultdict(int)
    text_lower = text.lower()
    for mood, indicators in MOOD_INDICATORS.items():
        for indicator in indicators:
            if indicator in text_lower:
                scores[mood] += 1
    if scores:
        return max(scores, key=scores.get) if scores else 'нейтрал'
    return 'нейтрал'

def calculate_engagement_level(text: str, conv_type: str, mood: str) -> int:
    """Оцінює рівень залученості (1-10)."""
    score = 5  # базовий рівень
    if 'Гряг' in text or '@gryag_bot' in text:
        score += 3
    if '??' in text:
        score += 2
    if len(text) > 100:
        score += 1
    if conv_type in ["технічне", "філософське", "конфлікт"]:
        score += 1
    if mood in ["позитив", "енергія"]:
        score += 1
    return min(max(1, score), 10)

def should_bot_respond(text: str, conv_type: str, mood: str, engagement: int) -> bool:
    """Вирішує, чи варто боту відповідати."""
    if engagement > 7:
        return True
    if conv_type == "конфлікт" and mood == "негатив":
        return False  # Не втручаємось у конфлікти
    if PERSONA.get("smart_reply_chance", 0.1) > random.random():
        return True
    return False

def get_response_tone(conv_type: str, mood: str) -> str:
    """Визначає тон відповіді."""
    tone_map = PERSONA.get("tone_mappings", {})
    return tone_map.get((conv_type, mood), "природне_спілкування")

def extract_keywords(text: str) -> List[str]:
    """Витягує ключові слова."""
    words = re.findall(r'\b\w{4,}\b', text.lower())
    # Тут можна додати більш складну логіку, наприклад, TF-IDF
    return list(set(words))[:5] # 5 найчастіших слів

def get_tone_instruction(analysis: Dict[str, Any]) -> str:
    """Генерує інструкцію по тону на основі аналізу."""
    tone = get_response_tone(analysis['type'], analysis['mood'])
    return PERSONA["tone_mappings"].get(tone, "Спілкуйся природно і дружелюбно.")


def create_context_aware_prompt(message: Message, analysis: Dict[str, Any]) -> Tuple[str, str]:
    """
    Створює персоналізований промпт і системну інструкцію для Gemini,
    враховуючи аналіз контексту та історію діалогу.
    """
    chat_id = message.chat.id
    user_name = message.from_user.full_name if message.from_user else "Анонім"
    
    # 1. Отримуємо історію діалогу з іменами
    messages = context_sqlite.get_context(chat_id, limit=PERSONA.get("context_limit", 50))
    dialog_lines = []
    for msg in messages:
        dialog_user_name = msg.get("user_name", "Користувач")
        text = msg.get("text", "")
        if text:
            dialog_lines.append(f"{dialog_user_name}: {text}")
    dialog_context = "\n".join(dialog_lines)

    # 2. Формуємо промпт
    prompt = (
        f"Ось історія чату:\n{dialog_context}\n\n"
        f"Зараз користувач '{user_name}' пише:\n{message.text}\n\n"
        f"Гряг, твоя відповідь:"
    )

    # 3. Формуємо системну інструкцію на основі аналізу
    tone_instruction = get_tone_instruction(analysis)
    system_instruction = (
        "Ти - дружелюбний чат-бот з ім'ям Гряг у телеграм чаті. "
        "Відповідай ЛИШЕ українською мовою. "
        "Будь природним у спілкуванні, звертайся до користувача по імені, якщо це доречно. "
        f"{tone_instruction}" # Додаємо інструкцію по тону
    )
    
    return prompt, system_instruction


def update_chat_analysis(chat_id: int, analysis: Dict[str, Any]) -> None:
    """Оновлює історію аналізу чату"""
    timestamp = time.time()
    chat_analysis_history[chat_id].append({
        "timestamp": timestamp,
        "type": analysis["type"],
        "mood": analysis["mood"],
        "engagement": analysis["engagement"]
    })
    
    # Зберігаємо тільки останні 100 записів
    chat_analysis_history[chat_id] = chat_analysis_history[chat_id][-100:]

def get_chat_trends(chat_id, hours=6):
    """Аналізує тренди чату за останні години"""
    current_time = time.time()
    cutoff_time = current_time - (hours * 3600)
    
    recent_analysis = [
        a for a in chat_analysis_history[chat_id] 
        if a["timestamp"] > cutoff_time
    ]
    
    if not recent_analysis:
        return {"activity": "low", "mood_trend": "stable", "topics": []}
    
    # Активність
    activity_level = "high" if len(recent_analysis) > 20 else "medium" if len(recent_analysis) > 5 else "low"
    
    # Тренд настрою
    moods = [a["mood"] for a in recent_analysis]
    positive_moods = sum(1 for mood in moods if mood in ["позитив", "енергія"])
    mood_trend = "positive" if positive_moods > len(moods) // 2 else "negative" if positive_moods < len(moods) // 3 else "stable"
    
    # Популярні теми
    topics = [a["type"] for a in recent_analysis]
    topic_counts = {}
    for topic in topics:
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    popular_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        "activity": activity_level,
        "mood_trend": mood_trend,
        "topics": [topic for topic, count in popular_topics],
        "engagement_avg": sum(a["engagement"] for a in recent_analysis) / len(recent_analysis)
    }

def should_intervene_spontaneously(chat_id):
    """Визначає чи варто втрутитися спонтанно"""
    current_time = time.time()
    
    # Перевіряємо час з останнього втручання
    time_since_last = current_time - last_intervention[chat_id]
    
    # Мінімум 30 хвилин між спонтанними втручаннями
    if time_since_last < 1800:
        return False
    
    # Аналізуємо тренди
    trends = get_chat_trends(chat_id)
    
    # Втручаємося при низькій активності (оживити чат)
    if trends["activity"] == "low" and time_since_last > 3600:
        return random.random() < 0.3
    
    # Втручаємося при негативному тренді (підняти настрій)
    if trends["mood_trend"] == "negative":
        return random.random() < 0.4
    
    # Базова спонтанність
    return random.random() < PERSONA.get("spontaneous_chance", 0.02)

def mark_intervention(chat_id):
    """Позначає що бот втрутився"""
    last_intervention[chat_id] = time.time()

def get_spontaneous_prompt_based_on_trends(chat_id):
    """Генерує спонтанний промт на основі трендів чату"""
    trends = get_chat_trends(chat_id)
    
    if trends["activity"] == "low":
        prompts = [
            "Ти — Гряг. В чаті довго немає активності. Скажи щось цікаве або корисне щоб підтримати спілкування. Будь дружелюбним.",
            "Ти — Гряг. Чат замовк. Поділись якоюсь цікавою думкою або запитай щось у людей. Говори природно.",
            "Ти — Гряг. Спокій в розмові. Скажи щось корисне або цікаве. Будь дружелюбним та зрозумілим.",
            "Ти — Гряг. Пауза у спілкуванні. Розкажи щось цікаве або запропонуй тему для обговорення.",
            "Ти — Гряг. Затишшя в чаті. Поділись корисною інформацією або цікавим спостереженням.",
        ]
    elif trends["mood_trend"] == "negative":
        prompts = [
            "Ти — Гряг. В чаті негативний настрій. Скажи щось позитивне та підбадьорливе. Будь підтримуючим.",
            "Ти — Гряг. Потрібно підняти настрій. Скажи щось позитивне та мотивуюче. Говори зрозуміло.",
            "Ти — Гряг. Настрій не дуже. Поділись чимось позитивним та корисним. Будь дружелюбним.",
            "Ти — Гряг. Напруга в чаті. Розрядь атмосферу дружелюбним та позитивним коментарем.",
        ]
    else:
        prompts = [
            "Ти — Гряг. Скажи щось цікаве або корисне просто так. Будь дружелюбним та природним.",
            "Ти — Гряг. Поділись цікавою думкою або корисним фактом. Говори зрозуміло.",
            "Ти — Гряг. Запитай щось цікаве у людей або поділись корисною інформацією. Будь адекватним.",
            "Ти — Гряг. Підтримай розмову цікавим коментарем або запропонуй нову тему.",
            "Ти — Гряг. Долучися до чату з корисною думкою або цікавим спостереженням.",
        ]
    
    base_prompt = random.choice(prompts)
    return f"{base_prompt} Говори природно та зрозуміло."

def cleanup_old_analysis_data(max_age_hours: int = 48):
    """Очищає старі дані аналізу для економії пам'яті"""
    current_time = time.time()
    cutoff_time = current_time - (max_age_hours * 3600)
    
    cleaned_chats = 0
    for chat_id in list(chat_analysis_history.keys()):
        original_count = len(chat_analysis_history[chat_id])
        chat_analysis_history[chat_id] = [
            analysis for analysis in chat_analysis_history[chat_id]
            if analysis["timestamp"] > cutoff_time
        ]
        new_count = len(chat_analysis_history[chat_id])
        
        if new_count != original_count:
            logging.info(f"Очищено {original_count - new_count} старих записів для чату {chat_id}")
            cleaned_chats += 1
    
    return cleaned_chats

def analyze_chat_spam_level(chat_id: int, recent_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Аналізує рівень спаму та активності в чаті"""
    current_time = time.time()
    
    # Очищуємо старі записи (останні 5 хвилин)
    five_minutes_ago = current_time - 300
    chat_message_frequency[chat_id] = deque([
        ts for ts in chat_message_frequency[chat_id] if ts > five_minutes_ago
    ])
    
    # Додаємо поточний час
    chat_message_frequency[chat_id].append(current_time)
    
    # Аналізуємо частоту повідомлень
    message_count = len(chat_message_frequency[chat_id])
    spam_level = "low"
    
    if message_count > 30:  # Більше 30 повідомлень за 5 хвилин
        spam_level = "high"
    elif message_count > 15:  # 15-30 повідомлень за 5 хвилин
        spam_level = "medium"
    
    # Аналізуємо повторювані повідомлення
    if recent_messages:
        recent_texts = [msg.get('text', '').lower() for msg in recent_messages[-10:]]
        unique_texts = set(recent_texts)
        repetition_ratio = 1 - (len(unique_texts) / len(recent_texts)) if recent_texts else 0
        
        if repetition_ratio > 0.7:  # Більше 70% повторюваних повідомлень
            spam_level = "high"
        elif repetition_ratio > 0.4:  # 40-70% повторюваних повідомлень
            spam_level = "medium" if spam_level == "low" else spam_level
    
    return {
        "spam_level": spam_level,
        "message_frequency": message_count,
        "should_reduce_activity": spam_level in ["medium", "high"],
        "suggested_reply_chance": _get_spam_adjusted_reply_chance(spam_level)
    }

def _get_spam_adjusted_reply_chance(spam_level: str) -> float:
    """Повертає скоригований шанс відповіді залежно від рівня спаму"""
    base_chance = PERSONA.get("smart_reply_chance", 0.05)
    
    if spam_level == "high":
        return base_chance * 0.1  # Зменшуємо в 10 разів
    elif spam_level == "medium":
        return base_chance * 0.3  # Зменшуємо в 3 рази
    else:
        return base_chance

def compress_context_smartly(context: List[Dict[str, Any]], max_context_size: int = 100) -> List[Dict[str, Any]]:
    """
    Розумно стискає контекст, зберігаючи найважливіші повідомлення.
    Тепер використовує підрахунок токенів замість кількості повідомлень.
    """
    if not context:
        return context
    
    # Використовуємо нові параметри для токенів
    max_tokens = PERSONA.get('max_context_tokens', 800000)
    
    # Якщо параметр max_context_size передано як кількість повідомлень, 
    # конвертуємо в токени (для зворотної сумісності)
    if max_context_size < 10000:  # Якщо це кількість повідомлень
        estimated_tokens_per_message = 50  # Середня оцінка
        max_tokens = min(max_tokens, max_context_size * estimated_tokens_per_message)
    
    # Використовуємо token_counter для оптимального стискання
    compressed = token_counter.compress_context_by_tokens(context, max_tokens)
    
    logger.info(f"Контекст стиснено: {len(context)} -> {len(compressed)} повідомлень, "
                f"~{token_counter.estimate_context_tokens(compressed)} токенів")
    
    return compressed

def analyze_context_quality(context: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Аналізує якість контексту для покращення відповідей"""
    if not context:
        return {"quality": "poor", "coherence": 0, "topics": []}
    
    # Аналізуємо когерентність розмови
    recent_messages = context[-10:]  # Останні 10 повідомлень
    topics = []
    
    for msg in recent_messages:
        text = msg.get('text', '')
        if text:
            analysis = analyze_conversation_context(text)
            topics.append(analysis['type'])
    
    # Рахуємо когерентність (наскільки схожі теми)
    if topics:
        topic_counts = {}
        for topic in topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Якщо є домінуюча тема, когерентність вища
        max_count = max(topic_counts.values())
        coherence = max_count / len(topics)
    else:
        coherence = 0
    
    # Визначаємо якість контексту
    if coherence > 0.7:
        quality = "high"
    elif coherence > 0.4:
        quality = "medium"
    else:
        quality = "poor"
    
    return {
        "quality": quality,
        "coherence": coherence,
        "dominant_topics": [topic for topic, count in topic_counts.items() if count == max(topic_counts.values())],
        "message_count": len(recent_messages)
    }

def should_respond_contextually(message_text: str, chat_id: int, context: List[Dict[str, Any]], 
                               recent_messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Розумно визначає чи потрібно відповідати з урахуванням контексту та спаму"""
    
    # Базовий аналіз повідомлення
    base_analysis = analyze_conversation_context(message_text)
    
    # Аналіз спаму в чаті
    spam_analysis = analyze_chat_spam_level(chat_id, recent_messages or [])
    
    # Аналіз якості контексту
    context_quality = analyze_context_quality(context)
    
    # Коригуємо рішення на основі спаму
    should_respond = base_analysis["should_respond"]
    
    if spam_analysis["should_reduce_activity"]:
        # В умовах спаму відповідаємо рідше
        if not any(trigger in message_text.lower() for trigger in PERSONA.get("trigger_keywords", [])):
            # Якщо не згадали бота прямо, різко зменшуємо шанс відповіді
            should_respond = should_respond and (random.random() < spam_analysis["suggested_reply_chance"])
    
    # Покращуємо якість відповіді в залежності від контексту
    if context_quality["quality"] == "poor" and should_respond:
        # В поганому контексті намагаємося направити розмову
        base_analysis["response_tone"] = "направляючий_жарт"
    
    return {
        **base_analysis,
        "should_respond": should_respond,
        "spam_analysis": spam_analysis,
        "context_quality": context_quality,
        "adjusted_reply_chance": spam_analysis["suggested_reply_chance"]
    }

def process_message_with_smart_context(message_text: str, chat_id: int, context: List[Dict[str, Any]], 
                                       recent_messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Головна функція для розумної обробки повідомлень з урахуванням контексту та спаму"""
    
    # Комплексний аналіз повідомлення та контексту
    analysis = should_respond_contextually(message_text, chat_id, context, recent_messages)
    
    # Якщо контекст занадто великий, стискаємо його
    if len(context) > 100:
        compressed_context = compress_context_smartly(context)
        logging.info(f"Стиснуто контекст для чату {chat_id}: {len(context)} -> {len(compressed_context)}")
        context = compressed_context
    
    # Оновлюємо історію аналізу
    update_chat_analysis(chat_id, analysis)
    
    # Повертаємо результат для використання у відповіді
    return {
        **analysis,
        "processed_context": context,
        "tone_instruction": get_tone_instruction(analysis),
        "recommendations": _get_response_recommendations(analysis)
    }

def _get_response_recommendations(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Генерує рекомендації для відповіді на основі аналізу"""
    recommendations = {}
    
    spam_level = analysis.get('spam_analysis', {}).get('spam_level', 'low')
    context_quality = analysis.get('context_quality', {}).get('quality', 'medium')
    
    # Рекомендації щодо довжини відповіді
    if spam_level == 'high':
        recommendations['max_response_length'] = 50  # Дуже коротка відповідь
        recommendations['response_style'] = 'minimal'
    elif spam_level == 'medium':
        recommendations['max_response_length'] = 100  # Коротка відповідь
        recommendations['response_style'] = 'concise'
    else:
        recommendations['max_response_length'] = 200  # Нормальна відповідь
        recommendations['response_style'] = 'normal'
    
    # Рекомендації щодо типу відповіді
    if context_quality == 'poor':
        recommendations['should_ask_clarification'] = True
        recommendations['should_provide_guidance'] = True
    
    return recommendations

def get_anti_spam_message(spam_level: str) -> Optional[str]:
    """Повертає повідомлення для ситуацій зі спамом"""
    if spam_level == 'high':
        return random.choice([
            "Ой, тут трохи багато активності! Давайте притихнемо на хвилинку 🤫",
            "Спокійніше, друзі! Дайте мені обдумати що відповісти 🤔",
            "Тіха, хлопці! Занадто швидко пишете 😅"
        ])
    elif spam_level == 'medium':
        return random.choice([
            "Ого, як активно! 🔥",
            "Багато повідомлень одразу! 📱",
            "Активність зашкалює! ⚡"
        ])
    
    return None

# Логування обробки контексту для діагностики
def log_context_processing(chat_id: int, message_count: int, spam_level: str, context_quality: str):
    logger.info(f"Чат {chat_id}: повідомлень={message_count}, спам={spam_level}, якість_контексту={context_quality}")

def get_processing_statistics(chat_id: int) -> Dict[str, Any]:
    """Отримує статистику обробки для чату"""
    current_time = time.time()
    hour_ago = current_time - 3600
    
    # Статистика частоти повідомлень
    recent_timestamps = [ts for ts in chat_message_frequency[chat_id] if ts > hour_ago]
    
    # Статистика аналізу
    recent_analysis = [
        a for a in chat_analysis_history[chat_id] 
        if a["timestamp"] > hour_ago
    ]
    
    return {
        "chat_id": chat_id,
        "messages_last_hour": len(recent_timestamps),
        "analysis_records": len(recent_analysis),
        "last_intervention": last_intervention.get(chat_id, 0),
        "current_time": current_time
    }

def generate_enhanced_response(message: Message, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерує покращену відповідь з урахуванням контексту та персоналізації.
    
    Args:
        message: Повідомлення користувача
        context_data: Дані контексту з іменами користувачів та аналізом
        
    Returns:
        Словник з рекомендаціями для генерації відповіді
    """
    user_name = getattr(message.from_user, 'full_name', 'Невідомий') if message.from_user else 'Невідомий'
    text = message.text or ""
    
    # Аналізуємо тип розмови та настрій
    conv_type = detect_conversation_type(text)
    mood = detect_mood(text)
    engagement = calculate_engagement_level(text, conv_type, mood)
    
    # Формуємо персоналізовану інструкцію
    personal_instruction = f"Відповідай користувачу '{user_name}' "
    
    if conv_type == "технічне":
        personal_instruction += "надаючи корисну технічну інформацію. "
    elif conv_type == "філософське":
        personal_instruction += "з цікавими роздумами та запитаннями. "
    elif conv_type == "веселе":
        personal_instruction += "підтримуючи веселий настрій. "
    elif conv_type == "емоційне":
        personal_instruction += "з розумінням та підтримкою. "
    else:
        personal_instruction += "дружньо та природно. "
    
    # Рекомендації для тону
    response_tone = get_response_tone(conv_type, mood)
    tone_instruction = f"Використовуй {response_tone} тон спілкування. "
    
    # Додаткові рекомендації
    if engagement > 7:
        tone_instruction += "Користувач дуже зацікавлений, дай детальну відповідь. "
    elif engagement < 4:
        tone_instruction += "Дай коротку, але корисну відповідь. "
    
    # Уникання повторів
    tone_instruction += "Використовуй різноманітні слова та фрази, уникай повторення однакових виразів. "
    
    return {
        "should_reply": should_bot_respond(text, conv_type, mood, engagement),
        "tone_instruction": personal_instruction + tone_instruction,
        "conversation_type": conv_type,
        "mood": mood,
        "engagement_level": engagement,
        "user_name": user_name,
        "max_response_length": 200 if engagement > 7 else 100,
        "complex_request": engagement > 6 and conv_type in ["технічне", "філософське"]
    }

def should_reply_with_enhanced_logic(message: Message, context_data: Dict[str, Any]) -> bool:
    """
    Покращена логіка визначення чи потрібно відповідати.
    """
    analysis = generate_enhanced_response(message, context_data)
    return analysis.get("should_reply", False)

def get_enhanced_tone_instruction(message: Message, context_data: Dict[str, Any]) -> str:
    """
    Отримує покращену інструкцію для тону відповіді.
    """
    analysis = generate_enhanced_response(message, context_data)
    return analysis.get("tone_instruction", "Будь дружелюбним та природним.")
