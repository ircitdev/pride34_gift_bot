"""Face swapping service using OpenCV with Seamless Cloning for realistic face replacement."""
import logging
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FaceSwapper:
    """Swap faces on generated figurines using advanced face detection and Poisson Blending."""

    def __init__(self):
        """Initialize face swapper with frontal and profile cascades."""
        cv_data = cv2.data.haarcascades
        self.frontal_cascade = cv2.CascadeClassifier(
            cv_data + 'haarcascade_frontalface_default.xml'
        )
        self.profile_cascade = cv2.CascadeClassifier(
            cv_data + 'haarcascade_profileface.xml'
        )

        if self.frontal_cascade.empty():
            logger.error("Failed to load frontal face cascade")
        if self.profile_cascade.empty():
            logger.warning("Failed to load profile face cascade, will use frontal only")

    async def swap_face(
        self,
        base_image_path: Path,
        user_face_path: Path,
        output_path: Path
    ) -> Path:
        """
        Swap face on base image with user's face using Seamless Cloning.

        Args:
            base_image_path: Path to base generated image
            user_face_path: Path to user's photo
            output_path: Path to save result

        Returns:
            Path to output image
        """
        try:
            logger.info(f"Starting face swap: {base_image_path.name} + {user_face_path.name}")

            # Validate input files
            if not base_image_path.exists() or not user_face_path.exists():
                raise FileNotFoundError("Input images not found")

            # Load images
            base_img = cv2.imread(str(base_image_path))
            user_img = cv2.imread(str(user_face_path))

            if base_img is None or user_img is None:
                raise ValueError("Failed to read image data (corrupted files?)")

            # Extract user's face with robust detection
            user_face = self._extract_face_region(user_img)
            if user_face is None:
                logger.warning("Could not detect face in user photo, using center crop")
                user_face = self._center_crop_face(user_img)

            # Detect face region in base image
            face_region = self._detect_face_region(base_img)

            if face_region is not None:
                # Perform face swap with Seamless Cloning
                result = self._seamless_blend_faces(base_img, user_face, face_region)
            else:
                logger.warning("No face detected in base image, skipping face swap")
                result = base_img

            # Save result
            cv2.imwrite(str(output_path), result, [cv2.IMWRITE_JPEG_QUALITY, 95])
            logger.info(f"Face swap completed: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error in face swap: {e}", exc_info=True)
            # If face swap fails, copy the base image as fallback
            import shutil
            if base_image_path.exists():
                shutil.copy(base_image_path, output_path)
            return output_path

    def _extract_face_region(self, img: np.ndarray) -> np.ndarray:
        """
        Extract face region from image with robust detection.
        Tries frontal cascade first, then profile cascade.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Try frontal face detection first
        faces = self.frontal_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        # If frontal fails, try profile detection
        if len(faces) == 0 and not self.profile_cascade.empty():
            faces = self.profile_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

        if len(faces) == 0:
            return None

        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

        # Add padding for better face framing (включая волосы и шею)
        padding_w = int(w * 0.3)  # 30% horizontal padding
        padding_h = int(h * 0.4)  # 40% vertical padding

        # Расширяем регион с КОРРЕКТНЫМ учетом границ
        # (аналогично исправлению в template_generator.py)
        x_start = max(0, x - padding_w)
        y_start = max(0, y - padding_h)
        x_end = min(img.shape[1], x + w + padding_w)
        y_end = min(img.shape[0], y + h + padding_h)

        return img[y_start:y_end, x_start:x_end]

    def _center_crop_face(self, img: np.ndarray) -> np.ndarray:
        """Create center crop of image."""
        height, width = img.shape[:2]
        size = min(height, width)
        x = (width - size) // 2
        y = (height - size) // 2
        return img[y:y+size, x:x+size]

    def _detect_face_region(self, img: np.ndarray) -> tuple:
        """
        Detect face region in base image.
        Returns (x, y, w, h) tuple or None.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Try frontal detection
        faces = self.frontal_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)
        )

        # Try profile if frontal fails
        if len(faces) == 0 and not self.profile_cascade.empty():
            faces = self.profile_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)
            )

        if len(faces) == 0:
            return None

        # Get largest face
        return max(faces, key=lambda f: f[2] * f[3])

    def _seamless_blend_faces(
        self,
        base_img: np.ndarray,
        face_img: np.ndarray,
        face_region: tuple
    ) -> np.ndarray:
        """
        Blend user's face onto base image using Seamless Cloning (Poisson Blending).

        This method:
        1. Preserves aspect ratio to prevent distortion
        2. Uses cv2.seamlessClone for realistic lighting/color integration
        3. Handles edge cases with proper bounds checking
        """
        x, y, w, h = face_region

        # Calculate expansion to cover entire head
        expand_factor = 1.5
        target_w = int(w * expand_factor)

        # PRESERVE ASPECT RATIO of user's face
        face_h, face_w = face_img.shape[:2]
        aspect_ratio = face_w / face_h
        target_h = int(target_w / aspect_ratio)

        # Recalculate position to keep centered
        x_offset = (target_w - w) // 2
        y_offset = (target_h - h) // 2
        x = max(0, x - x_offset)
        y = max(0, y - y_offset)

        # Bounds checking - ensure region fits within base image
        base_h, base_w = base_img.shape[:2]

        if x + target_w > base_w:
            target_w = base_w - x
        if y + target_h > base_h:
            target_h = base_h - y

        # Recalculate height maintaining aspect ratio after width adjustment
        if target_w != int(w * expand_factor):
            target_h = int(target_w / aspect_ratio)
            if y + target_h > base_h:
                target_h = base_h - y

        # Resize user's face to target size
        face_resized = cv2.resize(
            face_img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4
        )

        # Create mask for seamlessClone (elliptical shape for natural blending)
        mask = np.zeros(face_resized.shape[:2], dtype=np.uint8)
        center_mask = (target_w // 2, target_h // 2)
        axes_mask = (int(target_w * 0.45), int(target_h * 0.45))
        cv2.ellipse(mask, center_mask, axes_mask, 0, 0, 360, 255, -1)

        # Calculate center point in destination image
        dest_center = (x + target_w // 2, y + target_h // 2)

        # Perform Poisson Blending (Seamless Clone)
        try:
            result = cv2.seamlessClone(
                face_resized,
                base_img,
                mask,
                dest_center,
                cv2.NORMAL_CLONE  # NORMAL_CLONE for full replacement
            )
            logger.info("Seamless cloning successful")
            return result

        except cv2.error as e:
            # Fallback to manual blending if seamlessClone fails
            logger.warning(f"Seamless clone failed: {e}, using fallback blending")
            return self._fallback_blend(base_img, face_resized, x, y, mask)

    def _fallback_blend(
        self,
        base_img: np.ndarray,
        face_img: np.ndarray,
        x: int,
        y: int,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        Fallback blending method using color matching + alpha blending.
        Used when seamlessClone fails (e.g., face near image border).
        """
        h, w = face_img.shape[:2]

        # Get ROI from base image
        roi = base_img[y:y+h, x:x+w].copy()

        # Color matching in LAB space (improved version from template_generator.py)
        face_lab = cv2.cvtColor(face_img, cv2.COLOR_BGR2LAB).astype(np.float32)
        roi_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB).astype(np.float32)

        # Match each channel (mean + std)
        for i in range(3):
            face_mean = face_lab[:, :, i].mean()
            face_std = face_lab[:, :, i].std()
            roi_mean = roi_lab[:, :, i].mean()
            roi_std = roi_lab[:, :, i].std()

            # Adjust both mean and std
            face_lab[:, :, i] = (
                (face_lab[:, :, i] - face_mean) * (roi_std / (face_std + 1e-6))
                + roi_mean
            )

        face_lab = np.clip(face_lab, 0, 255).astype(np.uint8)
        face_matched = cv2.cvtColor(face_lab, cv2.COLOR_LAB2BGR)

        # Create soft blending mask
        mask_float = mask.astype(np.float32) / 255.0
        mask_float = cv2.GaussianBlur(mask_float, (51, 51), 25)
        mask_3ch = cv2.merge([mask_float, mask_float, mask_float])

        # Blend
        result = base_img.copy()
        blended = (face_matched * mask_3ch + roi * (1 - mask_3ch)).astype(np.uint8)
        result[y:y+h, x:x+w] = blended

        return result
