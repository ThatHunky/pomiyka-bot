# Модуль для передбачення та аналізу ситуацій в чаті
import re
import random
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any
from bot.bot_config import PERSONA

# Спроба імпорту локального аналізатора
try:
    from .local_analyzer import get_analyzer, get_conversation_context, analyze_text_local
    LOCAL_ANALYZER_AVAILABLE = True
except ImportError:
    LOCAL_ANALYZER_AVAILABLE = False

# Патерни для розпізнавання типів розмов (fallback для випадків без локального аналізатора)
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

async def analyze_message_context_enhanced(message_text: str, chat_history: List[Dict[str, Any]], chat_id: int = 0) -> Dict[str, Any]:
    """Покращений аналіз контексту повідомлення з використанням локального аналізатора"""
    if not message_text:
        return {"type": "unknown", "mood": "neutral", "prediction": "continue"}
    
    # Якщо доступний локальний аналізатор - використовуємо його
    if LOCAL_ANALYZER_AVAILABLE:
        try:
            # Отримуємо локальний аналіз
            local_analysis = await analyze_text_local(message_text)
            
            # Отримуємо контекст розмови
            conversation_context = await get_conversation_context(chat_id, chat_history[-10:] if chat_history else [], hours=6)
            
            # Перетворюємо результати локального аналізу в формат, сумісний з існуючим кодом
            return {
                "type": _map_topic_to_conversation_type(local_analysis.get("topic", "загальне")),
                "mood": _map_emotion_to_mood(local_analysis.get("emotion", "нейтральний")),
                "prediction": _predict_from_local_analysis(local_analysis, conversation_context),
                "engagement_level": _calculate_engagement_from_local(local_analysis, message_text),
                "should_intervene": _should_intervene_from_local(local_analysis, conversation_context),
                "suggested_tone": _get_tone_from_local(local_analysis),
                "context_keywords": local_analysis.get("keywords", []),
                "local_confidence": local_analysis.get("confidence", 0.5),
                "conversation_summary": conversation_context.get("recommended_for_gemini", ""),
                "analysis_method": "enhanced_local"
            }
        except Exception as e:
            # Fallback на стандартний аналіз при помилці
            return analyze_message_context_fallback(message_text, chat_history)
    
    # Fallback на стандартний аналіз
    return analyze_message_context_fallback(message_text, chat_history)

def _map_topic_to_conversation_type(topic: str) -> str:
    """Мапінг тем з локального аналізатора на типи розмов"""
    topic_mapping = {
        "технології": "технічна_дискусія",
        "робота_навчання": "технічна_дискусія", 
        "повсякденне": "побутова_розмова",
        "розваги": "жарти_мемі",
        "погода_природа": "побутова_розмова",
        "відносини": "емоційна_розмова"
    }
    return topic_mapping.get(topic, "загальна_розмова")

def _map_emotion_to_mood(emotion: str) -> str:
    """Мапінг емоцій з локального аналізатора на настрої"""
    emotion_mapping = {
        "радість": "позитивний",
        "сум": "негативний", 
        "злість": "негативний",
        "страх": "негативний",
        "здивування": "збуджений",
        "відраза": "негативний",
        "нейтральний": "нейтральний"
    }
    return emotion_mapping.get(emotion, "нейтральний")

def _predict_from_local_analysis(local_analysis: Dict[str, Any], conversation_context: Dict[str, Any]) -> str:
    """Передбачає розвиток розмови на основі локального аналізу"""
    confidence = local_analysis.get("confidence", 0.5)
    emotion = local_analysis.get("emotion", "нейтральний")
    topic = local_analysis.get("topic", "загальне")
    
    # Високий рівень впевненості + емоційність = активна реакція
    if confidence > 0.7 and emotion in ["радість", "злість", "здивування"]:
        return "емоційна_реакція"
    
    # Технічні теми зазвичай розвиваються
    if topic == "технології":
        return "розвиток_теми"
    
    # Аналізуємо контекст розмови
    current_conv = conversation_context.get("current_conversation", {})
    if current_conv.get("message_count", 0) > 5:
        return "активна_дискусія"
    
    return "продовження"

def _calculate_engagement_from_local(local_analysis: Dict[str, Any], message_text: str) -> int:
    """Розраховує рівень залученості на основі локального аналізу"""
    base_level = 3
    
    # Додаємо впевненість аналізу
    confidence = local_analysis.get("confidence", 0.5)
    base_level += int(confidence * 4)
    
    # Емоційність
    emotion = local_analysis.get("emotion", "нейтральний")
    if emotion in ["радість", "здивування"]:
        base_level += 2
    elif emotion in ["сум", "злість"]:
        base_level += 1
    
    # Тема
    topic = local_analysis.get("topic", "загальне")
    if topic in ["технології", "відносини"]:
        base_level += 2
    
    # Згадки бота
    text_lower = message_text.lower()
    if any(trigger.strip() in text_lower for trigger in PERSONA["trigger_keywords"]):
        base_level += 4
    
    return max(1, min(10, base_level))

