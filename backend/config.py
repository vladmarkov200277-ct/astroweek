import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
WEBAPP_URL: str = os.getenv("WEBAPP_URL", "")   # HTTPS URL вашего фронтенда

# Claude API
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = "claude-opus-4-6"

# Server
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
# Render задаёт PORT автоматически; локально используем 8000
API_PORT: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))

# Geopy (для определения координат города)
GEOPY_USER_AGENT: str = "astroweek_bot/1.0"
