"""Image processing service for creating personalized Christmas figures."""
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np

from config import settings
from services.ai_generator import AIImageGenerator
from services.face_swapper import FaceSwapper
from services.template_generator import TemplateGenerator

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process images and create personalized Christmas figures."""

    def __init__(self):
        """Initialize image processor."""
        self.templates_dir = settings.IMAGES_DIR / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        # Path to logo.png in project root
        self.logo_path = Path("logo.png")

        # Generation services (ordered by priority)
        self.template_generator = TemplateGenerator()
        self.ai_generator = AIImageGenerator()
        self.face_swapper = FaceSwapper()

    async def create_christmas_figure(
        self,
        user_photo_path: Path,
        gender: str,
        user_id: int
    ) -> Path:
        """
        Create personalized Christmas figure with user's face.

        Args:
            user_photo_path: Path to user's uploaded photo
            gender: User's gender ('male' or 'female')
            user_id: User ID for generating unique filename

        Returns:
            Path to generated image
        """
        try:
            # PRIORITY 1: Try professional 3D templates first (BEST QUALITY)
            try:
                logger.info(f"Trying template-based generation for user {user_id}")
                return await self.template_generator.generate_from_template(
                    user_photo_path, gender, user_id
                )
            except FileNotFoundError as template_error:
                logger.warning(f"Templates not found: {template_error}")
                # Fall through to AI generation
            except Exception as template_error:
                logger.error(f"Template generation failed: {template_error}")
                # Fall through to AI generation

            # PRIORITY 2: Try AI generation if templates not available
            if settings.AI_GENERATION_ENABLED and settings.OPENAI_API_KEY:
                logger.info(f"Using AI generation for user {user_id}")
                try:
                    # Generate base 3D figurine with DALL-E 3
                    base_image = await self.ai_generator.generate_figurine(
                        user_photo_path, gender, user_id
                    )

                    # Apply face swapping for realistic face replacement
                    output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
                    final_image = await self.face_swapper.swap_face(
                        base_image, user_photo_path, output_path
                    )

                    logger.info(f"AI generation successful for user {user_id}")
                    return final_image

                except Exception as ai_error:
                    logger.error(f"AI generation failed: {ai_error}, falling back to basic method")
                    # Fall through to basic method

            # PRIORITY 3: Fallback to basic template method
            logger.info(f"Using basic template method for user {user_id}")

            # Load user photo
            user_img = Image.open(user_photo_path)

            # Detect and extract face
            face_img = self._extract_face(user_img)

            if face_img is None:
                # If face detection fails, use simple circular crop
                face_img = self._create_circular_crop(user_img)

            # Load template based on gender
            template = self._load_template(gender)

            # Composite face onto template
            result = self._composite_face_on_template(template, face_img)

            # Save result
            output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
            result.save(output_path, "JPEG", quality=95)

            logger.info(f"Generated Christmas figure for user {user_id}")
            return output_path

        except Exception as e:
            logger.error(f"Error creating Christmas figure: {e}")
            # Return a default/placeholder image
            return self._create_placeholder(user_id)

    def _extract_face(self, img: Image.Image) -> Image.Image | None:
        """
        Extract face from image using OpenCV face detection.

        Args:
            img: PIL Image

        Returns:
            Cropped face image or None if no face detected
        """
        try:
            # Convert PIL to OpenCV format
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            # Load face cascade
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )

            # Detect faces
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) == 0:
                return None

            # Get the largest face
            face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = face

            # Add padding
            padding = int(w * 0.3)
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.width - x, w + 2 * padding)
            h = min(img.height - y, h + 2 * padding)

            # Crop face
            face_img = img.crop((x, y, x + w, y + h))

            # Resize to standard size
            face_img = face_img.resize((400, 400), Image.Resampling.LANCZOS)

            return face_img

        except Exception as e:
            logger.error(f"Error extracting face: {e}")
            return None

    def _create_circular_crop(self, img: Image.Image) -> Image.Image:
        """
        Create circular crop of the center of the image.

        Args:
            img: PIL Image

        Returns:
            Circular cropped image
        """
        # Calculate center square
        size = min(img.width, img.height)
        left = (img.width - size) // 2
        top = (img.height - size) // 2
        right = left + size
        bottom = top + size

        # Crop to square
        img_square = img.crop((left, top, right, bottom))

        # Resize
        img_square = img_square.resize((400, 400), Image.Resampling.LANCZOS)

        # Create circular mask
        mask = Image.new('L', (400, 400), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 400, 400), fill=255)

        # Apply mask
        output = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
        output.paste(img_square, (0, 0))
        output.putalpha(mask)

        return output

    def _load_template(self, gender: str) -> Image.Image:
        """
        Load Christmas figure template based on gender.

        Args:
            gender: 'male' or 'female'

        Returns:
            Template image
        """
        template_filename = f"figure_{gender}.png"
        template_path = self.templates_dir / template_filename

        if template_path.exists():
            return Image.open(template_path).convert("RGBA")

        # Create a simple placeholder template if not found
        return self._create_default_template()

    def _create_default_template(self) -> Image.Image:
        """
        Create a default template image.

        Returns:
            Default template image
        """
        # Create new image with Christmas background
        img = Image.new('RGB', (800, 1200), (18, 74, 90))  # Teal color

        draw = ImageDraw.Draw(img)

        # Draw simple figure body
        # Head area (circular placeholder for face)
        draw.ellipse((200, 100, 600, 500), fill=(255, 220, 177))

        # Body (rectangle for clothes)
        draw.rectangle((250, 480, 550, 900), fill=(0, 51, 102))

        # Add PRIDE34 text at bottom
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()

        text = "PRIDE34"
        draw.text((250, 1000), text, fill=(255, 140, 0), font=font)

        return img.convert("RGBA")

    def _composite_face_on_template(
        self,
        template: Image.Image,
        face: Image.Image
    ) -> Image.Image:
        """
        Composite face onto template with logo overlay.

        Args:
            template: Template image
            face: Face image

        Returns:
            Composited image with logo
        """
        # Create a copy of template
        result = template.copy()

        # Calculate position to place face (top center)
        face_x = (template.width - face.width) // 2
        face_y = 120  # Position from top

        # Paste face onto template
        if face.mode == 'RGBA':
            result.paste(face, (face_x, face_y), face)
        else:
            result.paste(face, (face_x, face_y))

        # Add logo overlay if logo.png exists
        if self.logo_path.exists():
            try:
                logo = Image.open(self.logo_path).convert("RGBA")

                # Resize logo to fit nicely (max 30% of image width)
                max_logo_width = int(result.width * 0.3)
                logo_aspect = logo.height / logo.width
                logo_width = min(logo.width, max_logo_width)
                logo_height = int(logo_width * logo_aspect)

                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

                # Position logo at bottom center
                logo_x = (result.width - logo_width) // 2
                logo_y = result.height - logo_height - 50

                # Paste logo with transparency
                result.paste(logo, (logo_x, logo_y), logo)

                logger.info("Logo overlay added successfully")

            except Exception as e:
                logger.error(f"Error adding logo overlay: {e}")

        return result.convert("RGB")

    def _create_placeholder(self, user_id: int) -> Path:
        """
        Create a placeholder image if processing fails.

        Args:
            user_id: User ID

        Returns:
            Path to placeholder image
        """
        img = Image.new('RGB', (800, 1200), (18, 74, 90))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()

        text = "С Новым 2026 годом!\nPRIDE34"
        draw.text((200, 500), text, fill=(255, 255, 255), font=font)

        # Add logo if exists
        if self.logo_path.exists():
            try:
                logo = Image.open(self.logo_path).convert("RGBA")

                # Resize logo
                max_logo_width = int(img.width * 0.3)
                logo_aspect = logo.height / logo.width
                logo_width = min(logo.width, max_logo_width)
                logo_height = int(logo_width * logo_aspect)

                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

                # Position logo at bottom center
                logo_x = (img.width - logo_width) // 2
                logo_y = img.height - logo_height - 50

                # Convert img to RGBA for logo pasting
                img = img.convert("RGBA")
                img.paste(logo, (logo_x, logo_y), logo)
                img = img.convert("RGB")

            except Exception as e:
                logger.error(f"Error adding logo to placeholder: {e}")

        output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
        img.save(output_path, "JPEG", quality=95)

        return output_path
