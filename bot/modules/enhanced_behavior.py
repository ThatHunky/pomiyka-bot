# Покращений модуль для розумної поведінки та передбачення ситуацій
import time
import random
import re
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple
from bot.bot_config import PERSONA

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
    """Аналізує контекст розмови та повертає рекомендації для бота"""
    if not message_text:
        return {"type": "unknown", "mood": "neutral", "should_respond": False}
    
    text = message_text.lower()
    
    # Визначаємо тип розмови
    conv_type = detect_conversation_type(text)
    
    # Аналізуємо настрій
    mood = detect_mood(text)
    
    # Рівень залученості
    engagement = calculate_engagement_level(text, conv_type, mood)
    
    # Чи варто відповісти
    should_respond = should_bot_respond(text, conv_type, mood, engagement)
    
    # Рекомендований тон відповіді
    response_tone = get_response_tone(conv_type, mood)
    
    return {
        "type": conv_type,
        "mood": mood,
        "engagement": engagement,
        "should_respond": should_respond,
        "response_tone": response_tone,
        "keywords": extract_keywords(text)
    }

def detect_conversation_type(text: str) -> str:
    """Визначає тип розмови з покращеним аналізом"""
    scores = {}
    text_lower = text.lower()
    
    for conv_type, keywords in CONVERSATION_PATTERNS.items():
        score = 0
        for keyword in keywords:
            # Пошук точних збігів та підрядків
            if keyword in text_lower:
                score += 1
                # Бонус за точний збіг слова
                if f" {keyword} " in f" {text_lower} ":
                    score += 0.5
        scores[conv_type] = score
    
    # Додаткові правила для кращого розпізнавання
    
    # Технічний контекст: помилки, з'єднання, колекції
    if any(word in text_lower for word in ["помилк", "підключен", "колекц", "перлин", "океан", "інтернет"]):
        scores["технічне"] = scores.get("технічне", 0) + 2
    
    # Філософський контекст: метафори, глибокі думки
    if any(word in text_lower for word in ["таємнич", "глибин", "сенс", "буття", "реальн"]):
        scores["філософське"] = scores.get("філософське", 0) + 2
    
    # Поетичний/творчий контекст
    if any(word in text_lower for word in ["перлин", "океан", "павутин", "розущен"]):
        scores["філософське"] = scores.get("філософське", 0) + 1.5
    
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "загальне"

def detect_mood(text: str) -> str:
    """Визначає настрій повідомлення"""
    scores = {}
    for mood, indicators in MOOD_INDICATORS.items():
        score = sum(1 for indicator in indicators if indicator in text)
        scores[mood] = score
    
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "нейтрал"

def calculate_engagement_level(text: str, conv_type: str, mood: str) -> int:
    """Розраховує рівень залученості бота (1-10)"""
    base_level = 3
    
    # Згадки бота
    bot_keywords = PERSONA.get("trigger_keywords", ["гряг", "бот"])
    bot_mentions = sum(1 for keyword in bot_keywords if keyword.strip() in text)
    base_level += bot_mentions * 3
    
    # Тип розмови
    type_bonuses = {
        "технічне": 2,
        "філософське": 2,
        "веселе": 1,
        "емоційне": 1,
        "конфлікт": -1
    }
    base_level += type_bonuses.get(conv_type, 0)
    
    # Настрій
    mood_bonuses = {
        "позитив": 1,
        "негатив": -1,
        "енергія": 2,
        "нейтрал": 1
    }
    base_level += mood_bonuses.get(mood, 0)
    
    # Питання
    if "?" in text:
        base_level += 2
    
    return max(1, min(10, base_level))

def should_bot_respond(text, conv_type, mood, engagement):
    """Визначає чи варто боту відповісти"""
    # Завжди відповідаємо на згадки
    bot_keywords = PERSONA.get("trigger_keywords", ["гряг", "бот"])
    if any(keyword.strip() in text for keyword in bot_keywords):
        return True
    
    # Високий рівень залученості
    if engagement >= 7:
        return True
    
    # Конфлікти - для розрядки
    if conv_type == "конфлікт":
        return random.random() < 0.6
    
    # Філософські та технічні дискусії
    if conv_type in ["філософське", "технічне"]:
        return random.random() < 0.4
    
    # Питання
    if "?" in text:
        return random.random() < 0.3
    
    # Базовий шанс
    return random.random() < PERSONA.get("smart_reply_chance", 0.1)

def get_response_tone(conv_type, mood):
    """Рекомендує тон для відповіді"""
    tone_map = {
        ("технічне", "позитив"): "розумний_жарт",
        ("технічне", "нейтрал"): "розумний_жарт",
        ("філософське", "нейтрал"): "мудрий_жарт",
        ("філософське", "позитив"): "мудрий_гумор",
        ("веселе", "позитив"): "веселий_жарт",
        ("веселе", "енергія"): "енергійний_жарт",
        ("емоційне", "негатив"): "підтримуючий_жарт",
        ("емоційне", "позитив"): "радісний_жарт",
        ("конфлікт", "негатив"): "розряджаючий_жарт",
        ("побутове", "нейтрал"): "дружелюбний_жарт"
    }
    
    return tone_map.get((conv_type, mood), "дружелюбний_жарт")

def extract_keywords(text):
    """Витягує ключові слова"""
    words = re.findall(r'\b\w{4,}\b', text.lower())
    stop_words = {"який", "яка", "яке", "цей", "ця", "це", "той", "та", "те"}
    keywords = [word for word in words if word not in stop_words]
    return sorted(set(keywords), key=len, reverse=True)[:5]

