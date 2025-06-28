# Локальний аналізатор для розмов - оптимізовано для i5-6500, 16GB RAM
import json
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
import re
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers не встановлено. Буде використано fallback аналіз.")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy не встановлено. Деякі функції будуть недоступні.")

from bot.bot_config import *

class LocalAnalyzer:
    """Локальний аналізатор розмов з оптимізацією для обмежених ресурсів"""
    
    def __init__(self, db_path: str = "data/analysis_cache.db"):
        self.db_path = db_path
        self.model = None
        self.nlp = None
        self.embedding_cache = {}
        self.analysis_cache = {}
        self.batch_size = 5  # Оптимально для i5-6500
        
        # Ініціалізація бази даних для кешування
        self._init_database()
        
        # Завантаження моделей
        self._load_models()
        
        # Емоційні словники для швидкого аналізу
        self._init_emotion_dictionaries()
        
        # Тематичні ключові слова
        self._init_topic_keywords()

    def _init_database(self):
        """Ініціалізація бази даних для кешування"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблиця для кешування векторних представлень
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings_cache (
                    text_hash TEXT PRIMARY KEY,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця для кешування аналізу
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    text_hash TEXT PRIMARY KEY,
                    emotion TEXT,
                    topic TEXT,
                    confidence REAL,
                    keywords TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця для збереження підсумків розмов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    chat_id INTEGER,
                    time_period TEXT,
                    summary TEXT,
                    dominant_emotion TEXT,
                    main_topics TEXT,
                    participants_count INTEGER,
                    message_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, time_period)
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("База даних локального аналізатора ініціалізована")
            
        except Exception as e:
            logging.error(f"Помилка ініціалізації бази даних: {e}")

    def _load_models(self):
        """Завантаження локальних моделей з обробкою помилок"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # Легка багатомовна модель, оптимізована для CPU
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logging.info("Sentence Transformer модель завантажена")
            
            if SPACY_AVAILABLE:
                try:
                    # Спробуємо завантажити українську модель
                    self.nlp = spacy.load("uk_core_news_sm")
                    logging.info("spaCy українська модель завантажена")
                except OSError:
                    # Fallback на англійську модель
                    try:
                        self.nlp = spacy.load("en_core_web_sm")
                        logging.info("spaCy англійська модель завантажена як fallback")
                    except OSError:
                        logging.warning("Жодна spaCy модель не доступна")
                        
        except Exception as e:
            logging.error(f"Помилка завантаження моделей: {e}")

    def _init_emotion_dictionaries(self):
        """Ініціалізація словників емоцій для швидкого аналізу"""
        self.emotion_words = {
            "радість": [
                "радий", "радість", "щасливий", "щастя", "веселий", "весело", "круто", "класно", 
                "супер", "чудово", "прекрасно", "відмінно", "ура", "вау", "😊", "😃", "😄", 
                "😁", "😆", "😂", "🤣", "😍", "🥰", "❤️", "👍", "🔥", "🎉", "🥳"
            ],
            "сум": [
                "сумно", "сум", "грустно", "плачу", "засмучений", "гірко", "жаль", "жалко",
                "печально", "меланхолія", "😢", "😭", "😔", "😞", "😟", "😥", "😪", "💔", "😿"
            ],
            "злість": [
                "злий", "злість", "бісний", "роздратований", "дратує", "нервує", "лють", "гнів",
                "обурений", "лайно", "фігня", "дурниця", "😡", "😠", "🤬", "👎", "💩", "🖕"
            ],
            "страх": [
                "боюсь", "страх", "страшно", "лякає", "тривога", "хвилювання", "нервую", 
                "переживаю", "панікую", "😨", "😰", "😱", "😧", "😦", "😟"
            ],
            "здивування": [
                "ого", "вау", "неймовірно", "дивовижно", "шок", "шокує", "вражає", "капець",
                "не може бути", "😮", "😯", "😲", "🤯", "😱", "🙄"
            ],
            "відраза": [
                "фу", "огидно", "бридко", "противно", "ненавиджу", "гидота", "мерзота",
                "🤢", "🤮", "😷", "🤧", "😖", "😣"
            ]
        }

    def _init_topic_keywords(self):
        """Ініціалізація ключових слів для визначення тем"""
        self.topic_keywords = {
            "технології": [
                "код", "програма", "програмування", "алгоритм", "функція", "змінна", "клас",
                "python", "javascript", "java", "react", "node", "git", "github", "api", "json",
                "сервер", "база", "даних", "sql", "mongodb", "docker", "linux", "windows"
            ],
            "робота_навчання": [
                "робота", "офіс", "проект", "завдання", "дедлайн", "презентація", "звіт",
                "університет", "навчання", "екзамен", "сесія", "диплом", "курсова", "лекція"
            ],
            "повсякденне": [
                "їжа", "готую", "обід", "вечеря", "сніданок", "кухня", "рецепт", "смачно",
                "дім", "квартира", "прибирання", "покупки", "магазин", "транспорт", "дорога"
            ],
            "розваги": [
                "фільм", "серіал", "музика", "пісня", "гра", "ігра", "спорт", "футбол", "кіно",
                "театр", "концерт", "книга", "читаю", "мандрівка", "подорож", "відпустка"
            ],
            "погода_природа": [
                "погода", "дощ", "сонце", "сніг", "вітер", "тепло", "холодно", "літо", "зима",
                "весна", "осінь", "природа", "ліс", "море", "гори", "парк"
            ],
            "відносини": [
                "любов", "стосунки", "дівчина", "хлопець", "дружба", "друзі", "сім'я", "мама",
                "тато", "родичі", "одруження", "весілля", "діти", "кохання"
            ]
        }

    def get_text_hash(self, text: str) -> str:
        """Генерує хеш для тексту для кешування"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get_cached_analysis(self, text: str) -> Optional[Dict[str, Any]]:
        """Отримує закешований аналіз тексту"""
        text_hash = self.get_text_hash(text)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT emotion, topic, confidence, keywords 
                FROM analysis_cache 
                WHERE text_hash = ? AND created_at > datetime('now', '-24 hours')
            ''', (text_hash,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "emotion": result[0],
                    "topic": result[1],
                    "confidence": result[2],
                    "keywords": json.loads(result[3]) if result[3] else []
                }
                
        except Exception as e:
            logging.error(f"Помилка отримання кешу: {e}")
            
        return None

    def cache_analysis(self, text: str, analysis: Dict[str, Any]):
        """Зберігає результат аналізу в кеш"""
        text_hash = self.get_text_hash(text)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO analysis_cache 
                (text_hash, emotion, topic, confidence, keywords)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                text_hash,
                analysis.get("emotion", "нейтральний"),
                analysis.get("topic", "загальне"),
                analysis.get("confidence", 0.5),
                json.dumps(analysis.get("keywords", []))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Помилка збереження в кеш: {e}")

    def analyze_emotion_fast(self, text: str) -> Tuple[str, float]:
        """Швидкий аналіз емоцій за ключовими словами"""
        text_lower = text.lower()
        emotion_scores = defaultdict(float)
        
        for emotion, words in self.emotion_words.items():
            score = 0
            for word in words:
                if word in text_lower:
                    # Емодзі мають більшу вагу
                    weight = 2 if any(ord(char) > 127 for char in word) else 1
                    score += weight
            
            if score > 0:
                emotion_scores[emotion] = score / len(words)
        
        if emotion_scores:
            dominant_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = min(emotion_scores[dominant_emotion] * 2, 1.0)
            return dominant_emotion, confidence
        
        return "нейтральний", 0.3

    def analyze_topic_fast(self, text: str) -> Tuple[str, float]:
        """Швидкий аналіз теми за ключовими словами"""
        text_lower = text.lower()
        topic_scores = defaultdict(float)
        
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                topic_scores[topic] = score / len(keywords)
        
        if topic_scores:
            dominant_topic = max(topic_scores, key=topic_scores.get)
            confidence = min(topic_scores[dominant_topic] * 3, 1.0)
            return dominant_topic, confidence
        
        return "загальне", 0.3

    def extract_keywords_simple(self, text: str) -> List[str]:
        """Проста екстракція ключових слів"""
        # Видаляємо пунктуацію та розбиваємо на слова
        words = re.findall(r'\b[а-яёії]{3,}\b', text.lower())
        
        # Стоп-слова
        stop_words = {
            "що", "який", "яка", "яке", "який", "цей", "ця", "це", "той", "та", "те",
            "мене", "тебе", "його", "неї", "нас", "вас", "них", "для", "про", "при",
            "над", "під", "між", "без", "через", "після", "перед", "вже", "ще", "дуже",
            "тому", "тільки", "також", "може", "можна", "треба", "буде", "була", "було"
        }
        
        # Фільтруємо стоп-слова та повертаємо найчастіші
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        word_counts = Counter(filtered_words)
        
        return [word for word, count in word_counts.most_common(5)]

    async def analyze_message(self, text: str, use_cache: bool = True) -> Dict[str, Any]:
        """Основна функція аналізу повідомлення"""
        if not text or len(text.strip()) < 3:
            return {
                "emotion": "нейтральний",
                "topic": "загальне", 
                "confidence": 0.1,
                "keywords": [],
                "analysis_method": "minimal"
            }
        
        # Перевіряємо кеш
        if use_cache:
            cached = self.get_cached_analysis(text)
            if cached:
                cached["analysis_method"] = "cached"
                return cached
        
        # Швидкий аналіз
        emotion, emotion_conf = self.analyze_emotion_fast(text)
        topic, topic_conf = self.analyze_topic_fast(text)
        keywords = self.extract_keywords_simple(text)
        
        # Середня впевненість
        avg_confidence = (emotion_conf + topic_conf) / 2
        
        analysis = {
            "emotion": emotion,
            "topic": topic,
            "confidence": avg_confidence,
            "keywords": keywords,
            "analysis_method": "fast_local"
        }
        
        # Якщо доступні нейронні мережі та впевненість низька - використовуємо їх
        if self.model and avg_confidence < 0.6:
            try:
                enhanced_analysis = await self._analyze_with_transformers(text, analysis)
                analysis.update(enhanced_analysis)
                analysis["analysis_method"] = "enhanced_local"
            except Exception as e:
                logging.warning(f"Помилка enhanced аналізу: {e}")
        
        # Зберігаємо в кеш
        if use_cache:
            self.cache_analysis(text, analysis)
        
        return analysis

    async def _analyze_with_transformers(self, text: str, base_analysis: Dict) -> Dict[str, Any]:
        """Покращений аналіз з використанням transformer моделей"""
        if not self.model:
            return {}
        
        try:
            # Генеруємо ембеддінг для тексту
            embedding = self.model.encode([text])[0]
            
            # Порівнюємо з еталонними ембеддінгами емоцій (спрощена версія)
            emotion_examples = {
                "радість": "Як же я щасливий! Це неймовірно круто!",
                "сум": "Мені так сумно і гірко на душі",
                "злість": "Це просто бісить! Яка фігня!",
                "нейтральний": "Сьогодні звичайний день, нічого особливого"
            }
            
            emotion_similarities = {}
            for emotion, example in emotion_examples.items():
                example_embedding = self.model.encode([example])[0]
                similarity = np.dot(embedding, example_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(example_embedding)
                )
                emotion_similarities[emotion] = similarity
            
            # Якщо нейронка дає кращий результат - оновлюємо
            best_emotion = max(emotion_similarities, key=emotion_similarities.get)
            best_similarity = emotion_similarities[best_emotion]
            
            if best_similarity > 0.7 and best_similarity > base_analysis["confidence"]:
                return {
                    "emotion": best_emotion,
                    "confidence": min(best_similarity, 0.95)
                }
                
        except Exception as e:
            logging.error(f"Помилка transformer аналізу: {e}")
        
        return {}

    async def analyze_conversation_batch(self, messages: List[Dict[str, Any]], chat_id: int) -> Dict[str, Any]:
        """Аналіз пакету повідомлень для розуміння контексту розмови"""
        if not messages:
            return {"summary": "Порожня розмова", "dominant_emotion": "нейтральний", "main_topics": []}
        
        # Аналізуємо кожне повідомлення
        analyses = []
        for message in messages[-self.batch_size:]:  # Беремо останні N повідомлень
            text = message.get("text", "")
            if text:
                analysis = await self.analyze_message(text)
                analyses.append(analysis)
        
        if not analyses:
            return {"summary": "Немає текстових повідомлень", "dominant_emotion": "нейтральний", "main_topics": []}
        
        # Збираємо статистику
        emotions = [a["emotion"] for a in analyses]
        topics = [a["topic"] for a in analyses]
        all_keywords = []
        for a in analyses:
            all_keywords.extend(a["keywords"])
        
        # Домінуюча емоція
        emotion_counts = Counter(emotions)
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "нейтральний"
        
        # Основні теми
        topic_counts = Counter(topics)
        main_topics = [topic for topic, count in topic_counts.most_common(3)]
        
        # Ключові слова
        keyword_counts = Counter(all_keywords)
        top_keywords = [kw for kw, count in keyword_counts.most_common(5)]
        
        # Генеруємо короткий опис
        summary = self._generate_conversation_summary(messages, dominant_emotion, main_topics, top_keywords)
        
        result = {
            "summary": summary,
            "dominant_emotion": dominant_emotion,
            "main_topics": main_topics,
            "top_keywords": top_keywords,
            "message_count": len(messages),
            "analyzed_count": len(analyses),
            "emotion_distribution": dict(emotion_counts),
            "topic_distribution": dict(topic_counts)
        }
        
        # Зберігаємо підсумок в БД
        self._save_conversation_summary(chat_id, result)
        
        return result

    def _generate_conversation_summary(self, messages: List[Dict], emotion: str, topics: List[str], keywords: List[str]) -> str:
        """Генерує короткий опис розмови"""
        participants = set()
        for msg in messages:
            user = msg.get("user", "")
            if user:
                participants.add(user)
        
        participant_count = len(participants)
        message_count = len(messages)
        
        # Базовий опис
        if message_count == 1:
            base = "Одне повідомлення"
        elif message_count < 5:
            base = f"Коротка розмова ({message_count} повідомлень)"
        else:
            base = f"Активна розмова ({message_count} повідомлень)"
        
        # Додаємо інформацію про учасників
        if participant_count > 1:
            base += f" між {participant_count} учасниками"
        
        # Додаємо емоційний контекст
        emotion_desc = {
            "радість": "з веселим настроєм",
            "сум": "з сумним відтінком", 
            "злість": "з напруженою атмосферою",
            "здивування": "з елементами здивування",
            "нейтральний": "в спокійному тоні"
        }
        base += f" {emotion_desc.get(emotion, 'в нейтральному тоні')}"
        
        # Додаємо тематику
        if topics and topics[0] != "загальне":
            if len(topics) == 1:
                base += f". Тема: {topics[0]}"
            else:
                base += f". Теми: {', '.join(topics[:2])}"
        
        # Додаємо ключові слова якщо вони цікаві
        interesting_keywords = [kw for kw in keywords if len(kw) > 4]
        if interesting_keywords:
            base += f". Ключові слова: {', '.join(interesting_keywords[:3])}"
        
        return base

    def _save_conversation_summary(self, chat_id: int, summary_data: Dict[str, Any]):
        """Зберігає підсумок розмови в базу даних"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            time_period = datetime.now().strftime("%Y-%m-%d_%H")  # Година як період
            
            cursor.execute('''
                INSERT OR REPLACE INTO conversation_summaries
                (chat_id, time_period, summary, dominant_emotion, main_topics, 
                 participants_count, message_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                chat_id,
                time_period,
                summary_data["summary"],
                summary_data["dominant_emotion"],
                json.dumps(summary_data["main_topics"]),
                summary_data.get("participants_count", 1),
                summary_data["message_count"]
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Помилка збереження підсумку: {e}")

    def get_chat_context_summary(self, chat_id: int, hours: int = 24) -> Dict[str, Any]:
        """Отримує підсумок контексту чату за останні години"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Отримуємо підсумки за останні години
            cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d_%H")
            
            cursor.execute('''
                SELECT summary, dominant_emotion, main_topics, message_count
                FROM conversation_summaries
                WHERE chat_id = ? AND time_period >= ?
                ORDER BY time_period DESC
            ''', (chat_id, cutoff_time))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return {
                    "status": "no_data",
                    "summary": "Немає даних про розмову",
                    "dominant_emotions": [],
                    "main_topics": [],
                    "total_messages": 0
                }
            
            # Аналізуємо зібрані дані
            all_emotions = []
            all_topics = []
            total_messages = 0
            summaries = []
            
            for result in results:
                summary, emotion, topics_json, msg_count = result
                summaries.append(summary)
                all_emotions.append(emotion)
                
                try:
                    topics = json.loads(topics_json)
                    all_topics.extend(topics)
                except:
                    pass
                    
                total_messages += msg_count
            
            # Статистика
            emotion_counts = Counter(all_emotions)
            topic_counts = Counter(all_topics)
            
            return {
                "status": "success",
                "summary": f"За останні {hours} годин: {total_messages} повідомлень",
                "detailed_summaries": summaries[:3],  # Останні 3 підсумки
                "dominant_emotions": [e for e, c in emotion_counts.most_common(3)],
                "main_topics": [t for t, c in topic_counts.most_common(5)],
                "total_messages": total_messages,
                "analysis_periods": len(results)
            }
            
        except Exception as e:
            logging.error(f"Помилка отримання контексту: {e}")
            return {
                "status": "error",
                "summary": "Помилка отримання контексту",
                "dominant_emotions": [],
                "main_topics": [],
                "total_messages": 0
            }

    def cleanup_old_data(self, days: int = 7):
        """Очищення старих даних для економії місця"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Очищаємо старі кеші
            cursor.execute('DELETE FROM embeddings_cache WHERE created_at < ?', (cutoff_date,))
            cursor.execute('DELETE FROM analysis_cache WHERE created_at < ?', (cutoff_date,))
            
            # Очищаємо старі підсумки (залишаємо більше часу)
            old_cutoff = datetime.now() - timedelta(days=days*2)
            cursor.execute('DELETE FROM conversation_summaries WHERE created_at < ?', (old_cutoff,))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Видалено дані старше {days} днів")
            
        except Exception as e:
            logging.error(f"Помилка очищення даних: {e}")

    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Простий аналіз настрою тексту."""
        # Швидкий аналіз на основі ключових слів
        positive_words = ["добре", "чудово", "класно", "супер", "відмінно", "гарно", "круто", "👍", "❤️", "😊"]
        negative_words = ["погано", "жахливо", "сумно", "дратує", "біситьv", "👎", "😢", "😡"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "позитивний"
            score = 0.7
        elif negative_count > positive_count:
            sentiment = "негативний" 
            score = 0.3
        else:
            sentiment = "нейтральний"
            score = 0.5
            
        return {
            "sentiment": sentiment,
            "score": score,
            "positive_count": positive_count,
            "negative_count": negative_count
        }

# Глобальний екземпляр аналізатора
_analyzer_instance = None

def get_analyzer() -> LocalAnalyzer:
    """Отримує глобальний екземпляр аналізатора (Singleton)"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = LocalAnalyzer()
    return _analyzer_instance

# Допоміжні функції для інтеграції з існуючим кодом
async def analyze_text_local(text: str) -> Dict[str, Any]:
    """Швидкий локальний аналіз тексту"""
    analyzer = get_analyzer()
    return await analyzer.analyze_message(text)

async def get_conversation_context(chat_id: int, messages: List[Dict], hours: int = 24) -> Dict[str, Any]:
    """Отримує контекст розмови для передачі в Gemini"""
    analyzer = get_analyzer()
    
    # Аналізуємо поточний батч повідомлень
    current_analysis = await analyzer.analyze_conversation_batch(messages, chat_id)
    
    # Отримуємо історичний контекст
    historical_context = analyzer.get_chat_context_summary(chat_id, hours)
    
    return {
        "current_conversation": current_analysis,
        "historical_context": historical_context,
        "recommended_for_gemini": _prepare_gemini_context(current_analysis, historical_context)
    }

def _prepare_gemini_context(current: Dict, historical: Dict) -> str:
    """Підготовує стислий контекст для передачі в Gemini"""
    context_parts = []
    
    # Поточна розмова
    if current.get("summary"):
        context_parts.append(f"Поточна ситуація: {current['summary']}")
    
    if current.get("dominant_emotion") != "нейтральний":
        context_parts.append(f"Настрій: {current['dominant_emotion']}")
    
    if current.get("main_topics") and current["main_topics"][0] != "загальне":
        context_parts.append(f"Теми: {', '.join(current['main_topics'][:2])}")
    
    # Історичний контекст
    if historical.get("status") == "success":
        if historical.get("dominant_emotions"):
            context_parts.append(f"Загальний настрій чату: {', '.join(historical['dominant_emotions'][:2])}")
        
        if historical.get("main_topics"):
            context_parts.append(f"Популярні теми: {', '.join(historical['main_topics'][:3])}")
    
    return " | ".join(context_parts) if context_parts else "Стандартна розмова"

# Експорт функцій для інтеграції
__all__ = [
    'LocalAnalyzer',
    'get_analyzer', 
    'analyze_text_local',
    'get_conversation_context'
]
