# Модуль для передбачення та аналізу ситуацій в чаті
import re
import random
from datetime import datetime, timedelta
from collections import defaultdict
from bot.bot_config import PERSONA

# Патерни для розпізнавання типів розмов
CONVERSATION_PATTERNS = {
    "технічна_дискусія": [
        r"(\w+)\s+(код|програма|алгоритм|функція|метод|клас|змінна)",
        r"(помилка|баг|дебаг|логи|консоль|термінал)",
        r"(сервер|база\s+даних|API|JSON|XML|HTTP)",
        r"(React|Python|JavaScript|Java|C\+\+|Node\.js|Django)",
        r"(git|github|комміт|пуш|мердж|бранч)"
    ],
    "філософська_розмова": [
        r"(що\s+таке|в\s+чому\s+сенс|як\s+ти\s+думаєш|на\s+мою\s+думку)",
        r"(життя|смерть|любов|щастя|сенс|мета|мрія)",
        r"(чому\s+люди|що\s+означає|як\s+можна|чи\s+варто)",
        r"(філософія|психологія|мораль|етика|душа|розум)"
    ],
    "жарти_мемі": [
        r"(хаха|лол|😂|🤣|прикол|жарт|смішно)",
        r"(мем|гіф|стікер|картинка|відео)",
        r"(тролінг|сарказм|іронія)",
        r"(ору|плачу\s+від\s+сміху|не\s+можу|капець)"
    ],
    "емоційна_розмова": [
        r"(😢|😭|😡|😤|💔|😍|🥰|😘)",
        r"(сумно|весело|злий|щасливий|закоханий|розчарований)",
        r"(переживаю|хвилююсь|радію|злюсь|плачу|сміюсь)",
        r"(відчуваю|емоції|настрій|почуття)"
    ],
    "побутова_розмова": [
        r"(їжа|їсти|готувати|кухня|обід|вечеря|сніданок)",
        r"(робота|навчання|університет|школа|завдання|проект)",
        r"(погода|дощ|сонце|сніг|тепло|холодно)",
        r"(дім|квартира|сім'я|друзі|відпочинок|плани)"
    ],
    "конфлікт": [
        r"(дурень|ідіот|кретин|дебіл|мудак)",
        r"(не\s+згоден|ти\s+неправий|це\s+фігня|лайно)",
        r"(сварка|конфлікт|суперечка|не\s+розумієш)",
        r"(😡|🤬|👎|💩|🖕)"
    ]
}

# Історія настроїв чатів
chat_moods = defaultdict(list)
chat_topics = defaultdict(list)
user_patterns = defaultdict(lambda: defaultdict(int))

def analyze_message_context(message_text, chat_history):
    """Аналізує контекст повідомлення та передбачає подальший розвиток розмови"""
    if not message_text:
        return {"type": "unknown", "mood": "neutral", "prediction": "continue"}
    
    text = message_text.lower()
    
    # Визначаємо тип розмови
    conversation_type = detect_conversation_type(text)
    
    # Аналізуємо настрій
    mood = analyze_emotional_tone(text)
    
    # Передбачаємо розвиток розмови
    prediction = predict_conversation_flow(text, chat_history, conversation_type)
    
    # Визначаємо рівень залученості бота
    bot_engagement = calculate_bot_engagement_level(text, conversation_type, mood)
    
    return {
        "type": conversation_type,
        "mood": mood,
        "prediction": prediction,
        "engagement_level": bot_engagement,
        "should_intervene": should_bot_intervene(text, conversation_type, mood, chat_history),
        "suggested_tone": get_suggested_response_tone(conversation_type, mood),
        "context_keywords": extract_context_keywords(text)
    }

def detect_conversation_type(text: str) -> str:
    """Визначає тип розмови на основі патернів"""
    scores = {}
    
    for conv_type, patterns in CONVERSATION_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            score += matches
        scores[conv_type] = score
    
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    
    return "загальна_розмова"

def analyze_emotional_tone(text: str) -> str:
    """Аналізує емоційний тон повідомлення"""
    # Позитивні емоції
    positive_words = ["круто", "класно", "супер", "чудово", "весело", "радий", "щасливий", "❤️", "😍", "😊", "👍", "🔥"]
    positive_score = sum(1 for word in positive_words if word in text.lower())
    
    # Негативні емоції
    negative_words = ["погано", "сумно", "злий", "розчарований", "гірко", "лайно", "😢", "😭", "😡", "👎", "💩"]
    negative_score = sum(1 for word in negative_words if word in text.lower())
    
    # Нейтральні/задумливі
    thoughtful_words = ["думаю", "мабуть", "можливо", "цікаво", "🤔", "🧐"]
    thoughtful_score = sum(1 for word in thoughtful_words if word in text.lower())
    
    # Збуджені/енергійні
    excited_words = ["ого", "вау", "капець", "неймовірно", "🤯", "⚡", "🎉"]
    excited_score = sum(1 for word in excited_words if word in text.lower())
    
    scores = {
        "позитивний": positive_score,
        "негативний": negative_score,
        "задумливий": thoughtful_score,
        "збуджений": excited_score
    }
    
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    
    return "нейтральний"

