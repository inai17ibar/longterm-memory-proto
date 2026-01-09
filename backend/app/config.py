"""
アプリケーション設定
データベースパスやその他の設定を一元管理
"""
import os
from pathlib import Path

# プロジェクトのルートディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent

# データディレクトリ
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = DATA_DIR / "databases"
PROFILES_DIR = DATA_DIR / "profiles"

# データベースファイルのパス
MEMORIES_DB_PATH = DATABASE_DIR / "memories.db"
KNOWLEDGE_BASE_DB_PATH = DATABASE_DIR / "knowledge_base.db"
USER_PROFILES_DB_PATH = DATABASE_DIR / "user_profiles.db"
EPISODIC_MEMORY_DB_PATH = DATABASE_DIR / "episodic_memory.db"

# JSONファイルのパス
EXTENDED_PROFILES_JSON_PATH = PROFILES_DIR / "extended_profiles.json"

# OpenAI設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_FALLBACK_MODEL = "gpt-4o-mini"

# メモリ設定
MAX_MEMORY_ITEMS = 100
MEMORY_IMPORTANCE_THRESHOLD = 0.15

# ログ設定
ENABLE_DEBUG_LOGGING = True
