"""Template-based image generation with professional face-swapping."""
import logging
import random
from pathlib import Path
from typing import Optional, Tuple
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

        # NEW: Directory with multiple templates
        self.new_templates_dir = settings.IMAGES_DIR / "new_templates"
        self.new_templates_dir.mkdir(exist_ok=True)

        # Paths to high-quality 3D templates (fallback)
        # Try both naming conventions
        self.male_template = self._find_template("male")
        self.female_template = self._find_template("female")

        # Pre-load face cascade classifier (performance optimization)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            logger.error("Failed to load Haar Cascade classifier")
            raise RuntimeError("Face detection cascade not loaded")

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

    def _get_random_template(self, gender: str) -> Path:
        """
        Get random template from new_templates directory.

        Args:
            gender: 'male' or 'female'

        Returns:
            Path to randomly selected template
        """
        # Look for templates with pattern: figure_{gender}*.png
        pattern = f"figure_{gender}*.png"
        templates = list(self.new_templates_dir.glob(pattern))

        if not templates:
            # Fallback to old templates
            logger.warning(f"No templates found in new_templates for {gender}, using fallback")
            return self.male_template if gender == "male" else self.female_template

        # Random selection
        selected = random.choice(templates)
        logger.info(f"Selected random template for {gender}: {selected.name}")
        return selected

    async def generate_from_template(
        self,
        user_photo_path: Path,
        gender: str,
        user_id: int
    ) -> Path:
        """
        Generate personalized image using pre-made 3D template (async wrapper).
        Выносит тяжелые CPU/IO операции в отдельный поток для неблокирующего выполнения.

        Args:
            user_photo_path: Path to user's photo
            gender: User gender ('male' or 'female')
            user_id: User ID

        Returns:
            Path to generated image
        """
        import asyncio
        from functools import partial

        # Запускаем синхронную обработку в executor (ThreadPoolExecutor)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # Использует default ThreadPoolExecutor
            partial(self._generate_sync, user_photo_path, gender, user_id)
        )

    def _generate_sync(
        self,
        user_photo_path: Path,
        gender: str,
        user_id: int
    ) -> Path:
        """
        Synchronous implementation of template generation.
        Performs actual CPU/IO intensive work without blocking event loop.
        """
        try:
            # Use random template selection from new_templates
            template_path = self._get_random_template(gender)

            if not template_path.exists():
                raise FileNotFoundError(
                    f"Template not found: {template_path}. "
                    "Please add 3D templates to images/new_templates/"
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

            # Perform professional face swap with Poisson Blending
            result = self._seamless_face_swap(template, user_face, template_face_region)

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

    def _extract_face(self, img: np.ndarray) -> Optional[np.ndarray]:
        """Extract face from user photo using pre-loaded cascade classifier."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Use pre-loaded cascade (instead of creating new instance each time)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )

        if len(faces) == 0:
            return None

        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

        # Add padding for better face framing (includes hair and neck)
        padding_w = int(w * 0.5)  # 50% horizontal padding
        padding_h = int(h * 0.6)  # 60% vertical padding for hair/neck

        # Расширяем регион с КОРРЕКТНЫМ учетом границ
        # (исправлено: теперь лицо центрируется правильно даже у края)
        x_start = max(0, x - padding_w)
        y_start = max(0, y - padding_h)
        x_end = min(img.shape[1], x + w + padding_w)
        y_end = min(img.shape[0], y + h + padding_h)

        return img[y_start:y_end, x_start:x_end]

    def _center_crop(self, img: np.ndarray) -> np.ndarray:
        """Fallback: center crop of image."""
        h, w = img.shape[:2]
        size = min(h, w)
        x = (w - size) // 2
        y = (h - size) // 2
        return img[y:y+size, x:x+size]

    def _detect_template_face_region(self, template: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Detect where to place face on template.

        Точная замена головы на 3D-фигурке (как у конкурента)
        Голова должна быть КРУГЛОЙ, не вытянутой!
        """
        h, w = template.shape[:2]

        # Синхронизировано с visualize_face_region.py
        # Размеры для естественной круглой головы
        head_width = int(w * 0.20)   # 20% ширины шаблона (было 0.17)
        head_height = int(w * 0.23)  # 23% ширины для учета волос (было 0.17)

        # Position - центр по горизонтали, 14% от верха + 20px смещение вниз
        x = (w - head_width) // 2  # Центр по горизонтали
        y = int(h * 0.14) + 20  # 14% от верха + 20px вниз для лучшего позиционирования

        logger.info(f"Template size: {w}x{h}, Face region: x={x}, y={y}, w={head_width}, h={head_height}")

        return (x, y, head_width, head_height)

    def _advanced_face_swap_legacy(
        self,
        template: np.ndarray,
        user_face: np.ndarray,
        face_region: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Legacy face swapping with color matching and Gaussian blur blending.
        Kept for comparison and fallback purposes.
        """
        x, y, w, h = face_region

        # Проверка границ шаблона (защита от краша)
        template_h, template_w = template.shape[:2]

        # Обрезаем регион если выходит за границы
        actual_h = min(h, template_h - y)
        actual_w = min(w, template_w - x)

        if actual_h != h or actual_w != w:
            logger.warning(
                f"Face region {w}x{h} at ({x},{y}) exceeds template bounds "
                f"{template_w}x{template_h}, adjusting to {actual_w}x{actual_h}"
            )
            w, h = actual_w, actual_h

        # Resize user face to ACTUAL region size (теперь гарантированно безопасно)
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

    def _match_colors_simple(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:
        """
        Simple LAB color transfer for L channel only.
        Preserves skin tone while adjusting brightness for seamlessClone.

        Args:
            source: Source image (user face)
            target: Target image (template ROI)

        Returns:
            Color-matched source image
        """
        source_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype(np.float32)
        target_lab = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype(np.float32)

        # Only adjust L channel (lightness) - preserves skin tone
        l_mean_src = source_lab[:, :, 0].mean()
        l_mean_tgt = target_lab[:, :, 0].mean()

        # Damping factor 0.6 prevents over-adjustment
        l_diff = (l_mean_tgt - l_mean_src) * 0.6
        source_lab[:, :, 0] = np.clip(source_lab[:, :, 0] + l_diff, 0, 255)

        return cv2.cvtColor(source_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    def _match_colors(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:
        """Match color distribution of source to target (legacy method for fallback)."""
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

    def _seamless_face_swap(
        self,
        template: np.ndarray,
        user_face: np.ndarray,
        face_region: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Professional face swapping using Poisson Blending (cv2.seamlessClone).

        This method provides superior quality compared to simple alpha blending:
        - Automatically adjusts lighting gradients
        - Seamless edges using gradient domain editing
        - Preserves texture details

        Args:
            template: Base template image
            user_face: Extracted user face region
            face_region: Target region (x, y, w, h)

        Returns:
            Template with face seamlessly blended
        """
        x, y, w, h = face_region

        # Bounds checking
        template_h, template_w = template.shape[:2]
        actual_h = min(h, template_h - y)
        actual_w = min(w, template_w - x)

        if actual_h != h or actual_w != w:
            logger.warning(
                f"Face region {w}x{h} at ({x},{y}) exceeds template bounds "
                f"{template_w}x{template_h}, adjusting to {actual_w}x{actual_h}"
            )
            w, h = actual_w, actual_h

        # Resize user face with high-quality interpolation
        user_face_resized = cv2.resize(user_face, (w, h), interpolation=cv2.INTER_LANCZOS4)

        # Create elliptical mask for natural face shape
        mask = np.zeros(user_face_resized.shape, dtype=np.uint8)
        center = (w // 2, h // 2)
        axes = (int(w * 0.45), int(h * 0.45))
        cv2.ellipse(mask, center, axes, 0, 0, 360, (255, 255, 255), -1)

        # Pre-color matching helps seamlessClone with large lighting differences
        template_roi = template[y:y+h, x:x+w]
        user_face_matched = self._match_colors_simple(user_face_resized, template_roi)

        # Calculate center point for seamless cloning
        clone_center = (x + w // 2, y + h // 2)

        try:
            # Poisson Blending - industry standard for face swapping
            result = cv2.seamlessClone(
                user_face_matched,
                template,
                mask,
                clone_center,
                cv2.NORMAL_CLONE  # NORMAL_CLONE for full texture replacement
            )
            logger.info("Seamless cloning successful")
            return result

        except cv2.error as e:
            # Fallback to manual blending if seamlessClone fails
            logger.warning(f"Seamless clone failed: {e}, using fallback blend")
            return self._fallback_blend(template, user_face_matched, (x, y, w, h), mask)

    def _fallback_blend(
        self,
        template: np.ndarray,
        face: np.ndarray,
        region: Tuple[int, int, int, int],
        mask: np.ndarray
    ) -> np.ndarray:
        """
        Fallback blending method if seamlessClone crashes.

        Uses Gaussian blur alpha blending as safe alternative.

        Args:
            template: Base template image
            face: Color-matched face to blend
            region: Target region (x, y, w, h)
            mask: Binary mask for blending

        Returns:
            Template with face blended using alpha blending
        """
        x, y, w, h = region
        result = template.copy()

        # Convert mask to float and apply strong blur
        mask_float = mask[:, :, 0].astype(np.float32) / 255.0
        mask_float = cv2.GaussianBlur(mask_float, (21, 21), 10)
        mask_3ch = cv2.merge([mask_float, mask_float, mask_float])

        # Alpha blending
        roi = result[y:y+h, x:x+w].astype(np.float32)
        face_float = face.astype(np.float32)
        blended = (face_float * mask_3ch + roi * (1 - mask_3ch)).astype(np.uint8)
        result[y:y+h, x:x+w] = blended

        logger.info("Fallback blending applied")
        return result

    def _create_blend_mask(self, w: int, h: int) -> np.ndarray:
        """
        Create smooth blending mask (legacy method).

        Args:
            w: Mask width
            h: Mask height

        Returns:
            Float mask with smooth edges
        """
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
            aspect = logo.shape[0] / logo.shape[1]  # Исправлено: высота / ширина
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
