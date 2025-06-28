"""
Модуль Media Intelligence для розумної обробки медіа
Аналізує зображення, аудіо, відео та стікери з використанням AI
"""

import asyncio
import logging
import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import aiofiles
import aiohttp
# from PIL import Image  # Опційна залежність
import io
import base64

logger = logging.getLogger(__name__)


@dataclass
class MediaAnalysis:
    """Результат аналізу медіа"""
    media_id: str
    media_type: str
    description: str
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    file_size: Optional[int] = None
    dimensions: Optional[Tuple[int, int]] = None
    duration: Optional[float] = None


@dataclass
class MediaCache:
    """Кеш для збереження результатів аналізу медіа"""
    cache: Dict[str, MediaAnalysis] = field(default_factory=dict)
    max_size: int = 1000
    cache_file: str = "data/media_cache.json"


class MediaIntelligence:
    """Розумна обробка медіа контенту"""
    
    def __init__(self, 
                 gemini_api_key: Optional[str] = None,
                 cache_dir: str = "data",
                 max_cache_size: int = 1000,
                 enable_ai_analysis: bool = True):
        """
        Ініціалізація Media Intelligence
        
        Args:
            gemini_api_key: API ключ для Gemini (необов'язково)
            cache_dir: Директорія для кешу
            max_cache_size: Максимальний розмір кешу
            enable_ai_analysis: Увімкнути AI аналіз
        """
        self.gemini_api_key = gemini_api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.enable_ai_analysis = enable_ai_analysis
        
        # Ініціалізація кешу
        self.cache = MediaCache(
            max_size=max_cache_size,
            cache_file=str(self.cache_dir / "media_cache.json")
        )
        
        # Завантаження кешу
        asyncio.create_task(self._load_cache())
        
        # Статистика
        self.stats = {
            'analyzed_media': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'ai_calls': 0,
            'errors': 0
        }
        
        # Швидкі описи для різних типів медіа
        self.quick_descriptions = {
            'sticker': [
                "😄 Веселий стікер",
                "😢 Сумний стікер", 
                "😍 Милий стікер",
                "🤔 Задумливий стікер",
                "😡 Сердитий стікер",
                "🎉 Святковий стікер",
                "❤️ Романтичний стікер",
                "😂 Смішний стікер"
            ],
            'photo': [
                "📷 Фотографія",
                "🌅 Краєвид",
                "👥 Групове фото",
                "🍕 Їжа",
                "🏠 Інтер'єр",
                "🐱 Тварина",
                "🚗 Транспорт",
                "💻 Технології"
            ],
            'voice': [
                "🎤 Голосове повідомлення",
                "🎵 Музика",
                "📻 Аудіо запис",
                "🗣️ Розмова",
                "😴 Тихий голос",
                "😄 Веселий голос",
                "😠 Сердитий голос"
            ],
            'video': [
                "🎬 Відео",
                "🎮 Геймплей", 
                "🎭 Розваги",
                "📚 Навчальне відео",
                "🎵 Музичне відео",
                "🏃 Спорт",
                "🍳 Кулінарія"
            ]
        }

    async def _load_cache(self) -> None:
        """Завантаження кешу з файлу"""
        try:
            if os.path.exists(self.cache.cache_file):
                async with aiofiles.open(self.cache.cache_file, 'r', encoding='utf-8') as f:
                    data = await f.read()
                    cache_data = json.loads(data)
                    
                    # Відновлення кешу
                    for media_id, analysis_data in cache_data.items():
                        analysis = MediaAnalysis(
                            media_id=analysis_data['media_id'],
                            media_type=analysis_data['media_type'],
                            description=analysis_data['description'],
                            tags=analysis_data.get('tags', []),
                            confidence=analysis_data.get('confidence', 0.0),
                            timestamp=datetime.fromisoformat(analysis_data['timestamp']),
                            file_size=analysis_data.get('file_size'),
                            dimensions=tuple(analysis_data['dimensions']) if analysis_data.get('dimensions') else None,
                            duration=analysis_data.get('duration')
                        )
                        self.cache.cache[media_id] = analysis
                        
                logger.info(f"Завантажено {len(self.cache.cache)} записів кешу медіа")
        except Exception as e:
            logger.error(f"Помилка завантаження кешу медіа: {e}")

    async def _save_cache(self) -> None:
        """Збереження кешу у файл"""
        try:
            # Перетворення кешу в JSON-сумісний формат
            cache_data = {}
            for media_id, analysis in self.cache.cache.items():
                cache_data[media_id] = {
                    'media_id': analysis.media_id,
                    'media_type': analysis.media_type,
                    'description': analysis.description,
                    'tags': analysis.tags,
                    'confidence': analysis.confidence,
                    'timestamp': analysis.timestamp.isoformat(),
                    'file_size': analysis.file_size,
                    'dimensions': list(analysis.dimensions) if analysis.dimensions else None,
                    'duration': analysis.duration
                }
            
            async with aiofiles.open(self.cache.cache_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(cache_data, ensure_ascii=False, indent=2))
                
        except Exception as e:
            logger.error(f"Помилка збереження кешу медіа: {e}")

    def _generate_media_id(self, file_id: str, file_unique_id: Optional[str] = None) -> str:
        """Генерація унікального ID для медіа"""
        content = f"{file_id}_{file_unique_id or ''}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_quick_description(self, media_type: str) -> str:
        """Отримання швидкого опису для медіа"""
        import random
        descriptions = self.quick_descriptions.get(media_type, ["Медіа файл"])
        return random.choice(descriptions)

    async def analyze_media(self, 
                          file_id: str,
                          media_type: str,
                          file_unique_id: Optional[str] = None,
                          file_size: Optional[int] = None,
                          use_ai: Optional[bool] = None) -> MediaAnalysis:
        """
        Аналіз медіа файлу
        
        Args:
            file_id: ID файлу в Telegram
            media_type: Тип медіа (photo, sticker, voice, video)
            file_unique_id: Унікальний ID файлу
            file_size: Розмір файлу
            use_ai: Використовувати AI аналіз (за замовчуванням з налаштувань)
            
        Returns:
            MediaAnalysis: Результат аналізу
        """
        try:
            # Генерація ID медіа
            media_id = self._generate_media_id(file_id, file_unique_id)
            
            # Перевірка кешу
            if media_id in self.cache.cache:
                self.stats['cache_hits'] += 1
                return self.cache.cache[media_id]
            
            self.stats['cache_misses'] += 1
            
            # Визначення чи використовувати AI
            use_ai_analysis = use_ai if use_ai is not None else self.enable_ai_analysis
            
            # Створення базового аналізу
            analysis = MediaAnalysis(
                media_id=media_id,
                media_type=media_type,
                description=self._get_quick_description(media_type),
                file_size=file_size,
                confidence=0.5  # Базова впевненість для швидких описів
            )
            
            # AI аналіз (якщо увімкнений і доступний)
            if use_ai_analysis and self.gemini_api_key:
                try:
                    ai_analysis = await self._analyze_with_ai(file_id, media_type)
                    if ai_analysis:
                        analysis.description = ai_analysis.get('description', analysis.description)
                        analysis.tags = ai_analysis.get('tags', [])
                        analysis.confidence = ai_analysis.get('confidence', 0.8)
                        self.stats['ai_calls'] += 1
                except Exception as e:
                    logger.warning(f"Помилка AI аналізу медіа: {e}")
            
            # Збереження в кеш
            await self._cache_analysis(media_id, analysis)
            
            self.stats['analyzed_media'] += 1
            return analysis
            
        except Exception as e:
            logger.error(f"Помилка аналізу медіа {file_id}: {e}")
            self.stats['errors'] += 1
            
            # Повернення базового аналізу у випадку помилки
            return MediaAnalysis(
                media_id=self._generate_media_id(file_id, file_unique_id),
                media_type=media_type,
                description=f"Медіа файл ({media_type})",
                confidence=0.1
            )

    async def _analyze_with_ai(self, file_id: str, media_type: str) -> Optional[Dict[str, Any]]:
        """
        Аналіз медіа з використанням AI (Gemini)
        
        Args:
            file_id: ID файлу
            media_type: Тип медіа
            
        Returns:
            Результат AI аналізу або None
        """
        if not self.gemini_api_key:
            return None
            
        try:
            # Формування промпту залежно від типу медіа
            prompts = {
                'photo': "Опиши це зображення одним реченням українською мовою. Будь стислим та точним.",
                'sticker': "Опиши емоцію або значення цього стікера українською мовою одним словом або фразою.",
                'voice': "Це голосове повідомлення. Опиши можливий настрій або тон українською мовою.",
                'video': "Опиши зміст цього відео одним реченням українською мовою."
            }
            
            prompt = prompts.get(media_type, "Опиши цей медіа файл українською мовою.")
            
            # Тут би був виклик до Gemini API
            # Поки що повертаємо заглушку
            return {
                'description': f"AI аналіз: {media_type}",
                'tags': [media_type, 'ai_analyzed'],
                'confidence': 0.8
            }
            
        except Exception as e:
            logger.error(f"Помилка AI аналізу: {e}")
            return None

    async def _cache_analysis(self, media_id: str, analysis: MediaAnalysis) -> None:
        """Збереження аналізу в кеш"""
        try:
            # Перевірка розміру кешу
            if len(self.cache.cache) >= self.cache.max_size:
                await self._cleanup_cache()
            
            # Додавання в кеш
            self.cache.cache[media_id] = analysis
            
            # Збереження кешу (асинхронно)
            asyncio.create_task(self._save_cache())
            
        except Exception as e:
            logger.error(f"Помилка кешування аналізу: {e}")

    async def _cleanup_cache(self) -> None:
        """Очищення старих записів кешу"""
        try:
            # Сортування за часом (найстаріші перші)
            sorted_items = sorted(
                self.cache.cache.items(),
                key=lambda x: x[1].timestamp
            )
            
            # Видалення 20% найстаріших записів
            items_to_remove = len(sorted_items) // 5
            for i in range(items_to_remove):
                media_id = sorted_items[i][0]
                del self.cache.cache[media_id]
                
            logger.info(f"Очищено {items_to_remove} записів з кешу медіа")
            
        except Exception as e:
            logger.error(f"Помилка очищення кешу: {e}")

    async def get_media_summary(self, chat_id: int, limit: int = 100) -> Dict[str, Any]:
        """
        Отримання статистики медіа для чату
        
        Args:
            chat_id: ID чату
            limit: Ліміт записів
            
        Returns:
            Статистика медіа
        """
        try:
            # Аналіз кешу для отримання статистики
            media_types = {}
            recent_media = []
            
            # Фільтрація записів (в реальності би використовувалась БД)
            for analysis in self.cache.cache.values():
                media_type = analysis.media_type
                media_types[media_type] = media_types.get(media_type, 0) + 1
                
                if len(recent_media) < limit:
                    recent_media.append({
                        'type': analysis.media_type,
                        'description': analysis.description,
                        'timestamp': analysis.timestamp.isoformat(),
                        'confidence': analysis.confidence
                    })
            
            return {
                'total_analyzed': len(self.cache.cache),
                'media_types': media_types,
                'recent_media': recent_media[:limit],
                'stats': self.stats.copy()
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання статистики медіа: {e}")
            return {
                'total_analyzed': 0,
                'media_types': {},
                'recent_media': [],
                'stats': self.stats.copy()
            }

    async def search_media(self, 
                          query: str,
                          media_type: Optional[str] = None,
                          limit: int = 50) -> List[MediaAnalysis]:
        """
        Пошук медіа за описом або тегами
        
        Args:
            query: Пошуковий запит
            media_type: Фільтр за типом медіа
            limit: Ліміт результатів
            
        Returns:
            Список знайдених медіа
        """
        try:
            results = []
            query_lower = query.lower()
            
            for analysis in self.cache.cache.values():
                # Фільтр за типом
                if media_type and analysis.media_type != media_type:
                    continue
                
                # Пошук в описі та тегах
                if (query_lower in analysis.description.lower() or 
                    any(query_lower in tag.lower() for tag in analysis.tags)):
                    results.append(analysis)
                    
                    if len(results) >= limit:
                        break
            
            # Сортування за релевантністю (впевненістю)
            results.sort(key=lambda x: x.confidence, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Помилка пошуку медіа: {e}")
            return []

    async def get_health_status(self) -> Dict[str, Any]:
        """Отримання статусу здоров'я модуля"""
        try:
            cache_size = len(self.cache.cache)
            cache_health = "healthy" if cache_size < self.cache.max_size * 0.8 else "warning"
            
            return {
                'status': 'healthy',
                'cache_size': cache_size,
                'cache_max_size': self.cache.max_size,
                'cache_health': cache_health,
                'ai_enabled': self.enable_ai_analysis,
                'stats': self.stats.copy(),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Помилка перевірки здоров'я MediaIntelligence: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    async def cleanup_old_data(self, days: int = 30) -> None:
        """Очищення старих даних"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            removed_count = 0
            
            # Видалення старих записів
            media_ids_to_remove = []
            for media_id, analysis in self.cache.cache.items():
                if analysis.timestamp < cutoff_date:
                    media_ids_to_remove.append(media_id)
            
            for media_id in media_ids_to_remove:
                del self.cache.cache[media_id]
                removed_count += 1
            
            if removed_count > 0:
                await self._save_cache()
                logger.info(f"Видалено {removed_count} старих записів медіа аналізу")
                
        except Exception as e:
            logger.error(f"Помилка очищення старих даних MediaIntelligence: {e}")
