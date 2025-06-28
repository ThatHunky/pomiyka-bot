"""
Модуль UI компонентів для Telegram бота
Створює красиві інтерфейси, кнопки, клавіатури та форматування повідомлень
"""

import logging
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    from aiogram.types import (
        InlineKeyboardMarkup, InlineKeyboardButton,
        ReplyKeyboardMarkup, KeyboardButton,
        ReplyKeyboardRemove, ForceReply
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
    from aiogram.utils.formatting import Text, Bold, Italic, Code, Pre
    aiogram_available = True
except ImportError:
    # Заглушки для тестування
    aiogram_available = False
    
    class InlineKeyboardMarkup:
        def __init__(self, **kwargs: Any): pass
    
    class InlineKeyboardButton:
        def __init__(self, **kwargs: Any): pass
    
    class ReplyKeyboardMarkup:
        def __init__(self, **kwargs: Any): pass
    
    class KeyboardButton:
        def __init__(self, **kwargs: Any): pass
    
    class ReplyKeyboardRemove:
        pass
    
    class ForceReply:
        pass
    
    class InlineKeyboardBuilder:
        def __init__(self): pass
        def button(self, *args: Any, **kwargs: Any) -> 'InlineKeyboardBuilder': return self
        def adjust(self, *args: Any) -> 'InlineKeyboardBuilder': return self
        def as_markup(self) -> InlineKeyboardMarkup: return InlineKeyboardMarkup()
    
    class ReplyKeyboardBuilder:
        def __init__(self): pass
        def button(self, *args: Any, **kwargs: Any) -> 'ReplyKeyboardBuilder': return self
        def adjust(self, *args: Any) -> 'ReplyKeyboardBuilder': return self
        def as_markup(self, **kwargs: Any) -> ReplyKeyboardMarkup: return ReplyKeyboardMarkup()
    
    class Text:
        def __init__(self, *args: Any, **kwargs: Any): pass
    
    Bold = Italic = Code = Pre = Text

logger = logging.getLogger(__name__)


class ButtonStyle(Enum):
    """Стилі кнопок"""
    PRIMARY = "🔵"
    SUCCESS = "🟢"
    WARNING = "🟡" 
    DANGER = "🔴"
    INFO = "ℹ️"
    SETTINGS = "⚙️"
    BACK = "◀️"
    FORWARD = "▶️"
    UP = "🔼"
    DOWN = "🔽"
    HOME = "🏠"
    REFRESH = "🔄"
    CLOSE = "❌"


class MessageType(Enum):
    """Типи повідомлень"""
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    LOADING = "⏳"
    QUESTION = "❓"


@dataclass
class UIButton:
    """Кнопка інтерфейсу"""
    text: str
    callback_data: str = ""
    url: Optional[str] = None
    style: ButtonStyle = ButtonStyle.PRIMARY
    enabled: bool = True
    row: int = 0


@dataclass
class UIKeyboard:
    """Клавіатура інтерфейсу"""
    buttons: List[UIButton] = field(default_factory=list)
    inline: bool = True
    one_time: bool = False
    resize: bool = True
    selective: bool = False


@dataclass
class UIMessage:
    """Повідомлення інтерфейсу"""
    text: str
    message_type: MessageType = MessageType.INFO
    keyboard: Optional[UIKeyboard] = None
    parse_mode: str = "HTML"
    disable_preview: bool = True


class UIComponentsManager:
    """Менеджер UI компонентів"""
    
    def __init__(self):
        """Ініціалізація менеджера UI"""
        self.templates = {}
        self.default_styles = {
            'emoji_map': {
                ButtonStyle.PRIMARY: "🔵",
                ButtonStyle.SUCCESS: "✅", 
                ButtonStyle.WARNING: "⚠️",
                ButtonStyle.DANGER: "❌",
                ButtonStyle.INFO: "ℹ️",
                ButtonStyle.SETTINGS: "⚙️",
                ButtonStyle.BACK: "◀️",
                ButtonStyle.FORWARD: "▶️",
                ButtonStyle.HOME: "🏠",
                ButtonStyle.REFRESH: "🔄",
                ButtonStyle.CLOSE: "❌"
            },
            'message_icons': {
                MessageType.INFO: "ℹ️",
                MessageType.SUCCESS: "✅",
                MessageType.WARNING: "⚠️", 
                MessageType.ERROR: "❌",
                MessageType.LOADING: "⏳",
                MessageType.QUESTION: "❓"
            }
        }

    def create_button(self, 
                     text: str,
                     callback_data: str = "",
                     url: Optional[str] = None,
                     style: ButtonStyle = ButtonStyle.PRIMARY,
                     enabled: bool = True) -> UIButton:
        """
        Створення кнопки
        
        Args:
            text: Текст кнопки
            callback_data: Дані для callback
            url: URL для кнопки-посилання
            style: Стиль кнопки
            enabled: Чи активна кнопка
            
        Returns:
            UIButton: Створена кнопка
        """
        # Додавання емодзі до тексту
        emoji = self.default_styles['emoji_map'].get(style, "")
        if emoji and not text.startswith(emoji):
            text = f"{emoji} {text}"
            
        return UIButton(
            text=text,
            callback_data=callback_data,
            url=url,
            style=style,
            enabled=enabled
        )

    def create_keyboard(self, 
                       buttons: List[UIButton],
                       inline: bool = True,
                       columns: int = 2,
                       one_time: bool = False) -> UIKeyboard:
        """
        Створення клавіатури
        
        Args:
            buttons: Список кнопок
            inline: Інлайн клавіатура
            columns: Кількість колонок
            one_time: Одноразова клавіатура
            
        Returns:
            UIKeyboard: Створена клавіатура
        """
        # Розподіл кнопок по рядках
        for i, button in enumerate(buttons):
            button.row = i // columns
            
        return UIKeyboard(
            buttons=buttons,
            inline=inline,
            one_time=one_time
        )

    def create_pagination_keyboard(self,
                                 current_page: int,
                                 total_pages: int,
                                 callback_prefix: str = "page",
                                 additional_buttons: List[UIButton] = None) -> UIKeyboard:
        """
        Створення клавіатури з пагінацією
        
        Args:
            current_page: Поточна сторінка
            total_pages: Загальна кількість сторінок
            callback_prefix: Префікс для callback даних
            additional_buttons: Додаткові кнопки
            
        Returns:
            UIKeyboard: Клавіатура з пагінацією
        """
        buttons = []
        
        # Кнопка "Назад"
        if current_page > 1:
            buttons.append(self.create_button(
                "◀️ Назад",
                f"{callback_prefix}_{current_page - 1}",
                style=ButtonStyle.BACK
            ))
        
        # Інформація про сторінку
        page_info = f"{current_page}/{total_pages}"
        buttons.append(self.create_button(
            page_info,
            f"{callback_prefix}_info",
            style=ButtonStyle.INFO,
            enabled=False
        ))
        
        # Кнопка "Вперед"
        if current_page < total_pages:
            buttons.append(self.create_button(
                "Вперед ▶️",
                f"{callback_prefix}_{current_page + 1}",
                style=ButtonStyle.FORWARD
            ))
        
        # Додаткові кнопки
        if additional_buttons:
            buttons.extend(additional_buttons)
            
        return self.create_keyboard(buttons, columns=3)

    def create_confirmation_keyboard(self,
                                   confirm_callback: str,
                                   cancel_callback: str = "cancel",
                                   confirm_text: str = "✅ Підтвердити",
                                   cancel_text: str = "❌ Скасувати") -> UIKeyboard:
        """
        Створення клавіатури підтвердження
        
        Args:
            confirm_callback: Callback для підтвердження
            cancel_callback: Callback для скасування
            confirm_text: Текст кнопки підтвердження
            cancel_text: Текст кнопки скасування
            
        Returns:
            UIKeyboard: Клавіатура підтвердження
        """
        buttons = [
            self.create_button(confirm_text, confirm_callback, style=ButtonStyle.SUCCESS),
            self.create_button(cancel_text, cancel_callback, style=ButtonStyle.DANGER)
        ]
        
        return self.create_keyboard(buttons, columns=2)

    def create_menu_keyboard(self, 
                           menu_items: Dict[str, str],
                           back_callback: str = "back",
                           columns: int = 2) -> UIKeyboard:
        """
        Створення меню
        
        Args:
            menu_items: Словник пунктів меню {назва: callback}
            back_callback: Callback для кнопки "Назад"
            columns: Кількість колонок
            
        Returns:
            UIKeyboard: Клавіатура меню
        """
        buttons = []
        
        # Додавання пунктів меню
        for name, callback in menu_items.items():
            buttons.append(self.create_button(name, callback))
        
        # Кнопка "Назад"
        if back_callback:
            buttons.append(self.create_button(
                "◀️ Назад",
                back_callback,
                style=ButtonStyle.BACK
            ))
        
        return self.create_keyboard(buttons, columns=columns)

    def format_message(self,
                      text: str,
                      message_type: MessageType = MessageType.INFO,
                      title: Optional[str] = None,
                      data: Optional[Dict[str, Any]] = None,
                      footer: Optional[str] = None) -> str:
        """
        Форматування повідомлення
        
        Args:
            text: Основний текст
            message_type: Тип повідомлення
            title: Заголовок
            data: Дані для відображення
            footer: Нижній колонтитул
            
        Returns:
            str: Відформатоване повідомлення
        """
        # Іконка типу повідомлення
        icon = self.default_styles['message_icons'].get(message_type, "")
        
        # Формування повідомлення
        parts = []
        
        # Заголовок
        if title:
            parts.append(f"<b>{icon} {title}</b>\n")
        elif icon:
            parts.append(f"{icon} ")
        
        # Основний текст
        parts.append(text)
        
        # Дані
        if data:
            parts.append("\n\n📊 <b>Дані:</b>")
            for key, value in data.items():
                parts.append(f"• <b>{key}:</b> {value}")
        
        # Нижній колонтитул
        if footer:
            parts.append(f"\n\n<i>{footer}</i>")
        
        return "".join(parts)

    def format_list(self,
                   items: List[Any],
                   title: str = "Список",
                   item_formatter: Callable[[Any], str] = str,
                   max_items: int = 10,
                   numbered: bool = True) -> str:
        """
        Форматування списку
        
        Args:
            items: Елементи списку
            title: Заголовок списку
            item_formatter: Функція форматування елементів
            max_items: Максимальна кількість елементів
            numbered: Нумерований список
            
        Returns:
            str: Відформатований список
        """
        if not items:
            return f"<b>{title}</b>\n\n<i>Список порожній</i>"
        
        # Обмеження кількості елементів
        display_items = items[:max_items]
        
        # Формування списку
        lines = [f"<b>{title}</b> ({len(items)} елементів)\n"]
        
        for i, item in enumerate(display_items, 1):
            formatted_item = item_formatter(item)
            if numbered:
                lines.append(f"{i}. {formatted_item}")
            else:
                lines.append(f"• {formatted_item}")
        
        # Інформація про обрізання
        if len(items) > max_items:
            lines.append(f"\n<i>... та ще {len(items) - max_items} елементів</i>")
        
        return "\n".join(lines)

    def format_stats(self, 
                    stats: Dict[str, Any],
                    title: str = "Статистика") -> str:
        """
        Форматування статистики
        
        Args:
            stats: Словник статистики
            title: Заголовок
            
        Returns:
            str: Відформатована статистика
        """
        if not stats:
            return f"<b>{title}</b>\n\n<i>Немає даних</i>"
        
        lines = [f"📊 <b>{title}</b>\n"]
        
        for key, value in stats.items():
            # Форматування значення
            if isinstance(value, (int, float)):
                if value >= 1000000:
                    formatted_value = f"{value/1000000:.1f}M"
                elif value >= 1000:
                    formatted_value = f"{value/1000:.1f}K"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value)
            
            lines.append(f"• <b>{key}:</b> {formatted_value}")
        
        return "\n".join(lines)

    def format_progress_bar(self,
                          current: int,
                          total: int,
                          width: int = 10,
                          filled_char: str = "█",
                          empty_char: str = "░") -> str:
        """
        Створення прогрес-бару
        
        Args:
            current: Поточне значення
            total: Загальне значення
            width: Ширина бару
            filled_char: Символ заповнення
            empty_char: Символ порожнечі
            
        Returns:
            str: Прогрес-бар
        """
        if total == 0:
            return f"{empty_char * width} 0%"
        
        percentage = min(100, (current / total) * 100)
        filled_width = int((percentage / 100) * width)
        empty_width = width - filled_width
        
        bar = filled_char * filled_width + empty_char * empty_width
        return f"{bar} {percentage:.1f}%"

    def build_aiogram_keyboard(self, ui_keyboard: UIKeyboard) -> Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]:
        """
        Конвертація UIKeyboard в aiogram клавіатуру
        
        Args:
            ui_keyboard: UI клавіатура
            
        Returns:
            Aiogram клавіатура
        """
        try:
            if ui_keyboard.inline:
                builder = InlineKeyboardBuilder()
                
                for button in ui_keyboard.buttons:
                    if not button.enabled:
                        continue
                        
                    if button.url:
                        builder.button(text=button.text, url=button.url)
                    else:
                        builder.button(text=button.text, callback_data=button.callback_data)
                
                # Групування по рядках
                rows = {}
                for button in ui_keyboard.buttons:
                    if button.enabled:
                        row = button.row
                        if row not in rows:
                            rows[row] = 0
                        rows[row] += 1
                
                if rows:
                    builder.adjust(*rows.values())
                
                return builder.as_markup()
            else:
                builder = ReplyKeyboardBuilder()
                
                for button in ui_keyboard.buttons:
                    if button.enabled:
                        builder.button(text=button.text)
                
                return builder.as_markup(
                    one_time_keyboard=ui_keyboard.one_time,
                    resize_keyboard=ui_keyboard.resize,
                    selective=ui_keyboard.selective
                )
                
        except Exception as e:
            logger.error(f"Помилка створення aiogram клавіатури: {e}")
            # Повернення порожньої клавіатури у випадку помилки
            return InlineKeyboardMarkup(inline_keyboard=[])

    def create_admin_keyboard(self, user_is_admin: bool = False) -> UIKeyboard:
        """
        Створення адміністративної клавіатури
        
        Args:
            user_is_admin: Чи є користувач адміністратором
            
        Returns:
            UIKeyboard: Адміністративна клавіатура
        """
        if not user_is_admin:
            return self.create_keyboard([])
        
        buttons = [
            self.create_button("📊 Статистика", "admin_stats", ButtonStyle.INFO),
            self.create_button("👥 Користувачі", "admin_users", ButtonStyle.INFO),
            self.create_button("⚙️ Налаштування", "admin_settings", ButtonStyle.SETTINGS),
            self.create_button("🔄 Перезавантаження", "admin_reload", ButtonStyle.WARNING),
            self.create_button("💾 Бекап", "admin_backup", ButtonStyle.SUCCESS),
            self.create_button("🏠 Головне меню", "main_menu", ButtonStyle.HOME)
        ]
        
        return self.create_keyboard(buttons, columns=2)

    async def get_health_status(self) -> Dict[str, Any]:
        """Отримання статусу здоров'я модуля"""
        return {
            'status': 'healthy',
            'templates_count': len(self.templates),
            'last_check': datetime.now().isoformat()
        }