def get_tone_instruction(analysis):
    """Повертає інструкцію тону для відповіді на основі аналізу"""
    tone_instructions = {
        "розумний_жарт": "Відповідай розумно з легким гумором та корисними порадами. Будь конкретним та по суті.",
        "дружелюбний_жарт": "Будь дружелюбним та приємним у спілкуванні. Використовуй нормальні слова.",
        "підтримуючий_жарт": "Підтримай розмову легким гумором та дотепними коментарями. Будь адекватним.",
        "веселий_жарт": "Будь веселим та дотепним, але не переборщуй. Говори зрозуміло.",
        "підтримуючий": "Підтримай та заспокій легким гумором. Будь розумним.",
        "розряджаючий_жарт": "Розрядь напругу дружелюбним коментарем. Говори по суті.",
        "мудрий_жарт": "Будь мудрим та дотепним одночасно. Давай корисні поради.",
        "енергійний_жарт": "Відповідай енергійно та весело, але зрозуміло.",
        "радісний_жарт": "Будь радісним та позитивним. Говори нормально.",
        "легкий_жарт": "Використовуй легкий, невимушений гумор. Будь адекватним та зрозумілим.",
        "направляючий_жарт": "Спробуй м'якко направити розмову в конструктивне русло. Будь корисним та по суті."
    }
    
    response_tone = analysis.get('response_tone', 'дружелюбний_жарт')
    base_instruction = tone_instructions.get(response_tone, "Відповідай дружелюбно з легким гумором. Будь розумним та адекватним.")
    
    # Додаємо спеціальні інструкції для ситуацій зі спамом
    spam_analysis = analysis.get('spam_analysis', {})
    context_quality = analysis.get('context_quality', {})
    
    special_instructions = []
    
    if spam_analysis.get('spam_level') in ['medium', 'high']:
        special_instructions.append("В чаті високий рівень активності - будь лаконічним та не додавай до спаму.")
    
    if context_quality.get('quality') == 'poor':
        special_instructions.append("Контекст розмови розбитий - спробуй дати корисну відповідь та направити розмову.")
    
    # Базова інструкція про стиль
    style_instruction = "ВАЖЛИВО: Говори нормальними словами, не використовуй занадто дивні або незрозумілі вирази. Будь дружелюбним та корисним."
    
    # Збираємо всі інструкції
    all_instructions = [base_instruction] + special_instructions + [style_instruction]
    
    return " ".join(all_instructions)

def create_context_aware_prompt(message_text, analysis):
    """ЗАСТАРІЛА функція - використовуйте get_tone_instruction замість неї"""
    return get_tone_instruction(analysis)

def update_chat_analysis(chat_id, analysis):
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
            "Ти — Гряг. В чаті довго тиша. Скажи щось цікаве, корисне або дотепне щоб оживити атмосферу. Будь дружелюбним та зрозумілим.",
            "Ти — Гряг. Чат замовк. Поділись якоюсь цікавою думкою, фактом або спостереженням. Говори нормально та по суті.",
            "Ти — Гряг. Тиша в чаті. Скажи щось корисне або запитай щось цікаве у людей. Будь дружелюбним.",
        ]
    elif trends["mood_trend"] == "negative":
        prompts = [
            "Ти — Гряг. В чаті негативний настрій. Скажи щось підбадьорливе та позитивне. Будь розумним та підтримуючим.",
            "Ты — Гряг. Потрібно підняти настрій. Скажи щось дотепне але позитивне та мотивуюче. Говори зрозуміло.",
            "Ти — Гряг. Настрій не дуже. Поділись чимось цікавим та позитивним. Будь корисним.",
        ]
    else:
        prompts = [
            "Ти — Гряг. Скажи щось цікаве або корисне просто так, щоб нагадати про себе. Будь дружелюбним.",
            "Ты — Гряг. Час для спонтанної цікавої думки, корисного факту або дотепного коментаря. Говори зрозуміло.",
            "Ти — Гряг. Поділись цікавою думкою або запитай щось у людей. Будь адекватним та корисним.",
        ]
    
    base_prompt = random.choice(prompts)
    return f"{base_prompt} ВАЖЛИВО: Використовуй нормальні, зрозумілі слова. Не говори дивних речей."

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
    """Розумно стискає контекст, зберігаючи найважливіші повідомлення"""
    if len(context) <= max_context_size:
        return context
    
    # Розділяємо повідомлення на категорії важливості
    important_messages = []
    regular_messages = []
    
    for msg in context:
        text = msg.get('text', '').lower()
        
        # Важливі повідомлення: згадки бота, питання, довгі повідомлення
        if (any(trigger in text for trigger in PERSONA.get("trigger_keywords", [])) or
            '?' in text or len(text) > 100):
            important_messages.append(msg)
        else:
            regular_messages.append(msg)
    
    # Зберігаємо всі важливі повідомлення + частину звичайних
    remaining_space = max_context_size - len(important_messages)
    
    if remaining_space > 0:
        # Беремо найновіші звичайні повідомлення
        selected_regular = regular_messages[-remaining_space:]
        compressed_context = important_messages + selected_regular
    else:
        # Якщо важливих повідомлень занадто багато, беремо найновіші
        compressed_context = important_messages[-max_context_size:]
    
    # Сортуємо за часом
    compressed_context.sort(key=lambda x: x.get('timestamp', 0))
    
    return compressed_context

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
