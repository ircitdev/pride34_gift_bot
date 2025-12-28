"""Template-based image generation with professional face-swapping."""
import logging
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class TemplateGenerator:
    """Generate personalized images using pre-made 3D templates."""

    def __init__(self):
        """Initialize template generator."""
        self.templates_dir = settings.IMAGES_DIR / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        # Paths to high-quality 3D templates
        # Try both naming conventions
        self.male_template = self._find_template("male")
        self.female_template = self._find_template("female")

    def _find_template(self, gender: str) -> Path:
        """Find template file with flexible naming."""
        possible_names = [
            f"figure_{gender}_3d.png",
            f"figure_{gender}.png",
            f"{gender}_3d.png",
            f"{gender}.png"
        ]

        for name in possible_names:
            path = self.templates_dir / name
            if path.exists():
                logger.info(f"Found template: {path}")
                return path

        # Return default path (will fail with clear error)
        return self.templates_dir / f"figure_{gender}_3d.png"

    async def generate_from_template(
        self,
        user_photo_path: Path,
        gender: str,
        user_id: int
    ) -> Path:
        """
        Generate personalized image using pre-made 3D template.

        Args:
            user_photo_path: Path to user's photo
            gender: User gender ('male' or 'female')
            user_id: User ID

        Returns:
            Path to generated image
        """
        try:
            # Load appropriate template
            template_path = self.male_template if gender == "male" else self.female_template

            if not template_path.exists():
                raise FileNotFoundError(
                    f"Template not found: {template_path}. "
                    "Please add 3D templates to images/templates/"
                )

            logger.info(f"Using template: {template_path}")

            # Load images
            template = cv2.imread(str(template_path))
            user_photo = cv2.imread(str(user_photo_path))

            if template is None:
                raise Exception(f"Failed to load template: {template_path}")
            if user_photo is None:
                raise Exception(f"Failed to load user photo: {user_photo_path}")

            # Extract and process user face
            user_face = self._extract_face(user_photo)
            if user_face is None:
                logger.warning("Face detection failed, using center crop")
                user_face = self._center_crop(user_photo)

            # Detect face region on template (blank head area)
            template_face_region = self._detect_template_face_region(template)

            # Perform high-quality face swap
            result = self._advanced_face_swap(template, user_face, template_face_region)

            # Logo is already in template, no need to add
            # result = self._add_logo(result)

            # Save result
            output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
            cv2.imwrite(str(output_path), result, [cv2.IMWRITE_JPEG_QUALITY, 95])

            logger.info(f"Template generation successful for user {user_id}")
            return output_path

        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            raise

    def _extract_face(self, img: np.ndarray) -> np.ndarray:
        """Extract face from user photo."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) == 0:
            return None

        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

        # Add MORE padding for better face framing (includes hair and neck)
        padding_w = int(w * 0.5)  # 50% horizontal padding
        padding_h = int(h * 0.6)  # 60% vertical padding for hair/neck

        x = max(0, x - padding_w)
        y = max(0, y - padding_h)
        w = min(img.shape[1] - x, w + 2 * padding_w)
        h = min(img.shape[0] - y, h + 2 * padding_h)

        return img[y:y+h, x:x+w]

    def _center_crop(self, img: np.ndarray) -> np.ndarray:
        """Fallback: center crop of image."""
        h, w = img.shape[:2]
        size = min(h, w)
        x = (w - size) // 2
        y = (h - size) // 2
        return img[y:y+size, x:x+size]

    def _detect_template_face_region(self, template: np.ndarray) -> tuple:
        """
        Detect where to place face on template.

        Точная замена головы на 3D-фигурке (как у конкурента)
        Голова должна быть КРУГЛОЙ, не вытянутой!
        """
        h, w = template.shape[:2]

        # Голова КРУГЛАЯ - ширина ≈ высоте
        # Размер ~17% от ширины шаблона для обоих измерений
        head_size = int(w * 0.17)  # 17% ширины (на 765px = ~130px)
        head_width = head_size
        head_height = head_size  # Квадрат для круглой головы!

        # Position - центр по горизонтали, 11% от верха (чтобы совпала с шеей)
        x = (w - head_width) // 2  # Центр по горизонтали
        y = int(h * 0.11)  # 11% от верха - ниже для лучшего совпадения с шеей

        logger.info(f"Template size: {w}x{h}, Face region: x={x}, y={y}, w={head_width}, h={head_height}")

        return (x, y, head_width, head_height)

    def _advanced_face_swap(
        self,
        template: np.ndarray,
        user_face: np.ndarray,
        face_region: tuple
    ) -> np.ndarray:
        """
        Advanced face swapping with color matching and seamless blending.
        """
        x, y, w, h = face_region

        # Resize user face to template head size
        face_resized = cv2.resize(user_face, (w, h), interpolation=cv2.INTER_LANCZOS4)

        # Color matching - match scene lighting
        template_roi = template[y:y+h, x:x+w].copy()
        face_matched = self._match_colors(face_resized, template_roi)

        # Create soft blending mask for natural edges
        mask = np.zeros((h, w), dtype=np.float32)
        center = (w // 2, h // 2)
        axes = (int(w * 0.45), int(h * 0.45))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 1, -1)
        mask = cv2.GaussianBlur(mask, (31, 31), 15)
        mask_3ch = cv2.merge([mask, mask, mask])

        # Blend with soft edges
        result = template.copy()
        blended = (face_matched * mask_3ch + template_roi * (1 - mask_3ch)).astype(np.uint8)
        result[y:y+h, x:x+w] = blended

        return result

    def _match_colors(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:
        """Match color distribution of source to target."""
        source_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype(np.float32)
        target_lab = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype(np.float32)

        # Match each channel
        for i in range(3):
            source_mean = source_lab[:, :, i].mean()
            source_std = source_lab[:, :, i].std()
            target_mean = target_lab[:, :, i].mean()
            target_std = target_lab[:, :, i].std()

            # Adjust
            source_lab[:, :, i] = (
                (source_lab[:, :, i] - source_mean) * (target_std / (source_std + 1e-6))
                + target_mean
            )

        source_lab = np.clip(source_lab, 0, 255).astype(np.uint8)
        return cv2.cvtColor(source_lab, cv2.COLOR_LAB2BGR)

    def _create_blend_mask(self, w: int, h: int) -> np.ndarray:
        """Create smooth blending mask."""
        mask = np.zeros((h, w), dtype=np.float32)

        # Elliptical mask
        center = (w // 2, h // 2)
        axes = (int(w * 0.48), int(h * 0.48))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 1, -1)

        # Heavy gaussian blur for seamless edges
        mask = cv2.GaussianBlur(mask, (99, 99), 30)

        return mask

    def _add_logo(self, img: np.ndarray) -> np.ndarray:
        """Add PRIDE34 logo to bottom of image."""
        logo_path = Path("logo.png")

        if not logo_path.exists():
            logger.warning("Logo not found, skipping")
            return img

        try:
            logo = cv2.imread(str(logo_path), cv2.IMREAD_UNCHANGED)
            if logo is None:
                return img

            # Resize logo
            logo_width = int(img.shape[1] * 0.25)
            aspect = logo.shape[0] / logo.shape[0]
            logo_height = int(logo_width * aspect)
            logo = cv2.resize(logo, (logo_width, logo_height))

            # Position at bottom center
            x = (img.shape[1] - logo_width) // 2
            y = img.shape[0] - logo_height - 30

            # Alpha blend if logo has alpha channel
            if logo.shape[2] == 4:
                alpha = logo[:, :, 3] / 255.0
                for c in range(3):
                    img[y:y+logo_height, x:x+logo_width, c] = (
                        alpha * logo[:, :, c] +
                        (1 - alpha) * img[y:y+logo_height, x:x+logo_width, c]
                    )
            else:
                img[y:y+logo_height, x:x+logo_width] = logo[:, :, :3]

        except Exception as e:
            logger.error(f"Error adding logo: {e}")

        return img
