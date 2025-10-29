"""
Quick script to verify configuration is loading correctly from .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file explicitly
env_path = Path(__file__).parent / ".env"
print(f"[INFO] Loading .env from: {env_path}")
print(f"[INFO] .env exists: {env_path.exists()}")
print()

load_dotenv(env_path)

# Check DATABASE_URL
db_url = os.getenv("DATABASE_URL", "NOT SET")
print("[CHECK] DATABASE_URL from os.getenv():")
if "postgresql" in db_url:
    # Mask sensitive info
    masked = db_url.split('@')[0] + '@***' if '@' in db_url else db_url[:50]
    print(f"   [OK] PostgreSQL (Neon): {masked}")
elif "sqlite" in db_url:
    print(f"   [WARN] SQLite: {db_url}")
else:
    print(f"   [ERROR] {db_url}")
print()

# Check via Settings class
print("[CHECK] DATABASE_URL via Settings class:")
try:
    from app.config import get_settings
    settings = get_settings()
    if "postgresql" in settings.DATABASE_URL:
        masked = settings.DATABASE_URL.split('@')[0] + '@***'
        print(f"   [OK] PostgreSQL (Neon): {masked}")
    elif "sqlite" in settings.DATABASE_URL:
        print(f"   [WARN] SQLite: {settings.DATABASE_URL}")
    else:
        print(f"   [ERROR] {settings.DATABASE_URL}")
except Exception as e:
    print(f"   [ERROR] {e}")
print()

# Check other env vars
print("[CHECK] Other environment variables:")
print(f"   GEMINI_API_KEY: {'[OK] Set' if os.getenv('GEMINI_API_KEY') else '[ERROR] Not set'}")
print(f"   DEBUG: {os.getenv('DEBUG', 'not set')}")
print(f"   APP_NAME: {os.getenv('APP_NAME', 'not set')}")
