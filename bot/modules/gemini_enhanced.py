# Покращений модуль для інтеграції з Gemini API з повною підтримкою нових можливостей
import aiohttp
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from aiogram.types import Message
from . import context
from .token_counter import token_counter
import os
from dotenv import load_dotenv
from bot.bot_config import GEMINI_MODEL, PERSONA

load_dotenv()

# Константи для API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY не знайдено в змінних середовища")

# Версія API (v1, v1beta, v1alpha)
GEMINI_API_VERSION = os.getenv("GEMINI_API_VERSION", "v1beta")
BASE_API_URL = f"https://generativelanguage.googleapis.com/{GEMINI_API_VERSION}"

# Налаштування з .env файлу - ОПТИМІЗОВАНО для природнішого спілкування
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))  # Ще більше знижено для більш стабільних відповідей
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "70"))  # Значно зменшено для коротких відповідей (2-3 речення)
GEMINI_TOP_P = float(os.getenv("GEMINI_TOP_P", "0.8"))  # Знижено для більшої передбачуваності
GEMINI_TOP_K = int(os.getenv("GEMINI_TOP_K", "40"))
GEMINI_ENABLE_THINKING = os.getenv("GEMINI_ENABLE_THINKING", "false").lower() == "true"
GEMINI_THINKING_BUDGET = int(os.getenv("GEMINI_THINKING_BUDGET", "2048"))
GEMINI_ENABLE_SAFETY_OVERRIDE = os.getenv("GEMINI_ENABLE_SAFETY_OVERRIDE", "true").lower() == "true"
GEMINI_ENABLE_STRUCTURED_OUTPUT = os.getenv("GEMINI_ENABLE_STRUCTURED_OUTPUT", "false").lower() == "true"
GEMINI_RATE_LIMIT_RPM = int(os.getenv("GEMINI_RATE_LIMIT_RPM", "45"))  # Збільшено з 30 до 45
GEMINI_CACHE_ENABLED = os.getenv("GEMINI_CACHE_ENABLED", "true").lower() == "true"
GEMINI_CACHE_TTL = int(os.getenv("GEMINI_CACHE_TTL", "300"))  # 5 minutes

# Енуми для типизації
class HarmCategory(Enum):
    HARASSMENT = "HARM_CATEGORY_HARASSMENT"
    HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
    SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
    DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"
    CIVIC_INTEGRITY = "HARM_CATEGORY_CIVIC_INTEGRITY"

class HarmBlockThreshold(Enum):
    BLOCK_NONE = "BLOCK_NONE"
    BLOCK_ONLY_HIGH = "BLOCK_ONLY_HIGH"
    BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE"
    BLOCK_LOW_AND_ABOVE = "BLOCK_LOW_AND_ABOVE"

class FinishReason(Enum):
    STOP = "STOP"
    MAX_TOKENS = "MAX_TOKENS"
    SAFETY = "SAFETY"
    RECITATION = "RECITATION"
    OTHER = "OTHER"

# Дата-класи для структурованих запитів
@dataclass
class SafetySetting:
    """Налаштування безпеки для Gemini API."""
    category: HarmCategory
    threshold: HarmBlockThreshold

@dataclass
class ThinkingConfig:
    """Конфігурація режиму мислення."""
    include_thoughts: bool = True
    thinking_budget: int = 2048

@dataclass
class GenerationConfig:
    """Конфігурація генерації тексту."""
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    response_mime_type: Optional[str] = None
    response_schema: Optional[Dict[str, Any]] = None
    thinking_config: Optional[ThinkingConfig] = None

@dataclass
class ContentPart:
    """Частина контенту."""
    text: str

@dataclass
class Content:
    """Контент для запиту."""
    parts: List[ContentPart]
    role: Optional[str] = None

@dataclass
class GenerateContentRequest:
    """Повний запит для генерації контенту."""
    contents: List[Content]
    system_instruction: Optional[Content] = None
    generation_config: Optional[GenerationConfig] = None
    safety_settings: Optional[List[SafetySetting]] = None

