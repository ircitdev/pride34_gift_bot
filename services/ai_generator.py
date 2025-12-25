"""AI-powered image generation service using OpenAI DALL-E 3."""
import logging
import aiohttp
import base64
from pathlib import Path
from PIL import Image
from io import BytesIO

from config import settings

logger = logging.getLogger(__name__)


class AIImageGenerator:
    """Generate realistic 3D figurine images using OpenAI DALL-E 3."""

    def __init__(self):
        """Initialize AI image generator."""
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/images/generations"

    async def generate_figurine(
        self,
        user_photo_path: Path,
        gender: str,
        user_id: int
    ) -> Path:
        """
        Generate 3D figurine with user's face using DALL-E 3.

        Args:
            user_photo_path: Path to user's uploaded photo
            gender: User's gender ('male' or 'female')
            user_id: User ID for generating unique filename

        Returns:
            Path to generated image
        """
        try:
            logger.info(f"Starting AI generation for user {user_id}, gender: {gender}")

            # Read user photo and encode to base64
            with open(user_photo_path, 'rb') as f:
                user_photo_data = f.read()

            # Create the prompt based on example
            prompt = self._create_prompt(gender)

            logger.info(f"Generated prompt: {prompt}")

            # Generate base figurine with DALL-E 3
            generated_image = await self._generate_with_dalle3(prompt)

            # Save the generated image
            output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
            generated_image.save(output_path, "JPEG", quality=95)

            logger.info(f"AI generation successful for user {user_id}")
            return output_path

        except Exception as e:
            logger.error(f"Error in AI generation: {e}")
            raise

    def _create_prompt(self, gender: str) -> str:
        """
        Create DALL-E prompt for generating 3D figurine.

        Args:
            gender: User's gender

        Returns:
            Detailed prompt optimized for DALL-E
        """
        # Optimized prompt following OpenAI best practices
        gender_clothing = {
            "male": "sporty blue and orange striped athletic outfit with track pants",
            "female": "sporty blue and orange striped athletic outfit with fitness leggings"
        }

        clothing = gender_clothing.get(gender, gender_clothing["male"])

        # Optimized prompt based on user feedback - generates template for face-swapping
        prompt = f"""A 3D glossy Christmas tree ornament hanging on a pine branch.

The ornament is a collectible vinyl toy figurine wearing a modern blue and orange striped athletic outfit, standing confidently in full body pose.

HEAD: Smooth blank mannequin head with NO facial features (no eyes, no nose, no mouth) in light skin tone for later face replacement.

BODY: {clothing}, glossy vinyl material with reflections and highlights.

BACKGROUND: Festive Christmas tree with warm bokeh lights, beautiful sparkles, pine branches visible.

STYLE: High quality 3D render, octane render quality, Pixar toy aesthetic, premium collectible figure, shiny ceramic/plastic texture.

TEXT: Bold orange text "PRIDE34" at the bottom of the image.

IMPORTANT: The head must be completely featureless and smooth like a mannequin.

Portrait orientation, photorealistic product photography."""

        return prompt

    async def _generate_with_dalle3(self, prompt: str) -> Image.Image:
        """
        Generate image using DALL-E 3 API.

        Args:
            prompt: Text prompt for generation

        Returns:
            PIL Image object
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1792",  # Portrait orientation like the example
            "quality": "hd",  # High quality for detailed renders
            "style": "natural"  # Natural for photorealistic product photography
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"DALL-E 3 API error: {error_text}")
                    raise Exception(f"DALL-E 3 API returned status {response.status}: {error_text}")

                result = await response.json()
                image_url = result['data'][0]['url']

                logger.info(f"DALL-E 3 generated image URL: {image_url}")

                # Download the generated image
                async with session.get(image_url) as img_response:
                    image_data = await img_response.read()
                    image = Image.open(BytesIO(image_data))

                    return image
