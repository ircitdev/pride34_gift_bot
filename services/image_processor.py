"""Image processing service for creating personalized Christmas figures."""
import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import settings
from services.ai_generator import AIImageGenerator
from services.face_swapper import FaceSwapper
from services.template_generator import TemplateGenerator

logger = logging.getLogger(__name__)

# Constants for default template generation
DEFAULT_BG_COLOR: Tuple[int, int, int] = (18, 74, 90)  # Teal
DEFAULT_BODY_COLOR: Tuple[int, int, int] = (0, 51, 102)
DEFAULT_SKIN_COLOR: Tuple[int, int, int] = (255, 220, 177)
DEFAULT_TEXT_COLOR: Tuple[int, int, int] = (255, 140, 0)
FACE_SIZE: Tuple[int, int] = (400, 400)
CANVAS_SIZE: Tuple[int, int] = (800, 1200)


class ImageProcessor:
    """Process images and create personalized Christmas figures."""

    def __init__(self):
        """Initialize image processor."""
        self.templates_dir = settings.IMAGES_DIR / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.logo_path = Path("logo.png")
        self.font_path = Path("arial.ttf")

        # Initialize Services
        self.template_generator = TemplateGenerator()
        self.ai_generator = AIImageGenerator()
        self.face_swapper = FaceSwapper()

        # Pre-load resources to save time during request
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    async def create_christmas_figure(
        self,
        user_photo_path: Path,
        gender: str,
        user_id: int
    ) -> Path:
        """
        Create personalized Christmas figure using the best available method.

        Args:
            user_photo_path: Path to user's uploaded photo
            gender: User's gender ('male' or 'female')
            user_id: User ID for generating unique filename

        Returns:
            Path to generated image
        """
        # AI Generation (ONLY METHOD) - Gemini 2.0 + DALL-E 3
        # Templates are DISABLED per user request
        if settings.AI_GENERATION_ENABLED and settings.OPENAI_API_KEY:
            try:
                logger.info(f"🎨 Using AI Generation (Gemini 2.0 + DALL-E 3) for user {user_id}")
                return await self._generate_via_ai(user_photo_path, gender, user_id)
            except Exception as e:
                logger.error(f"❌ AI Generation failed: {e}", exc_info=True)
                # Re-raise exception to show user there was an error
                raise Exception(f"Не удалось сгенерировать открытку. Попробуйте другое фото.") from e
        else:
            logger.error(f"⚠️ AI generation is disabled or API key is missing!")
            raise Exception("AI генерация отключена. Обратитесь к администратору.")

    async def _generate_via_ai(self, user_photo_path: Path, gender: str, user_id: int) -> Path:
        """
        Handle AI generation workflow.

        Args:
            user_photo_path: Path to user's photo
            gender: User gender
            user_id: User ID

        Returns:
            Path to generated image
        """
        # AI генерирует готовую фигурку (face swap ОТКЛЮЧЕН)
        final_image = await self.ai_generator.generate_figurine(
            user_photo_path, gender, user_id
        )
        return final_image

    async def _generate_fallback(self, user_photo_path: Path, gender: str, user_id: int) -> Path:
        """
        Run CPU-bound fallback generation in a separate thread to prevent blocking.

        Args:
            user_photo_path: Path to user's photo
            gender: User gender
            user_id: User ID

        Returns:
            Path to generated image
        """
        return await asyncio.to_thread(
            self._process_fallback_sync, user_photo_path, gender, user_id
        )

    def _process_fallback_sync(self, user_photo_path: Path, gender: str, user_id: int) -> Path:
        """
        Synchronous implementation of fallback logic for thread execution.

        Args:
            user_photo_path: Path to user's photo
            gender: User gender
            user_id: User ID

        Returns:
            Path to generated image
        """
        try:
            user_img = Image.open(user_photo_path)

            # Detect face
            face_img = self._extract_face(user_img)
            if face_img is None:
                face_img = self._create_circular_crop(user_img)

            # Get template
            template = self._load_template(gender)

            # Composite
            result = self._composite_face_on_template(template, face_img)

            # Save
            output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
            result.save(output_path, "JPEG", quality=95)

            return output_path

        except Exception as e:
            logger.error(f"Fallback generation error: {e}")
            # Absolute last resort
            return self._create_placeholder(user_id)

    def _extract_face(self, img: Image.Image) -> Optional[Image.Image]:
        """
        Extract face using pre-loaded OpenCV cascade.

        Args:
            img: PIL Image

        Returns:
            Cropped face image or None if no face detected
        """
        try:
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) == 0:
                return None

            # Get largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

            # Add padding logic (cleaner calculation)
            padding = int(w * 0.3)
            left = max(0, x - padding)
            top = max(0, y - padding)
            right = min(img.width, x + w + padding)
            bottom = min(img.height, y + h + padding)

            face_img = img.crop((left, top, right, bottom))
            return face_img.resize(FACE_SIZE, Image.Resampling.LANCZOS)

        except Exception as e:
            logger.error(f"Error extracting face: {e}")
            return None

    def _create_circular_crop(self, img: Image.Image) -> Image.Image:
        """
        Create circular crop from center.

        Args:
            img: PIL Image

        Returns:
            Circular cropped image
        """
        size = min(img.size)

        # Center crop calculation
        left = (img.width - size) // 2
        top = (img.height - size) // 2
        img_square = img.crop((left, top, left + size, top + size))
        img_square = img_square.resize(FACE_SIZE, Image.Resampling.LANCZOS)

        # Create mask
        mask = Image.new('L', FACE_SIZE, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + FACE_SIZE, fill=255)

        # Apply mask
        output = Image.new('RGBA', FACE_SIZE, (0, 0, 0, 0))
        output.paste(img_square, (0, 0))
        output.putalpha(mask)
        return output

    def _load_template(self, gender: str) -> Image.Image:
        """
        Load template from disk or create default.

        Args:
            gender: 'male' or 'female'

        Returns:
            Template image
        """
        template_path = self.templates_dir / f"figure_{gender}.png"
        if template_path.exists():
            return Image.open(template_path).convert("RGBA")
        return self._create_default_template()

    def _composite_face_on_template(self, template: Image.Image, face: Image.Image) -> Image.Image:
        """
        Composite face and add logo.

        Args:
            template: Template image
            face: Face image

        Returns:
            Composited image with logo
        """
        result = template.copy()

        # Position logic
        face_x = (template.width - face.width) // 2
        face_y = 120

        # Paste face (handling transparency safely)
        if face.mode == 'RGBA':
            result.paste(face, (face_x, face_y), face)
        else:
            result.paste(face, (face_x, face_y))

        # Add Logo (Reusing the helper method)
        result = self._apply_logo_overlay(result)

        return result.convert("RGB")

    def _apply_logo_overlay(self, image: Image.Image) -> Image.Image:
        """
        Helper method to apply logo to any image (DRY principle).

        Args:
            image: Image to overlay logo on

        Returns:
            Image with logo overlay
        """
        if not self.logo_path.exists():
            return image

        try:
            # Prepare image for composition
            if image.mode != 'RGBA':
                base = image.convert("RGBA")
            else:
                base = image.copy()

            logo = Image.open(self.logo_path).convert("RGBA")

            # Calc dimensions (max 30% width)
            max_width = int(base.width * 0.3)
            ratio = max_width / logo.width
            new_size = (max_width, int(logo.height * ratio))

            logo = logo.resize(new_size, Image.Resampling.LANCZOS)

            # Position bottom center
            x = (base.width - new_size[0]) // 2
            y = base.height - new_size[1] - 50

            base.paste(logo, (x, y), logo)
            return base

        except Exception as e:
            logger.error(f"Logo overlay failed: {e}")
            return image

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        Load font safely.

        Args:
            size: Font size

        Returns:
            Font object
        """
        try:
            return ImageFont.truetype(str(self.font_path), size)
        except OSError:
            return ImageFont.load_default()

    def _create_default_template(self) -> Image.Image:
        """
        Draw a simple vector-style template.

        Returns:
            Default template image
        """
        img = Image.new('RGB', CANVAS_SIZE, DEFAULT_BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Draw generic body
        draw.ellipse((200, 100, 600, 500), fill=DEFAULT_SKIN_COLOR)  # Head area
        draw.rectangle((250, 480, 550, 900), fill=DEFAULT_BODY_COLOR)  # Body

        # Text
        font = self._get_font(60)
        text = "PRIDE34"

        # Calculate text position (approximate center)
        # Note: accurate text centering requires font.getbbox() in newer Pillow
        draw.text((250, 1000), text, fill=DEFAULT_TEXT_COLOR, font=font)

        return img.convert("RGBA")

    def _create_placeholder(self, user_id: int) -> Path:
        """
        Create emergency placeholder image.

        Args:
            user_id: User ID

        Returns:
            Path to placeholder image
        """
        img = Image.new('RGB', CANVAS_SIZE, DEFAULT_BG_COLOR)
        draw = ImageDraw.Draw(img)

        font = self._get_font(48)
        text = "С Новым 2026 годом!\nPRIDE34"

        draw.text((200, 500), text, fill=(255, 255, 255), font=font)

        # Apply logo using the helper
        img = self._apply_logo_overlay(img)

        output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
        img.convert("RGB").save(output_path, "JPEG", quality=95)
        return output_path
