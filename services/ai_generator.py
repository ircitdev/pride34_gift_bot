"""AI service: Gemini 2.0 Flash for Vision + DALL-E 3 for Generation."""
import logging
import base64
import aiohttp
from pathlib import Path
from PIL import Image
from io import BytesIO
from config import settings

logger = logging.getLogger(__name__)


class AIImageGenerator:
    """Generate figurines using Gemini 2.0 (vision) + DALL-E 3 (generation)."""

    def __init__(self):
        """Initialize AI image generator."""
        self.google_key = getattr(settings, 'NANO_BANANA_API_KEY', '')
        self.openai_key = settings.OPENAI_API_KEY

        # Используем Gemini 2.0 Flash для анализа фото
        # v1beta required for gemini-2.0-flash-exp
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

        # DALL-E 3 для рисования (стабильная генерация)
        self.dalle_url = "https://api.openai.com/v1/images/generations"

    async def generate_figurine(
        self,
        user_photo_path: Path,
        gender: str,
        user_id: int
    ) -> Path:
        """
        Generate 3D figurine using 2-step process:
        1. Gemini 2.0 analyzes photo
        2. DALL-E 3 generates figurine

        Args:
            user_photo_path: Path to user's uploaded photo
            gender: User's gender ('male' or 'female')
            user_id: User ID for generating unique filename

        Returns:
            Path to generated image
        """
        try:
            # --- ШАГ 1: Gemini 2.0 анализирует фото ---
            logger.info(f"🤖 User {user_id}: Analyzing face with Gemini 2.0 Flash...")

            with open(user_photo_path, 'rb') as f:
                b64_image = base64.b64encode(f.read()).decode('utf-8')

            # Просим Gemini описать внешность для DALL-E
            vision_prompt = """
Analyze this photo to help create a 3D toy figurine.
Describe the person's key facial features in 2-3 short sentences:
- Hair style and color
- Glasses (if present)
- Beard/mustache (if present)
- Distinctive facial characteristics

Keep it concise. Do not mention clothing or background.
"""

            # Запрос к Gemini 2.0
            description = await self._ask_gemini(vision_prompt, b64_image)
            logger.info(f"✅ Gemini description: {description}")

            # --- ШАГ 2: Формируем промпт для DALL-E ---
            full_prompt = self._create_dalle_prompt(gender, description)
            logger.info(f"📝 DALL-E prompt created for user {user_id}")

            # --- ШАГ 3: DALL-E 3 генерирует изображение ---
            logger.info(f"🎨 User {user_id}: Generating image with DALL-E 3...")
            generated_image = await self._generate_with_dalle(full_prompt)

            # Накладываем overlay.png поверх результата
            overlay_path = Path(__file__).parent.parent / "overlay.png"
            if overlay_path.exists():
                try:
                    overlay = Image.open(overlay_path).convert("RGBA")

                    # Конвертируем generated_image в RGBA для прозрачности
                    if generated_image.mode != 'RGBA':
                        generated_image = generated_image.convert('RGBA')

                    # Масштабируем overlay под размер generated_image если нужно
                    if overlay.size != generated_image.size:
                        overlay = overlay.resize(generated_image.size, Image.Resampling.LANCZOS)

                    # Накладываем overlay поверх
                    generated_image = Image.alpha_composite(generated_image, overlay)

                    logger.info(f"✅ Overlay applied for user {user_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to apply overlay: {e}")
            else:
                logger.warning(f"⚠️ Overlay not found at {overlay_path}")

            # Сохраняем результат (конвертируем в RGB для JPEG)
            output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
            if generated_image.mode == 'RGBA':
                generated_image = generated_image.convert('RGB')
            generated_image.save(output_path, "JPEG", quality=95)

            logger.info(f"✅ AI generation successful for user {user_id}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Error in AI generation for user {user_id}: {e}", exc_info=True)
            raise

    async def _ask_gemini(self, text: str, b64_img: str) -> str:
        """
        Send photo to Gemini 2.0 Flash for analysis.

        Args:
            text: Analysis prompt
            b64_img: Base64-encoded image

        Returns:
            Text description from Gemini
        """
        payload = {
            "contents": [{
                "parts": [
                    {"text": text},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}
                ]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 200
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.gemini_url,
                params={"key": self.google_key},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Gemini API error: {error_text}")
                    # ОБЯЗАТЕЛЬНО используем Gemini - без fallback
                    raise Exception(f"Gemini API failed: {error_text}")

                result = await response.json()
                logger.info(f"Gemini response: {str(result)[:200]}...")

                # Извлекаем текст ответа
                try:
                    return result['candidates'][0]['content']['parts'][0]['text'].strip()
                except (KeyError, IndexError) as e:
                    logger.error(f"Failed to parse Gemini response: {e}")
                    return "A person with distinctive features"

    async def _generate_with_dalle(self, prompt: str) -> Image.Image:
        """
        Generate image using DALL-E 3.

        Args:
            prompt: Image generation prompt

        Returns:
            PIL Image object
        """
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "size": "1024x1792",
            "quality": "hd",
            "style": "vivid",
            "n": 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.dalle_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"DALL-E API error: {error_text}")
                    raise Exception(f"DALL-E returned status {response.status}: {error_text}")

                result = await response.json()

                # Скачиваем изображение по URL
                image_url = result['data'][0]['url']
                logger.info(f"Downloading image from DALL-E: {image_url}")

                async with session.get(image_url) as img_response:
                    img_data = await img_response.read()
                    return Image.open(BytesIO(img_data))

    def _create_dalle_prompt(self, gender: str, face_description: str) -> str:
        """
        Create detailed prompt for DALL-E based on Gemini's analysis.
        Randomly selects one of 4 scene variations for variety.

        Args:
            gender: User's gender
            face_description: Description from Gemini

        Returns:
            Detailed prompt for DALL-E
        """
        import random

        gender_clothing = {
            "male": "sporty blue and orange striped athletic outfit with track pants",
            "female": "sporty blue and orange striped athletic outfit with fitness leggings"
        }
        clothing = gender_clothing.get(gender, gender_clothing["male"])

        # 4 different scene variations (inspired by templates but generated from scratch)
        scenes = [
            # Scene 1: Evening sled near cottage
            {
                "pose": "Sitting on a classic wooden sled with curved metal runners",
                "background": "Evening winter forest with snow-covered trees. Cozy wooden cottage with warm glowing windows in the distance",
                "lighting": "Soft evening twilight with warm golden glow from cottage windows",
                "atmosphere": "Magical evening atmosphere with bokeh lights and gentle snowfall"
            },
            # Scene 2: Standing fitness pose indoors
            {
                "pose": "Standing in a confident fitness pose with hands on hips or flexing muscles",
                "background": "Cozy indoor room with decorated Christmas tree, warm fireplace, colorful ornaments and garlands",
                "lighting": "Warm indoor lighting from fireplace and Christmas lights",
                "atmosphere": "Festive home atmosphere with Christmas decorations all around"
            },
            # Scene 3: Daytime sled in mountains
            {
                "pose": "Sitting on a classic wooden sled with curved metal runners",
                "background": "Bright sunny winter landscape with snowy mountains and pine forest",
                "lighting": "Bright natural daylight with clear blue sky",
                "atmosphere": "Fresh winter morning with sparkling snow and mountain scenery"
            },
            # Scene 4: Bodybuilder pose near tree
            {
                "pose": "Standing in a strong bodybuilder pose showing muscles (flexing biceps or victory pose)",
                "background": "Close-up view with decorated Christmas tree full of colorful ornaments and baubles",
                "lighting": "Bright Christmas lights creating colorful bokeh effect",
                "atmosphere": "Festive mood with vibrant Christmas tree decorations filling the background"
            }
        ]

        # Randomly select one scene
        selected_scene = random.choice(scenes)
        logger.info(f"🎲 Selected random scene variation: {scenes.index(selected_scene) + 1}/4")

        prompt = f"""IMPORTANT: VERTICAL portrait orientation image (tall, not wide).

A 3D stylized figurine in a magical Christmas scene.

CHARACTER DETAILS (based on photo analysis):
{face_description}

FIGURINE STYLE:
- Gender: {gender}
- 3D collectible toy style (like premium Christmas ornament figurine)
- Smooth semi-realistic features with stylized proportions
- Outfit: {clothing} with visible PRIDE34 logo on chest
- Friendly, cheerful expression
- NOT photorealistic, NOT real person - it's a TOY FIGURINE

POSE & POSITION:
- {selected_scene["pose"]}

BACKGROUND & SCENE:
- {selected_scene["background"]}

LIGHTING:
- {selected_scene["lighting"]}

ATMOSPHERE:
- {selected_scene["atmosphere"]}

VERTICAL COMPOSITION:
- VERTICAL portrait format with figurine taking most of frame
- Christmas tree branches with decorations at TOP of vertical frame
- Decorative Christmas wreath with PRIDE34 logo at BOTTOM of vertical frame
- Premium product photography quality

TECHNICAL STYLE:
- VERTICAL portrait orientation (1024x1792)
- High-quality 3D render
- Pixar/Disney toy aesthetic (like collectible Christmas figurines)
- Glossy smooth surfaces
- Depth of field with background blur
- Professional studio quality
- The style should match premium Christmas collectible figurines
"""
        return prompt
