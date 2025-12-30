"""Certificate generation service."""
import logging
import random
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from config import settings

logger = logging.getLogger(__name__)


class CertificateGenerator:
    """Service for generating certificates with user name and date."""

    def __init__(self):
        """Initialize certificate generator."""
        # Template folder
        self.template_folder = settings.IMAGES_DIR / "sert"

        # Get all templates from sert folder
        if self.template_folder.exists():
            self.templates = list(self.template_folder.glob("*.jpg"))
            if not self.templates:
                # Fallback to old template
                self.template_path = settings.IMAGES_DIR / "sertificate.jpg"
                logger.warning(f"No templates found in {self.template_folder}, using fallback")
            else:
                logger.info(f"Found {len(self.templates)} certificate templates")
                self.template_path = None  # Will be selected randomly
        else:
            # Fallback to old template
            self.template_path = settings.IMAGES_DIR / "sertificate.jpg"
            logger.warning(f"Template folder not found: {self.template_folder}")

        # Validate fallback template if no templates folder
        if self.template_path and not self.template_path.exists():
            raise FileNotFoundError(f"Certificate template not found: {self.template_path}")

    def _get_random_template(self) -> Path:
        """Get random template from available templates."""
        if hasattr(self, 'templates') and self.templates:
            selected = random.choice(self.templates)
            logger.info(f"Selected random template: {selected.name}")
            return selected
        else:
            return self.template_path

    async def generate_certificate(
        self,
        user_id: int,
        user_name: str,
        expiry_date: str
    ) -> Path:
        """
        Generate certificate with user name and expiry date.

        Args:
            user_id: User's Telegram ID
            user_name: User's full name for certificate
            expiry_date: Certificate expiry date

        Returns:
            Path to generated certificate
        """
        try:
            # Select random template
            selected_template = self._get_random_template()
            template = Image.open(selected_template)

            if template.mode != 'RGB':
                template = template.convert('RGB')

            draw = ImageDraw.Draw(template)
            font = self._load_font(settings.CERTIFICATE_FONT_SIZE)

            try:
                r, g, b = map(int, settings.CERTIFICATE_FONT_COLOR.split(','))
                font_color = (r, g, b)
            except:
                font_color = (0, 0, 0)

            # Draw user name
            self._draw_centered_text(
                draw,
                text=user_name,
                y=settings.CERTIFICATE_NAME_Y,
                font=font,
                color=font_color,
                template_width=template.width
            )

            # Format date like "15 января 2026"
            try:
                # Try multiple date formats
                date_obj = None
                for fmt in ["%Y-%m-%d", "%d-%m-%Y"]:
                    try:
                        date_obj = datetime.strptime(expiry_date, fmt)
                        break
                    except ValueError:
                        continue

                if date_obj:
                    # Russian month names
                    months_ru = {
                        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
                    }
                    # Format: DD month_name YYYY
                    day = date_obj.day
                    month_name = months_ru[date_obj.month]
                    year = date_obj.year
                    formatted_date = f"{day} {month_name} {year}"
                else:
                    formatted_date = expiry_date
            except Exception as e:
                logger.warning(f"Error parsing date '{expiry_date}': {e}")
                formatted_date = expiry_date

            # Draw date
            self._draw_centered_text(
                draw,
                text=formatted_date,
                y=settings.CERTIFICATE_DATE_Y,
                font=font,
                color=font_color,
                template_width=template.width
            )

            output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_certificate.jpg"
            template.save(output_path, quality=95)

            logger.info(f"Certificate generated for user {user_id}: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating certificate for user {user_id}: {e}")
            raise

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load font for text rendering (Roboto Regular preferred)."""
        font_paths = [
            # Roboto Regular (preferred)
            "C:/Windows/Fonts/Roboto-Regular.ttf",
            "/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf",
            "/usr/share/fonts/roboto/Roboto-Regular.ttf",
            # Fallbacks
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]

        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    logger.info(f"Using font: {font_path}")
                    return ImageFont.truetype(font_path, size)
            except Exception as e:
                logger.debug(f"Could not load font {font_path}: {e}")
                continue

        logger.warning("Could not load TrueType font, using default")
        return ImageFont.load_default()

    def _draw_centered_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont,
        color: tuple,
        template_width: int
    ):
        """Draw text centered horizontally."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (template_width - text_width) // 2
        draw.text((x, y), text, font=font, fill=color)