def predict_conversation_flow(text: str, chat_history: List[Dict], conv_type: str) -> str:
    """Передбачає подальший розвиток розмови"""
    text_lower = text.lower()
    
    # Аналізуємо останні повідомлення
    recent_messages = chat_history[-5:] if chat_history else []
    recent_text = " ".join([msg.get("text", "") for msg in recent_messages]).lower()
    
    # Якщо багато питань - очікуємо дискусію
    question_count = text_lower.count("?") + recent_text.count("?")
    if question_count > 2:
        return "активна_дискусія"
    
    # Якщо згадується конкретна тема кілька разів - тема розвивається
    if conv_type != "загальна_розмова":
        return "розвиток_теми"
    
    # Емоційні повідомлення зазвичай викликають реакції
    emotional_indicators = ["!", "😂", "😢", "😡", "вау", "ого", "капець"]
    if any(indicator in text_lower for indicator in emotional_indicators):
        return "емоційна_реакція"
    
    # Довгі повідомлення зазвичай викликають обговорення
    if len(text) > 200:
        return "детальне_обговорення"
    
    # Короткі відповіді - розмова згасає
    if len(text) < 20 and not any(emoji in text for emoji in ["😂", "❤️", "👍"]):
        return "згасання"
    
    return "продовження"

def calculate_bot_engagement_level(text: str, conv_type: str, mood: str) -> int:
    """Розраховує рівень залученості бота (1-10)"""
    base_level = 3  # Базовий рівень
    
    # Згадки бота
    bot_mentions = sum(1 for trigger in PERSONA["trigger_keywords"] if trigger.strip() in text.lower())
    base_level += bot_mentions * 3
    
    # Тип розмови
    type_multipliers = {
        "технічна_дискусія": 2,
        "філософська_розмова": 2,
        "жарти_мемі": 1,
        "емоційна_розмова": 1,
        "побутова_розмова": 0,
        "конфлікт": -1,
        "загальна_розмова": 0
    }
    base_level += type_multipliers.get(conv_type, 0)
    
    # Настрій
    mood_multipliers = {
        "позитивний": 1,
        "негативний": -1,
        "задумливий": 2,
        "збуджений": 1,
        "нейтральний": 0
    }
    base_level += mood_multipliers.get(mood, 0)
    
    # Питання підвищують залученість
    if "?" in text:
        base_level += 2
    
    return max(1, min(10, base_level))

def should_bot_intervene(text: str, conv_type: str, mood: str, chat_history: List[Dict]) -> bool:
    """Визначає, чи варто боту втрутитися в розмову"""
    text_lower = text.lower()
    
    # Завжди втручаємося при згадках
    if any(trigger.strip() in text_lower for trigger in PERSONA["trigger_keywords"]):
        return True
    
    # Втручаємося в філософські та технічні дискусії
    if conv_type in ["філософська_розмова", "технічна_дискусія"]:
        return random.random() < 0.4
    
    # Втручаємося в конфлікти для розрядки
    if conv_type == "конфлікт":
        return random.random() < 0.6
    
    # Втручаємося при довгій тиші (аналізуємо останні повідомлення)
    if chat_history:
        last_messages_time = [msg.get("timestamp", 0) for msg in chat_history[-3:]]
        current_time = datetime.now().timestamp()
        if last_messages_time and current_time - max(last_messages_time) > 3600:  # 1 година тиші
            return random.random() < 0.3
    
    # Втручаємося при прямих питаннях
    question_words = ["що", "як", "коли", "де", "чому", "хто", "чи"]
    if any(word in text_lower for word in question_words) and "?" in text:
        return random.random() < 0.3
    
    return False

def get_suggested_response_tone(conv_type: str, mood: str) -> str:
    """Пропонує тон для відповіді бота"""
    tone_mapping = {
        ("технічна_дискусія", "задумливий"): "розумний_абсурд",
        ("технічна_дискусія", "позитивний"): "підтримуючий_жарт",
        ("філософська_розмова", "задумливий"): "глибокий_абсурд",
        ("філософська_розмова", "позитивний"): "мудрий_гумор",
        ("жарти_мемі", "позитивний"): "веселий_абсурд",
        ("жарти_мемі", "збуджений"): "енергійний_гумор",
        ("емоційна_розмова", "негативний"): "підтримуючий_абсурд",
        ("емоційна_розмова", "позитивний"): "радісний_гумор",
        ("конфлікт", "негативний"): "розряджаючий_абсурд",
        ("побутова_розмова", "нейтральний"): "легкий_гумор"
    }
    
    return tone_mapping.get((conv_type, mood), "стандартний_абсурд")

