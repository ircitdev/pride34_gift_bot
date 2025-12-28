"""Service for updating .env file safely."""
import logging
from pathlib import Path
from typing import Optional
import shutil

logger = logging.getLogger(__name__)


class EnvUpdater:
    """Handle .env file updates safely with backup."""

    ENV_FILE = Path(".env")

    @classmethod
    def update_value(cls, key: str, value: str) -> bool:
        """
        Update a key-value pair in .env file.

        Args:
            key: Environment variable name
            value: New value

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup
            backup_path = cls.ENV_FILE.with_suffix('.env.backup')
            if cls.ENV_FILE.exists():
                shutil.copy(cls.ENV_FILE, backup_path)
                logger.info(f"Created backup: {backup_path}")

            # Read current content
            if not cls.ENV_FILE.exists():
                logger.error(".env file not found")
                return False

            lines = cls.ENV_FILE.read_text(encoding='utf-8').splitlines()

            # Find and update the key
            key_found = False
            new_lines = []

            for line in lines:
                # Skip empty lines and comments
                if not line.strip() or line.strip().startswith('#'):
                    new_lines.append(line)
                    continue

                # Check if this line contains our key
                if '=' in line:
                    current_key = line.split('=')[0].strip()
                    if current_key == key:
                        new_lines.append(f"{key}={value}")
                        key_found = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            # If key not found, append it
            if not key_found:
                new_lines.append(f"{key}={value}")
                logger.info(f"Key {key} not found, appending to .env")

            # Write back to file
            cls.ENV_FILE.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')

            logger.info(f"Successfully updated {key} in .env file")
            return True

        except Exception as e:
            logger.error(f"Error updating .env file: {e}")
            # Restore backup if exists
            if backup_path.exists():
                shutil.copy(backup_path, cls.ENV_FILE)
                logger.info("Restored .env from backup due to error")
            return False

    @classmethod
    def get_value(cls, key: str) -> Optional[str]:
        """
        Get value from .env file.

        Args:
            key: Environment variable name

        Returns:
            Value if found, None otherwise
        """
        try:
            if not cls.ENV_FILE.exists():
                return None

            lines = cls.ENV_FILE.read_text(encoding='utf-8').splitlines()

            for line in lines:
                if '=' in line and not line.strip().startswith('#'):
                    current_key, val = line.split('=', 1)
                    if current_key.strip() == key:
                        return val.strip()

            return None

        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
            return None