def _should_intervene_from_local(local_analysis: Dict[str, Any], conversation_context: Dict[str, Any]) -> bool:
    """Визначає необхідність втручання на основі локального аналізу"""
    confidence = local_analysis.get("confidence", 0.5)
    emotion = local_analysis.get("emotion", "нейтральний")
    topic = local_analysis.get("topic", "загальне")
    
    # Висока впевненість + цікава тема
    if confidence > 0.8 and topic in ["технології", "відносини"]:
        return True
    
    # Сильні емоції
    if emotion in ["злість", "сум"] and confidence > 0.6:
        return True
    
    # Аналізуємо контекст - довга тиша
    historical = conversation_context.get("historical_context", {})
    if historical.get("total_messages", 0) < 5:  # Мало повідомлень = тиша
        return random.random() < 0.3
    
    return False

def _get_tone_from_local(local_analysis: Dict[str, Any]) -> str:
    """Визначає тон відповіді на основі локального аналізу"""
    emotion = local_analysis.get("emotion", "нейтральний")
    topic = local_analysis.get("topic", "загальне")
    confidence = local_analysis.get("confidence", 0.5)
    
    if topic == "технології" and confidence > 0.7:
        return "корисний_коментар"
    elif emotion == "радість":
        return "дружелюбна_підтримка" 
    elif emotion in ["сум", "злість"]:
        return "підтримка_та_розуміння"
    elif topic == "розваги":
        return "легкий_гумор"
    else:
        return "природне_спілкування"