@dataclass
class UsageMetadata:
    """Метадані використання."""
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int
    cached_content_token_count: Optional[int] = None
    thoughts_token_count: Optional[int] = None

@dataclass
class SafetyRating:
    """Рейтинг безпеки."""
    category: HarmCategory
    probability: str
    blocked: bool

@dataclass
class Candidate:
    """Кандидат відповіді."""
    content: Content
    finish_reason: Optional[FinishReason] = None
    safety_ratings: Optional[List[SafetyRating]] = None
    token_count: Optional[int] = None

@dataclass
class GenerateContentResponse:
    """Відповідь від API."""
    candidates: List[Candidate]
    usage_metadata: Optional[UsageMetadata] = None
    model_version: Optional[str] = None

# Глобальні змінні для статистики та кешування
class APIStats:
    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_reset = datetime.now()
        self.requests_this_minute: List[float] = []

    def add_request(self, success: bool, tokens: int = 0):
        self.total_requests += 1
        self.total_tokens += tokens
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Відстежуємо запити за хвилину
        now = time.time()
        self.requests_this_minute.append(now)
        # Очищаємо старі записи (більше хвилини)
        self.requests_this_minute = [t for t in self.requests_this_minute if now - t < 60]

    def get_rpm(self) -> int:
        """Повертає кількість запитів за останню хвилину."""
        return len(self.requests_this_minute)

    def can_make_request(self) -> bool:
        """Перевіряє чи можна зробити запит (rate limiting)."""
        return self.get_rpm() < GEMINI_RATE_LIMIT_RPM

    def get_stats(self) -> Dict[str, Any]:
        """Повертає статистику використання."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / max(1, self.total_requests),
            "total_tokens": self.total_tokens,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            "requests_per_minute": self.get_rpm(),
            "uptime": str(datetime.now() - self.last_reset)
        }

# Глобальна статистика
api_stats = APIStats()

# Простий кеш для результатів
class SimpleCache:
    def __init__(self, ttl: int = GEMINI_CACHE_TTL):
        self.cache: Dict[str, tuple[str, float]] = {}
        self.ttl = ttl

    def _get_key(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        """Генерує ключ для кешування."""
        config_str = json.dumps(asdict(config) if config else {}, sort_keys=True)
        return f"{hash(prompt)}_{hash(config_str)}"

    def get(self, prompt: str, config: Optional[GenerationConfig] = None) -> Optional[str]:
        """Отримує результат з кешу."""
        if not GEMINI_CACHE_ENABLED:
            return None
            
        key = self._get_key(prompt, config)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                api_stats.cache_hits += 1
                return result
            else:
                del self.cache[key]
        
        api_stats.cache_misses += 1
        return None

    def set(self, prompt: str, result: str, config: Optional[GenerationConfig] = None):
        """Зберігає результат в кеш."""
        if not GEMINI_CACHE_ENABLED:
            return
            
        key = self._get_key(prompt, config)
        self.cache[key] = (result, time.time())

    def clear(self):
        """Очищає кеш."""
        self.cache.clear()

# Глобальний кеш
cache = SimpleCache()

class GeminiAPIClient:
    """Клас для роботи з Gemini API з повною підтримкою нових можливостей."""
    
    def __init__(self, api_key: str = GEMINI_API_KEY, model: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model = model
        self.base_url = BASE_API_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Отримує або створює aiohttp сесію."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Закриває aiohttp сесію."""
        if self.session and not self.session.closed:
            await self.session.close()

    def _get_default_safety_settings(self) -> List[SafetySetting]:
        """Повертає дефолтні налаштування безпеки."""
        # Мінімальні налаштування безпеки для більш вільного спілкування
        return [
            SafetySetting(HarmCategory.HARASSMENT, HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(HarmCategory.HATE_SPEECH, HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(HarmCategory.SEXUALLY_EXPLICIT, HarmBlockThreshold.BLOCK_ONLY_HIGH),
            SafetySetting(HarmCategory.DANGEROUS_CONTENT, HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(HarmCategory.CIVIC_INTEGRITY, HarmBlockThreshold.BLOCK_NONE),
        ]

    def _get_default_generation_config(self) -> GenerationConfig:
        """Повертає дефолтну конфігурацію генерації."""
        config = GenerationConfig(
            temperature=GEMINI_TEMPERATURE,
            max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
            top_p=GEMINI_TOP_P,
            top_k=GEMINI_TOP_K,
        )
        
        if GEMINI_ENABLE_THINKING:
            config.thinking_config = ThinkingConfig(
                include_thoughts=True,
                thinking_budget=GEMINI_THINKING_BUDGET
            )
        
        return config

    def _build_system_instruction(self, context_type: str = "normal", 
                                  recommendations: Optional[Dict[str, Any]] = None) -> Content:
        """Будує системну інструкцію на основі контексту."""
        from bot.bot_config import PERSONA
        
        base_instruction = (
            f"Ти — {PERSONA['name']}, приємний та дружелюбний чат-бот українською мовою. "
            "Ти розумний співрозмовник, який може підтримати будь-яку розмову. "
            "Твій стиль: природне спілкування з дуже легким гумором коли це доречно. "
            "Говори зрозуміло, КОРОТКО та по суті як звичайна людина. "
            "Твої відповіді мають бути ДУЖЕ КОРОТКИМИ (1-2 речення максимум). "
            "Не використовуй дивних слів чи незрозумілих фраз. "
            "Будь корисним та адекватним у відповідях."
        )
        
        # Додаємо контекстні інструкції
        if context_type == "minimal":
            base_instruction += "\n\nРЕЖИМ: Мінімальні відповіді. Відповідай дуже коротко (1-2 речення)."
        elif context_type == "guidance":
            base_instruction += "\n\nРЕЖИМ: Корисні поради. Дай конструктивну пораду або направ розмову."
        elif context_type == "clarification":
            base_instruction += "\n\nРЕЖИМ: З'ясування. М'якко спитай що саме потрібно або направ розмову."
        elif context_type == "humor":
            base_instruction += "\n\nРЕЖИМ: Легкий гумор. Додай невимушений жарт або дотепний коментар."
        
        # Додаємо рекомендації з smart behavior
        if recommendations:
            response_style = recommendations.get('response_style', 'normal')
            max_length = recommendations.get('max_response_length', 200)
            
            if response_style == 'minimal':
                base_instruction += f"\n\nОБМЕЖЕННЯ: Твоя відповідь повинна бути ДУЖЕ короткою (до {max_length//2} символів)."
            elif response_style == 'concise':
                base_instruction += f"\n\nОБМЕЖЕННЯ: Твоя відповідь повинна бути короткою (до {max_length} символів)."
            
            if recommendations.get('should_ask_clarification'):
                base_instruction += "\n\nЗАВДАННЯ: Розмова незрозуміла - м'якко з'ясуй що саме потрібно."
            
            if recommendations.get('should_provide_guidance'):
                base_instruction += "\n\nЗАВДАННЯ: Дай корисну пораду або направ розмову в конструктивне русло."
        
        return Content(parts=[ContentPart(text=base_instruction)])

    async def generate_content(self, 
                              prompt: str, 
                              context_type: str = "normal",
                              custom_config: Optional[GenerationConfig] = None,
                              custom_safety: Optional[List[SafetySetting]] = None,
                              recommendations: Optional[Dict[str, Any]] = None,
                              enable_cache: bool = True) -> str:
        """
        Генерує відповідь використовуючи Gemini API.
        
        Args:
            prompt: Текст запиту
            context_type: Тип контексту ('normal', 'minimal', 'guidance', 'clarification', 'humor')
            custom_config: Кастомна конфігурація генерації
            custom_safety: Кастомні налаштування безпеки
            recommendations: Рекомендації з smart behavior системи
            enable_cache: Чи використовувати кешування
            
        Returns:
            Згенерований текст відповіді
        """
        
        # Перевіряємо rate limit
        if not api_stats.can_make_request():
            logging.warning(f"Rate limit досягнуто: {api_stats.get_rpm()}/хв")
            await asyncio.sleep(60 / GEMINI_RATE_LIMIT_RPM)
        
        # Перевіряємо кеш
        config_for_cache = custom_config or self._get_default_generation_config()
        if enable_cache:
            cached_result = cache.get(prompt, config_for_cache)
            if cached_result:
                return cached_result
        
        # Будуємо запит
        system_instruction = self._build_system_instruction(context_type, recommendations)
        generation_config = custom_config or self._get_default_generation_config()
        safety_settings = custom_safety or self._get_default_safety_settings()
        
        request = GenerateContentRequest(
            contents=[Content(parts=[ContentPart(text=prompt)])],
            system_instruction=system_instruction,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        try:
            response = await self._make_request(request)
            result = self._extract_text_from_response(response)
            
            # Зберігаємо в кеш
            if enable_cache:
                cache.set(prompt, result, config_for_cache)
            
            # Оновлюємо статистику
            tokens_used = 0
            if response.usage_metadata:
                tokens_used = response.usage_metadata.total_token_count
            api_stats.add_request(True, tokens_used)
            
            return result
            
        except Exception as e:
            api_stats.add_request(False)
            logging.error(f"Помилка генерації контенту: {e}")
            raise

    async def _make_request(self, request: GenerateContentRequest) -> GenerateContentResponse:
        """Виконує HTTP запит до Gemini API."""
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        
        # Конвертуємо запит в JSON, видаляючи None значення
        payload = self._request_to_dict(request)
        
        session = await self._get_session()
        async with session.post(url, headers=headers, params=params, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_response(data)
            else:
                error_text = await response.text()
                raise Exception(f"Gemini API помилка {response.status}: {error_text}")

    def _request_to_dict(self, request: GenerateContentRequest) -> Dict[str, Any]:
        """Конвертує запит в словник для JSON."""
        result: Dict[str, Any] = {}
        
        # Contents
        result["contents"] = []
        for content in request.contents:
            content_dict: Dict[str, Any] = {"parts": [{"text": part.text} for part in content.parts]}
            if content.role:
                content_dict["role"] = content.role
            result["contents"].append(content_dict)
        
        # System instruction
        if request.system_instruction:
            result["systemInstruction"] = {
                "parts": [{"text": part.text} for part in request.system_instruction.parts]
            }
        
        # Generation config
        if request.generation_config:
            config_dict: Dict[str, Any] = {}
            config = request.generation_config
            
            if config.temperature is not None:
                config_dict["temperature"] = config.temperature
            if config.max_output_tokens is not None:
                config_dict["maxOutputTokens"] = config.max_output_tokens
            if config.top_p is not None:
                config_dict["topP"] = config.top_p
            if config.top_k is not None:
                config_dict["topK"] = config.top_k
            if config.stop_sequences:
                config_dict["stopSequences"] = config.stop_sequences
            if config.presence_penalty is not None:
                config_dict["presencePenalty"] = config.presence_penalty
            if config.frequency_penalty is not None:
                config_dict["frequencyPenalty"] = config.frequency_penalty
            if config.response_mime_type:
                config_dict["responseMimeType"] = config.response_mime_type
            if config.response_schema:
                config_dict["responseSchema"] = config.response_schema
            
            # Thinking config
            if config.thinking_config:
                thinking_dict: Dict[str, Any] = {}
                thinking_dict["includeThoughts"] = config.thinking_config.include_thoughts
                thinking_dict["thinkingBudget"] = config.thinking_config.thinking_budget
                config_dict["thinkingConfig"] = thinking_dict
            
            if config_dict:
                result["generationConfig"] = config_dict
        
        # Safety settings
        if request.safety_settings:
            result["safetySettings"] = []
            for setting in request.safety_settings:
                safety_dict = {
                    "category": setting.category.value,
                    "threshold": setting.threshold.value
                }
                result["safetySettings"].append(safety_dict)
        
        return result

    def _parse_response(self, data: Dict[str, Any]) -> GenerateContentResponse:
        """Парсить відповідь від API."""
        candidates: List[Candidate] = []
        for candidate_data in data.get("candidates", []):
            content_data = candidate_data.get("content", {})
            parts = [ContentPart(text=part.get("text", "")) for part in content_data.get("parts", [])]
            content = Content(parts=parts, role=content_data.get("role"))
            
            finish_reason = None
            if "finishReason" in candidate_data:
                try:
                    finish_reason = FinishReason(candidate_data["finishReason"])
                except ValueError:
                    finish_reason = FinishReason.OTHER
            
            safety_ratings: List[SafetyRating] = []
            for rating_data in candidate_data.get("safetyRatings", []):
                try:
                    category = HarmCategory(rating_data.get("category", ""))
                    probability = rating_data.get("probability", "")
                    blocked = rating_data.get("blocked", False)
                    safety_ratings.append(SafetyRating(category, probability, blocked))
                except ValueError:
                    continue
            
            candidate = Candidate(
                content=content,
                finish_reason=finish_reason,
                safety_ratings=safety_ratings if safety_ratings else None,
                token_count=candidate_data.get("tokenCount")
            )
            candidates.append(candidate)
        
        usage_metadata = None
        if "usageMetadata" in data:
            usage_data = data["usageMetadata"]
            usage_metadata = UsageMetadata(
                prompt_token_count=usage_data.get("promptTokenCount", 0),
                candidates_token_count=usage_data.get("candidatesTokenCount", 0),
                total_token_count=usage_data.get("totalTokenCount", 0),
                cached_content_token_count=usage_data.get("cachedContentTokenCount"),
                thoughts_token_count=usage_data.get("thoughtsTokenCount")
            )
        
        return GenerateContentResponse(
            candidates=candidates,
            usage_metadata=usage_metadata,
            model_version=data.get("modelVersion")
        )

    def _extract_text_from_response(self, response: GenerateContentResponse) -> str:
        """Витягує текст з відповіді."""
        if not response.candidates:
            raise Exception("Немає кандидатів відповіді")
        
        candidate = response.candidates[0]
        
        # Перевіряємо finish_reason
        if candidate.finish_reason == FinishReason.SAFETY:
            logging.warning("Відповідь заблокована з міркувань безпеки")
            return "Вибачте, не можу відповісти на це питання з міркувань безпеки."
        elif candidate.finish_reason == FinishReason.MAX_TOKENS:
            logging.warning("Відповідь обрізана через ліміт токенів")
        
        if not candidate.content.parts:
            raise Exception("Немає тексту у відповіді")
        
        return candidate.content.parts[0].text.strip()

# Глобальний клієнт
_client: Optional[GeminiAPIClient] = None

async def get_client() -> GeminiAPIClient:
    """Отримує глобальний клієнт API."""
    global _client
    if _client is None:
        _client = GeminiAPIClient()
    return _client

async def close_client():
    """Закриває глобальний клієнт."""
    global _client
    if _client:
        await _client.close()
        _client = None

# Обгортки для сумісності зі старим кодом
async def process_message(message: Message, tone_instruction: Optional[str] = None) -> str:
    """
    Обробляє повідомлення через покращений Gemini API з урахуванням контексту та тону.
    
    Args:
        message: Повідомлення для обробки (може бути FakeMessage з додатковими даними)
        tone_instruction: Додаткова інструкція для тону відповіді
        
    Returns:
        Відповідь від Gemini
    """
    try:
        # Аналізуємо контекст відповіді (чи це відповідь на повідомлення бота)
        reply_context = analyze_reply_context(message)
        
        # Перевіряємо чи є обробленний контекст (з покращеної системи)
        if hasattr(message, 'processed_context') and message.processed_context:
            chat_context = message.processed_context
        else:
            chat_context = context.get_context(message.chat.id)
        
        # Отримуємо рекомендації якщо є
        recommendations = getattr(message, 'recommendations', {})
        
        # Аналізуємо контекст для визначення типу відповіді
        last_msgs = [m.get('text', '') for m in chat_context[-5:] if m.get('text')]
        context_type = _analyze_context_type(last_msgs, recommendations)
        
        # Формуємо історію діалогу з іменами користувачів
        history = []
        for m in chat_context[-PERSONA['context_limit']:]:
            if m.get('text'):
                user_display = m.get('user_name', m.get('user', 'Невідомий'))
                history.append(f"{user_display}: {m['text']}")
        
        # Додаємо поточне повідомлення
        last_text = message.text if message.text else '[медіа]'
        user_name = getattr(message.from_user, 'full_name', 'Невідомий') if message.from_user else 'Невідомий'
        
        # Створюємо покращену системну інструкцію
        system_instruction = build_enhanced_system_instruction(reply_context, recommendations)
        
        if tone_instruction:
            system_instruction += f" {tone_instruction}"
        
        # Формуємо фінальний промпт з урахуванням діалогових ланцюгів
        dialogue_context = "\n".join(history)
        
        # Спеціальний формат для відповідей на повідомлення бота
        if reply_context.get('is_reply_to_bot'):
            original_msg = reply_context.get('original_message', '')
            prompt = (
                f"Історія розмови:\n{dialogue_context}\n"
                f"Твоє попереднє повідомлення: {original_msg}\n"
                f"Відповідь від {user_name}: {last_text}\n"
                "Продовж діалог природно, враховуючи що користувач відповідає на твоє повідомлення."
            )
        else:
            prompt = (
                f"Історія розмови:\n{dialogue_context}\n"
                f"Поточне повідомлення від {user_name}: {last_text}\n"
                "Дай коротку, природну відповідь українською мовою."
            )
        
        # Компресія промпту якщо потрібно з урахуванням токенів
        max_tokens = PERSONA.get('max_context_tokens', 800000)
        
        # Оцінюємо поточну кількість токенів
        current_tokens = token_counter.estimate_tokens(prompt)
        
        while current_tokens > max_tokens and history:
            # Видаляємо найстарші повідомлення
            history.pop(0)
            dialogue_context = "\n".join(history)
            
            if reply_context.get('is_reply_to_bot'):
                original_msg = reply_context.get('original_message', '')
                prompt = (
                    f"Історія розмови:\n{dialogue_context}\n"
                    f"Твоє попереднє повідомлення: {original_msg}\n"
                    f"Відповідь від {user_name}: {last_text}\n"
                    "Продовж діалог природно, враховуючи що користувач відповідає на твоє повідомлення."
                )
            else:
                prompt = (
                    f"Історія розмови:\n{dialogue_context}\n"
                    f"Поточне повідомлення від {user_name}: {last_text}\n"
                    "Дай коротку, природну відповідь українською мовою."
                )
            current_tokens = token_counter.estimate_tokens(prompt)
        
        logging.info(f"Фінальний промпт: ~{current_tokens} токенів з {len(history)} повідомлень. "
                    f"Reply to bot: {reply_context.get('is_reply_to_bot', False)}")
        
        # Генеруємо відповідь
        client = await get_client()
        
        # Створюємо динамічну конфігурацію
        context_info = {
            'is_reply_to_bot': reply_context.get('is_reply_to_bot', False),
            'is_mention': recommendations.get('is_mention', False),
            'is_random': recommendations.get('is_random', False)
        }
        custom_config = get_dynamic_generation_config(context_info, recommendations)
        
        result = await safe_api_call(
            client.generate_content,
            prompt,
            context_type=context_type,
            custom_config=custom_config,
            recommendations=recommendations,
            system_instruction=system_instruction
        )
        
        return result
        
    except Exception as e:
        logging.error(f"Помилка в process_message: {e}")
        return "Вибачте, сталася помилка при обробці повідомлення."

def _analyze_context_type(last_msgs: List[str], recommendations: Optional[Dict[str, Any]] = None) -> str:
    """Аналізує тип контексту для вибору відповідного режиму."""
    if recommendations:
        if recommendations.get('should_ask_clarification'):
            return "clarification"
        if recommendations.get('should_provide_guidance'):
            return "guidance"
        if recommendations.get('response_style') == 'minimal':
            return "minimal"
    
    # Аналіз за ключовими словами
    text = ' '.join(last_msgs).lower()
    if any(word in text for word in ['жарт', '😂', 'lol', 'хаха']):
        return "humor"
    elif any(word in text for word in ['що', 'як', 'чому', 'де', 'коли', '?']):
        return "guidance"
    elif len(text.strip()) < 10:
        return "minimal"
    else:
        return "normal"

async def safe_api_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Безпечний виклик API з повторними спробами та exponential backoff."""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"API виклик провалився після {max_retries} спроб: {e}")
                raise
            
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            logging.warning(f"API помилка (спроба {attempt + 1}/{max_retries}): {e}. Повтор через {delay}с")
            await asyncio.sleep(delay)

async def get_api_stats() -> Dict[str, Any]:
    """Повертає статистику використання API."""
    return api_stats.get_stats()

async def clear_cache():
    """Очищає кеш API."""
    cache.clear()
    logging.info("Кеш API очищено")

# Функції для structured output (для майбутнього використання)
async def generate_json_response(prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Генерує структуровану JSON відповідь."""
    if not GEMINI_ENABLE_STRUCTURED_OUTPUT:
        raise Exception("Structured output не увімкнено")
    
    client = await get_client()
    config = GenerationConfig(
        temperature=0.1,  # Низька температура для структурованих відповідей
        response_mime_type="application/json",
        response_schema=schema
    )
    
    result = await client.generate_content(prompt, custom_config=config)
    return json.loads(result)

# Cleanup функція
async def cleanup():
    """Очищає ресурси при завершенні."""
    await close_client()
    cache.clear()
    logging.info("Gemini API клієнт очищено")

# Автоматичне очищення при імпорті
import atexit
atexit.register(lambda: asyncio.create_task(cleanup()) if asyncio.get_event_loop().is_running() else None)

def get_dynamic_temperature(is_reply_to_bot: bool, is_mention: bool, is_random: bool) -> float:
    """Динамічно визначає temperature для різних типів відповідей"""
    base_temp = 0.2  # Базова температура знижена ще більше
    
    if is_reply_to_bot:
        return 0.15  # Найнижча для точних відповідей на запитання
    elif is_mention:
        return 0.2   # Трохи більше креативності для згадок
    elif is_random:
        return 0.25  # Більше креативності для випадкових відповідей
    else:
        return base_temp

def analyze_reply_context(message) -> Dict[str, Any]:
    """Аналізує контекст відповіді на повідомлення бота"""
    context = {
        'is_reply_to_bot': False,
        'original_message': None,
        'reply_type': 'normal',
        'conversation_depth': 0
    }
    
    if hasattr(message, 'reply_to_message') and message.reply_to_message:
        # Перевіряємо чи це відповідь на повідомлення бота
        if hasattr(message.reply_to_message, 'from_user') and message.reply_to_message.from_user:
            # Отримуємо ID бота з конфігурації
            from bot.bot_config import PERSONA
            bot_id = getattr(message.reply_to_message.from_user, 'id', None)
            
            # Перевіряємо чи це повідомлення від бота (треба перевірити через username або інші ознаки)
            if message.reply_to_message.from_user.is_bot or \
               (hasattr(message.reply_to_message.from_user, 'username') and 
                message.reply_to_message.from_user.username and 
                'gryag' in message.reply_to_message.from_user.username.lower()):
                
                context['is_reply_to_bot'] = True
                context['original_message'] = message.reply_to_message.text or '[медіа]'
                
                # Визначаємо тип відповіді
                if '?' in (message.text or ''):
                    context['reply_type'] = 'question'
                elif any(word in (message.text or '').lower() for word in ['дякую', 'спасибо', 'thanks']):
                    context['reply_type'] = 'thanks' 
                elif any(word in (message.text or '').lower() for word in ['ні', 'нет', 'не', 'неправильно']):
                    context['reply_type'] = 'disagreement'
                else:
                    context['reply_type'] = 'continuation'
    
    return context

def build_enhanced_system_instruction(context: Dict[str, Any], recommendations: Optional[Dict[str, Any]] = None) -> str:
    """Будує покращену системну інструкцію з урахуванням контексту діалогу"""
    from bot.bot_config import PERSONA
    
    base_instruction = (
        f"Ти — {PERSONA['name']}, дружелюбний український чат-бот. "
        "Твій стиль: природне спілкування як у звичайній людини, з легким гумором коли доречно. "
        "Говори зрозуміло, коротко та по суті. Не використовуй дивних слів чи абсурдних фраз. "
        "Будь корисним та адекватним у відповідях."
    )
    
    # Додаємо контекст відповіді
    if context.get('is_reply_to_bot'):
        reply_type = context.get('reply_type', 'normal')
        original_msg = context.get('original_message', '')
        
        if reply_type == 'question':
            base_instruction += f"\n\nКОНТЕКСТ: Користувач ставить запитання у відповідь на твоє повідомлення: '{original_msg}'. Дай чітку та корисну відповідь."
        elif reply_type == 'thanks':
            base_instruction += f"\n\nКОНТЕКСТ: Користувач дякує за твоє повідомлення: '{original_msg}'. Відповідь має бути скромною та дружньою."
        elif reply_type == 'disagreement':
            base_instruction += f"\n\nКОНТЕКСТ: Користувач не погоджується з твоїм повідомленням: '{original_msg}'. Будь відкритим до дискусії."
        else:
            base_instruction += f"\n\nКОНТЕКСТ: Користувач продовжує розмову після твого повідомлення: '{original_msg}'. Підтримай діалог."
    
    # Додаємо рекомендації з аналізу поведінки
    if recommendations:
        conversation_type = recommendations.get('conversation_type', 'general')
        mood = recommendations.get('mood', 'neutral') 
        
        if conversation_type == 'technical':
            base_instruction += "\n\nТОН: Технічна розмова - будь точним та інформативним."
        elif conversation_type == 'funny':
            base_instruction += "\n\nТОН: Жартівлива розмова - додай легкий гумор."
        elif conversation_type == 'emotional':
            base_instruction += "\n\nТОН: Емоційна розмова - будь підтримуючим та розуміючим."
        
        # Обмеження довжини
        max_length = recommendations.get('max_response_length', 200)
        if max_length < 100:
            base_instruction += "\n\nОБМЕЖЕННЯ: Твоя відповідь має бути ДУЖЕ короткою (1-2 речення)."
        elif max_length < 200:
            base_instruction += "\n\nОБМЕЖЕННЯ: Твоя відповідь має бути короткою та по суті."
    
    return base_instruction

# Розширюємо функцію для роботи з динамічними параметрами
def get_dynamic_generation_config(context: Dict[str, Any], recommendations: Optional[Dict[str, Any]] = None) -> GenerationConfig:
    """Створює динамічну конфігурацію генерації на основі контексту"""
    
    # Визначаємо temperature
    is_reply_to_bot = context.get('is_reply_to_bot', False)
    is_mention = context.get('is_mention', False)
    is_random = context.get('is_random', False)
    
    temperature = get_dynamic_temperature(is_reply_to_bot, is_mention, is_random)
    
    # Визначаємо максимальну довжину (тепер набагато менше)
    max_tokens = GEMINI_MAX_OUTPUT_TOKENS  # Базове значення 70 токенів
    if recommendations:
        max_length = recommendations.get('max_response_length', 150)
        # Конвертуємо символи в токени (приблизно 3-4 символи на токен для української)
        estimated_tokens = max_length // 3
        max_tokens = min(max_tokens, max(30, estimated_tokens))  # Мінімум 30 токенів
    
    # Для різних типів відповідей - різні ліміти
    if is_reply_to_bot:
        max_tokens = min(max_tokens, 100)  # Трохи більше для відповідей на питання
    elif is_mention:
        max_tokens = min(max_tokens, 80)   # Стандартно для згадок
    elif is_random:
        max_tokens = min(max_tokens, 60)   # Коротше для випадкових відповідей
    
    return GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        top_p=GEMINI_TOP_P,
        top_k=GEMINI_TOP_K
    )
