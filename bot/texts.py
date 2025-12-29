"""Text management module for bot messages."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

TEXTS_FILE = Path(__file__).parent / "texts.json"


class TextManager:
    """Manages bot texts from JSON file."""

    _texts: Dict[str, Any] = {}

    @classmethod
    def load_texts(cls) -> None:
        """Load texts from JSON file."""
        try:
            with open(TEXTS_FILE, 'r', encoding='utf-8') as f:
                cls._texts = json.load(f)
            logger.info("Texts loaded successfully")
        except FileNotFoundError:
            logger.error(f"Texts file not found: {TEXTS_FILE}")
            cls._texts = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding texts JSON: {e}")
            cls._texts = {}

    @classmethod
    def save_texts(cls) -> bool:
        """Save texts to JSON file."""
        try:
            with open(TEXTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(cls._texts, f, ensure_ascii=False, indent=2)
            logger.info("Texts saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving texts: {e}")
            return False

    @classmethod
    def get(cls, path: str, default: str = "") -> str:
        """
        Get text by path.

        Args:
            path: Dot-separated path (e.g., 'welcome.text', 'quiz.question_1.text')
            default: Default value if path not found

        Returns:
            Text value
        """
        if not cls._texts:
            cls.load_texts()

        keys = path.split('.')
        value = cls._texts

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value if isinstance(value, str) else default

    @classmethod
    def get_list(cls, path: str) -> List[str]:
        """
        Get list of texts by path.

        Args:
            path: Dot-separated path (e.g., 'quiz.question_1.options')

        Returns:
            List of text values
        """
        if not cls._texts:
            cls.load_texts()

        keys = path.split('.')
        value = cls._texts

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return []

        return value if isinstance(value, list) else []

    @classmethod
    def set(cls, path: str, value: Any) -> bool:
        """
        Set text by path.

        Args:
            path: Dot-separated path
            value: New value

        Returns:
            True if successful
        """
        if not cls._texts:
            cls.load_texts()

        keys = path.split('.')
        data = cls._texts

        # Navigate to the parent
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]

        # Set the value
        data[keys[-1]] = value

        return cls.save_texts()

    @classmethod
    def get_all_editable_texts(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all editable texts with their paths and descriptions.

        Returns:
            Dictionary with text info
        """
        if not cls._texts:
            cls.load_texts()

        editable = {}

        # Welcome message
        editable['welcome'] = {
            'path': 'welcome.text',
            'title': 'Приветственное сообщение',
            'current': cls.get('welcome.text'),
            'description': cls.get('welcome.description')
        }

        # Quiz questions
        for i in range(1, 6):
            q_key = f'question_{i}'
            editable[f'quiz_q{i}_text'] = {
                'path': f'quiz.{q_key}.text',
                'title': f'Вопрос {i}',
                'current': cls.get(f'quiz.{q_key}.text'),
                'description': cls.get(f'quiz.{q_key}.description')
            }

            # Options for each question
            for j in range(4):
                editable[f'quiz_q{i}_opt{j}'] = {
                    'path': f'quiz.{q_key}.options.{j}',
                    'title': f'Вопрос {i} - Вариант {j+1}',
                    'current': cls.get_list(f'quiz.{q_key}.options')[j] if j < len(cls.get_list(f'quiz.{q_key}.options')) else '',
                    'description': f'Вариант ответа {j+1} для вопроса {i}'
                }

        # Gender selection
        editable['gender'] = {
            'path': 'gender.text',
            'title': 'Выбор пола',
            'current': cls.get('gender.text'),
            'description': cls.get('gender.description')
        }

        # Photo request
        editable['photo'] = {
            'path': 'photo.text',
            'title': 'Запрос фото',
            'current': cls.get('photo.text'),
            'description': cls.get('photo.description')
        }

        # Predictions
        predictions = ['fitness_enthusiast', 'balanced_lifestyle', 'sweet_lover', 'beginner', 'default']
        for pred in predictions:
            editable[f'prediction_{pred}'] = {
                'path': f'predictions.{pred}',
                'title': f'Предсказание: {pred}',
                'current': cls.get(f'predictions.{pred}'),
                'description': f'Предсказание для категории {pred}'
            }

        # Buttons
        editable['button_start'] = {
            'path': 'buttons.start',
            'title': 'Кнопка "Начать"',
            'current': cls.get('buttons.start'),
            'description': 'Текст кнопки начала квиза'
        }

        return editable

    @classmethod
    def get_categories(cls) -> List[Dict[str, str]]:
        """Get list of text categories for menu."""
        return [
            {'key': 'welcome', 'title': '👋 Приветствие', 'callback': 'edit_text_welcome'},
            {'key': 'quiz', 'title': '❓ Вопросы квиза', 'callback': 'edit_text_quiz'},
            {'key': 'gender', 'title': '👤 Выбор пола', 'callback': 'edit_text_gender'},
            {'key': 'photo', 'title': '📸 Запрос фото', 'callback': 'edit_text_photo'},
            {'key': 'predictions', 'title': '🔮 Предсказания', 'callback': 'edit_text_predictions'},
            {'key': 'buttons', 'title': '🔘 Кнопки', 'callback': 'edit_text_buttons'},
        ]


# Initialize on import
TextManager.load_texts()