def analyze_message_context_fallback(message_text: str, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Стандартна функція аналізу контексту повідомлення (fallback)"""
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
        "context_keywords": extract_context_keywords(text),
        "analysis_method": "regex_fallback"
    }

# Обгортка для зворотної сумісності
def analyze_message_context(message_text: str, chat_history: List[Dict[str, Any]], chat_id: int = 0) -> Dict[str, Any]:
    """Аналізує контекст повідомлення з можливістю використання локального аналізатора"""
    # Використовуємо async версію якщо можливо
    try:
        import asyncio
        if asyncio.iscoroutinefunction(analyze_message_context_enhanced):
            # Якщо ми в async контексті, використовуємо enhanced версію
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Якщо цикл вже запущений, створюємо task
                    task = asyncio.create_task(analyze_message_context_enhanced(message_text, chat_history, chat_id))
                    # Для синхронного виклику повертаємо fallback
                    return analyze_message_context_fallback(message_text, chat_history)
                else:
                    # Якщо циклу немає, запускаємо синхронно
                    return asyncio.run(analyze_message_context_enhanced(message_text, chat_history, chat_id))
            except:
                pass
    except:
        pass
    
    # Fallback на стандартний аналіз
    return analyze_message_context_fallback(message_text, chat_history)
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
        ("технічна_дискусія", "задумливий"): "корисний_коментар",
        ("технічна_дискусія", "позитивний"): "дружелюбна_підтримка",
        ("філософська_розмова", "задумливий"): "мудра_думка",
        ("філософська_розмова", "позитивний"): "цікаві_роздуми",
        ("жарти_мемі", "позитивний"): "легкий_гумор",
        ("жарти_мемі", "збуджений"): "веселий_настрій",
        ("емоційна_розмова", "негативний"): "підтримка_та_розуміння",
        ("емоційна_розмова", "позитивний"): "щира_радість",
        ("конфлікт", "негативний"): "дипломатичне_заспокоєння",
        ("побутова_розмова", "нейтральний"): "дружелюбна_розмова"
    }
    
    return tone_mapping.get((conv_type, mood), "природне_спілкування")

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
    base_prompt = f"Ти — Гряг, звичайний дружелюбний чат-бот з дуже легким гумором."
    
    # Додаємо контекст поточної розмови
    context_info = f"""
Поточна ситуація:
- Тип розмови: {chat_analysis.get('type', 'невідомий')}
- Настрій: {chat_analysis.get('mood', 'нейтральний')}
- Рівень залученості (1-10): {chat_analysis.get('engagement_level', 5)}
- Рекомендований тон: {chat_analysis.get('suggested_tone', 'дружелюбний')}

Тенденції чату:
- Домінуючий настрій: {chat_trend.get('dominant_mood', 'невідомий')}
- Основна тема: {chat_trend.get('dominant_topic', 'невідомий')}
- Тенденція: {chat_trend.get('trend', 'стабільний')}
- Рівень активності: {chat_trend.get('activity_level', 0)}

Повідомлення користувача: "{message_text}"
"""
    
    # Налаштовуємо стиль відповіді
    tone_instructions = {
        "розумний_жарт": "Відповідай розумно та по справі, коли доречно — додай легкий жарт.",
        "підтримуючий_жарт": "Підтримай розмову дружелюбним коментарем.",
        "дружелюбний_жарт": "Будь дружелюбним і приємним у спілкуванні.",
        "веселий_жарт": "Будь дружелюбним та підтримай розмову.",
        "підтримуючий": "Підтримай і допоможи в ситуації.",
        "розряджаючий": "Спробуй розрядити ситуацію спокійним коментарем."
    }
    
    tone_instruction = tone_instructions.get(
        chat_analysis.get('suggested_tone', 'дружелюбний_жарт'),
        "Відповідай у дружелюбному стилі."
    )
    
    return f"{base_prompt}\n{context_info}\n\nІнструкція: {tone_instruction}\n\nВідповідай коротко (1-2 речення), дотепно та по-українськи."

# Покращені функції з використанням локального аналізатора

async def generate_enhanced_context_prompt(message_text: str, chat_id: int, chat_history: List[Dict[str, Any]]) -> str:
    """Генерує покращений промт з використанням локального аналізатора"""
    if LOCAL_ANALYZER_AVAILABLE:
        try:
            # Отримуємо повний аналіз з локального аналізатора
            context_data = await get_conversation_context(chat_id, chat_history[-15:] if chat_history else [], hours=12)
            
            base_prompt = "Ти — Гряг, дружелюбний український чат-бот з легким гумором."
            
            # Використовуємо готовий контекст від локального аналізатора
            gemini_context = context_data.get("recommended_for_gemini", "")
            
            if gemini_context:
                context_info = f"\nКонтекст розмови: {gemini_context}"
            else:
                context_info = "\nСтандартна розмова в чаті."
            
            # Визначаємо стиль відповіді
            current_analysis = context_data.get("current_conversation", {})
            dominant_emotion = current_analysis.get("dominant_emotion", "нейтральний")
            main_topics = current_analysis.get("main_topics", [])
            
            style_instruction = _get_style_instruction(dominant_emotion, main_topics, message_text)
            
            return f"{base_prompt}{context_info}\n\n{style_instruction}\n\nВідповідай коротко та природно українською мовою."
            
        except Exception as e:
            # Fallback на стандартний генератор
            analysis = analyze_message_context_fallback(message_text, chat_history)
            return generate_context_aware_prompt(message_text, analysis, {})
    
    # Fallback для випадку без локального аналізатора
    analysis = analyze_message_context_fallback(message_text, chat_history)
    return generate_context_aware_prompt(message_text, analysis, {})

def _get_style_instruction(emotion: str, topics: List[str], message_text: str) -> str:
    """Визначає стиль інструкції на основі емоції та тем"""
    text_lower = message_text.lower()
    
    # Перевіряємо згадки бота
    bot_mentioned = any(trigger.strip() in text_lower for trigger in PERSONA.get("trigger_keywords", []))
    
    if bot_mentioned:
        return "Ти згаданий в повідомленні - відповідай активно та дружелюбно."
    
    # На основі емоцій
    if emotion == "радість":
        return "Підтримай веселий настрій дружелюбним коментарем."
    elif emotion in ["сум", "злість"]:
        return "Будь тактовним та підтримуючим."
    elif emotion == "збуджений":
        return "Підтримай енергійний настрій розмови."
    
    # На основі тем
    if topics and len(topics) > 0:
        main_topic = topics[0]
        if main_topic == "технології":
            return "Це технічна тема - можеш бути корисним та розумним."
        elif main_topic == "розваги":
            return "Розважальна тема - можна жартувати та бути веселим."
        elif main_topic == "побутова_розмова":
            return "Побутова розмова - будь природним та дружелюбним."
    
    return "Відповідай природно та дружелюбно."

# Функція для перевірки доступності локального аналізатора
def is_local_analyzer_available() -> bool:
    """Перевіряє доступність локального аналізатора"""
    return LOCAL_ANALYZER_AVAILABLE

# Функція для отримання статистики локального аналізатора
async def get_local_analyzer_stats() -> Dict[str, Any]:
    """Отримує статистику роботи локального аналізатора"""
    if not LOCAL_ANALYZER_AVAILABLE:
        return {"status": "unavailable"}
    
    try:
        analyzer = get_analyzer()
        # Тут можна додати більше статистики від аналізатора
        return {
            "status": "available",
            "model_loaded": analyzer.model is not None,
            "nlp_loaded": analyzer.nlp is not None,
            "cache_size": len(analyzer.analysis_cache),
            "batch_size": analyzer.batch_size
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Функція очищення для періодичного використання
async def cleanup_local_analyzer(days: int = 7):
    """Очищує дані локального аналізатора"""
    if LOCAL_ANALYZER_AVAILABLE:
        try:
            analyzer = get_analyzer()
            analyzer.cleanup_old_data(days)
            return True
        except Exception as e:
            return False
    return False
