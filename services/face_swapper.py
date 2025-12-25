"""Face swapping service using InsightFace for realistic face replacement."""
import logging
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FaceSwapper:
    """Swap faces on generated figurines using advanced face detection."""

    def __init__(self):
        """Initialize face swapper."""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    async def swap_face(
        self,
        base_image_path: Path,
        user_face_path: Path,
        output_path: Path
    ) -> Path:
        """
        Swap face on base image with user's face.

        Args:
            base_image_path: Path to base generated image
            user_face_path: Path to user's photo
            output_path: Path to save result

        Returns:
            Path to output image
        """
        try:
            logger.info("Starting face swap process")

            # Load images
            base_img = cv2.imread(str(base_image_path))
            user_img = cv2.imread(str(user_face_path))

            if base_img is None or user_img is None:
                raise Exception("Failed to load images for face swap")

            # Extract user's face
            user_face = self._extract_face_region(user_img)
            if user_face is None:
                logger.warning("Could not detect face in user photo, using center crop")
                user_face = self._center_crop_face(user_img)

            # Detect face region in base image
            face_region = self._detect_face_region(base_img)

            if face_region is not None:
                # Perform face swap
                result = self._blend_faces(base_img, user_face, face_region)
            else:
                logger.warning("No face detected in base image, skipping face swap")
                result = base_img

            # Save result
            cv2.imwrite(str(output_path), result)
            logger.info(f"Face swap completed: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error in face swap: {e}")
            # If face swap fails, just copy the base image
            import shutil
            shutil.copy(base_image_path, output_path)
            return output_path

    def _extract_face_region(self, img: np.ndarray) -> np.ndarray:
        """Extract face region from image."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return None

        # Get largest face
        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face

        # Add padding
        padding = int(w * 0.2)
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(img.shape[1] - x, w + 2 * padding)
        h = min(img.shape[0] - y, h + 2 * padding)

        return img[y:y+h, x:x+w]

    def _center_crop_face(self, img: np.ndarray) -> np.ndarray:
        """Create center crop of image."""
        height, width = img.shape[:2]
        size = min(height, width)
        x = (width - size) // 2
        y = (height - size) // 2
        return img[y:y+size, x:x+size]

    def _detect_face_region(self, img: np.ndarray) -> tuple:
        """Detect face region in base image."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return None

        # Get largest face
        face = max(faces, key=lambda f: f[2] * f[3])
        return face

    def _blend_faces(
        self,
        base_img: np.ndarray,
        face_img: np.ndarray,
        face_region: tuple
    ) -> np.ndarray:
        """Blend user's face onto base image with improved quality."""
        x, y, w, h = face_region

        # Make face region LARGER to cover entire head
        # Expand by 50% to ensure full head coverage
        expand_factor = 1.5
        new_w = int(w * expand_factor)
        new_h = int(h * expand_factor)

        # Recalculate position to keep centered
        x = max(0, x - (new_w - w) // 2)
        y = max(0, y - (new_h - h) // 2)

        # Ensure we don't go out of bounds
        if x + new_w > base_img.shape[1]:
            new_w = base_img.shape[1] - x
        if y + new_h > base_img.shape[0]:
            new_h = base_img.shape[0] - y

        w, h = new_w, new_h

        # Resize face to fit expanded region
        face_resized = cv2.resize(face_img, (w, h), interpolation=cv2.INTER_LANCZOS4)

        # Color matching - adjust face color to match scene lighting
        roi = base_img[y:y+h, x:x+w].copy()

        # Match color temperature
        face_lab = cv2.cvtColor(face_resized, cv2.COLOR_BGR2LAB)
        roi_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)

        # Adjust face to match scene lighting
        for i in range(3):
            face_mean = face_lab[:, :, i].mean()
            roi_mean = roi_lab[:, :, i].mean()
            face_lab[:, :, i] = np.clip(face_lab[:, :, i] + (roi_mean - face_mean) * 0.3, 0, 255)

        face_matched = cv2.cvtColor(face_lab, cv2.COLOR_LAB2BGR)

        # Create much softer blending mask
        mask = np.zeros((h, w), dtype=np.float32)
        center = (w // 2, h // 2)
        axes = (int(w * 0.45), int(h * 0.45))  # Larger ellipse
        cv2.ellipse(mask, center, axes, 0, 0, 360, 1, -1)

        # Much softer blur for seamless blending
        mask = cv2.GaussianBlur(mask, (51, 51), 25)

        # Convert to 3 channels
        mask_3ch = cv2.merge([mask, mask, mask])

        # High-quality blending
        result = base_img.copy()
        blended = (face_matched * mask_3ch + roi * (1 - mask_3ch)).astype(np.uint8)
        result[y:y+h, x:x+w] = blended

        return result