def extract_context_keywords(text: str) -> List[str]:
    """Витягує ключові слова з контексту для кращого розуміння"""
    # Прості ключові слова
    words = re.findall(r'\b\w{4,}\b', text.lower())
    
    # Фільтруємо стоп-слова
    stop_words = {"який", "яка", "яке", "який", "цей", "ця", "це", "той", "та", "те", "мене", "тебе", "його", "неї", "нас", "вас", "них"}
    keywords = [word for word in words if word not in stop_words]
    
    # Повертаємо топ-5 найдовших слів як ключові
    return sorted(set(keywords), key=len, reverse=True)[:5]

def update_chat_mood_history(chat_id: int, mood: str, conversation_type: str):
    """Оновлює історію настроїв чату"""
    timestamp = datetime.now().timestamp()
    
    # Зберігаємо тільки останні 50 записів
    chat_moods[chat_id].append((timestamp, mood))
    chat_moods[chat_id] = chat_moods[chat_id][-50:]
    
    chat_topics[chat_id].append((timestamp, conversation_type))
    chat_topics[chat_id] = chat_topics[chat_id][-50:]

def get_chat_mood_trend(chat_id: int, hours: int = 24) -> Dict:
    """Аналізує тенденції настрою чату за останні години"""
    current_time = datetime.now().timestamp()
    cutoff_time = current_time - (hours * 3600)
    
    recent_moods = [mood for timestamp, mood in chat_moods[chat_id] if timestamp > cutoff_time]
    recent_topics = [topic for timestamp, topic in chat_topics[chat_id] if timestamp > cutoff_time]
    
    if not recent_moods:
        return {"dominant_mood": "невідомий", "dominant_topic": "невідомий", "trend": "стабільний"}
    
    # Найпопулярніший настрій
    mood_counts = defaultdict(int)
    for mood in recent_moods:
        mood_counts[mood] += 1
    dominant_mood = max(mood_counts, key=mood_counts.get)
    
    # Найпопулярніша тема
    topic_counts = defaultdict(int)
    for topic in recent_topics:
        topic_counts[topic] += 1
    dominant_topic = max(topic_counts, key=topic_counts.get)
    
    # Тенденція (порівнюємо першу та другу половину періоду)
    mid_point = len(recent_moods) // 2
    if mid_point > 0:
        first_half = recent_moods[:mid_point]
        second_half = recent_moods[mid_point:]
        
        positive_moods = {"позитивний", "збуджений"}
        first_half_positive = sum(1 for mood in first_half if mood in positive_moods)
        second_half_positive = sum(1 for mood in second_half if mood in positive_moods)
        
        if second_half_positive > first_half_positive:
            trend = "покращення"
        elif second_half_positive < first_half_positive:
            trend = "погіршення"
        else:
            trend = "стабільний"
    else:
        trend = "стабільний"
    
    return {
        "dominant_mood": dominant_mood,
        "dominant_topic": dominant_topic,
        "trend": trend,
        "activity_level": len(recent_moods)
    }

def generate_context_aware_prompt(message_text: str, chat_analysis: Dict, chat_trend: Dict) -> str:
    """Генерує промт для Gemini з урахуванням контексту та аналізу"""
    base_prompt = f"Ти — Гряг, абсурдний дух чату з дотепним гумором."
    
    # Додаємо контекст поточної розмови
    context_info = f"""
Поточна ситуація:
- Тип розмови: {chat_analysis.get('type', 'невідомий')}
- Настрій: {chat_analysis.get('mood', 'нейтральний')}
- Рівень залученості (1-10): {chat_analysis.get('engagement_level', 5)}
- Рекомендований тон: {chat_analysis.get('suggested_tone', 'стандартний_абсурд')}

Тенденції чату:
- Домінуючий настрій: {chat_trend.get('dominant_mood', 'невідомий')}
- Основна тема: {chat_trend.get('dominant_topic', 'невідомий')}
- Тенденція: {chat_trend.get('trend', 'стабільний')}
- Рівень активності: {chat_trend.get('activity_level', 0)}

Повідомлення користувача: "{message_text}"
"""
    
    # Налаштовуємо стиль відповіді
    tone_instructions = {
        "розумний_абсурд": "Відповідай розумно, але з абсурдними аналогіями та несподіваними висновками.",
        "підтримуючий_жарт": "Підтримай розмову легким гумором та дотепними коментарями.",
        "глибокий_абсурд": "Філософствуй абсурдно, ставь дивні питання та роби несподівані зв'язки.",
        "веселий_абсурд": "Будь максимально смішним та абсурдним, підтримай веселощі.",
        "підтримуючий_абсурд": "Підтримай, але абсурдним способом, розвесели ситуацію.",
        "розряджаючий_абсурд": "Розрядь напругу абсурдним коментарем або несподіваною темою."
    }
    
    tone_instruction = tone_instructions.get(
        chat_analysis.get('suggested_tone', 'стандартний_абсурд'),
        "Відповідай у своєму звичному абсурдному стилі."
    )
    
    return f"{base_prompt}\n{context_info}\n\nІнструкція: {tone_instruction}\n\nВідповідай коротко (1-2 речення), дотепно та по-українськи."
