# Покращений модуль для розумної поведінки та передбачення ситуацій
import time
import random
import re
from datetime import datetime, timedelta
from collections import defaultdict
from bot.bot_config import PERSONA

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
chat_analysis_history = defaultdict(list)  # chat_id -> [analysis_data]
last_intervention = defaultdict(float)  # chat_id -> timestamp

def analyze_conversation_context(message_text, recent_messages=None):
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

def detect_conversation_type(text):
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

def detect_mood(text):
    """Визначає настрій повідомлення"""
    scores = {}
    for mood, indicators in MOOD_INDICATORS.items():
        score = sum(1 for indicator in indicators if indicator in text)
        scores[mood] = score
    
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "нейтрал"

def calculate_engagement_level(text, conv_type, mood):
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
        ("технічне", "нейтрал"): "розумний_абсурд",
        ("філософське", "нейтрал"): "глибокий_абсурд",
        ("філософське", "позитив"): "мудрий_гумор",
        ("веселе", "позитив"): "веселий_абсурд",
        ("веселе", "енергія"): "енергійний_гумор",
        ("емоційне", "негатив"): "підтримуючий_абсурд",
        ("емоційне", "позитив"): "радісний_гумор",
        ("конфлікт", "негатив"): "розряджаючий_абсурд",
        ("побутове", "нейтрал"): "легкий_гумор"
    }
    
    return tone_map.get((conv_type, mood), "стандартний_абсурд")

def extract_keywords(text):
    """Витягує ключові слова"""
    words = re.findall(r'\b\w{4,}\b', text.lower())
    stop_words = {"який", "яка", "яке", "цей", "ця", "це", "той", "та", "те"}
    keywords = [word for word in words if word not in stop_words]
    return sorted(set(keywords), key=len, reverse=True)[:5]

def create_context_aware_prompt(message_text, analysis):
    """Створює промт з урахуванням контексту"""
    base_prompt = "Ти — Гряг, абсурдний дух чату з дотепним гумором."
    
    context_info = f"""
Ситуація:
- Тип розмови: {analysis['type']}
- Настрій: {analysis['mood']}
- Рівень залученості: {analysis['engagement']}/10
- Рекомендований тон: {analysis['response_tone']}

Повідомлення: "{message_text}"
"""
    
    tone_instructions = {
        "розумний_жарт": "Відповідай розумно, але з дотепними жартами.",
        "розумний_абсурд": "Будь розумним, але з абсурдними висновками.",
        "глибокий_абсурд": "Філософствуй абсурдно, ставь дивні питання.",
        "веселий_абсурд": "Будь максимально смішним та абсурдним.",
        "підтримуючий_абсурд": "Підтримай, але абсурдним способом.",
        "розряджаючий_абсурд": "Розрядь напругу абсурдним коментарем."
    }
    
    instruction = tone_instructions.get(analysis['response_tone'], "Відповідай у своєму абсурдному стилі.")
    
    return f"{base_prompt}\n{context_info}\n\nІнструкція: {instruction}\n\nВідповідай коротко (1-2 речення), дотепно та по-українськи."

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
            "Ти — Гряг. В чаті довго тиша. Скажи щось абсурдно-філософське щоб оживити атмосферу.",
            "Ти — Гряг. Чат замовк. Поділись якоюсь дивною думкою або спостереженням.",
        ]
    elif trends["mood_trend"] == "negative":
        prompts = [
            "Ти — Гряг. В чаті негативний настрій. Скажи щось абсурдно-підбадьорливе.",
            "Ты — Гряг. Потрібно підняти настрій. Скажи щось дивне але позитивне.",
        ]
    else:
        prompts = [
            "Ти — Гряг. Скажи щось абсурдне просто так, щоб нагадати про себе.",
            "Ты — Гряг. Час для спонтанної абсурдної думки або коментаря.",
        ]
    
    return random.choice(prompts)
