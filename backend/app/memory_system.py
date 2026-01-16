"""
LangChainベースの高度な記憶システム
"""

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app.config import MEMORIES_DB_PATH

try:
    # LangChain imports (graceful fallback if not installed)
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.llms import OpenAI
    from langchain.memory import ConversationSummaryBufferMemory
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import Chroma

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not available, using fallback memory system")


@dataclass
class MemoryItem:
    """記憶アイテムの構造化されたデータクラス"""

    id: str
    user_id: str
    content: str
    memory_type: str  # emotional_state, goals, symptoms, etc.
    importance_score: float  # 0.0 - 1.0（保存時の基本重要度）
    timestamp: datetime
    metadata: dict[str, Any]
    embedding_vector: Optional[list[float]] = None

    def get_current_importance(self) -> float:
        """時間減衰を考慮した現在の重要度を取得"""
        days_ago = (datetime.now() - self.timestamp).days

        # 時間減衰係数（エビングハウスの忘却曲線に近い形）
        if days_ago == 0:
            decay_factor = 1.0  # 今日: 減衰なし
        elif days_ago <= 1:
            decay_factor = 0.95  # 1日: 5%減衰
        elif days_ago <= 7:
            decay_factor = 0.85  # 1週間: 15%減衰
        elif days_ago <= 30:
            decay_factor = 0.65  # 1ヶ月: 35%減衰
        elif days_ago <= 90:
            decay_factor = 0.45  # 3ヶ月: 55%減衰
        else:
            decay_factor = 0.25  # 3ヶ月以上: 75%減衰

        # 一部の記憶タイプは減衰しにくい（慢性的な症状や目標など）
        persistent_types = ["symptoms", "goals", "medication", "personality", "work_status"]
        if self.memory_type in persistent_types:
            decay_factor = max(decay_factor, 0.7)  # 最低でも70%は維持

        return self.importance_score * decay_factor


class MemoryImportanceCalculator:
    """記憶の重要度を計算するクラス"""

    # 記憶タイプ別の基本重要度
    TYPE_IMPORTANCE_WEIGHTS = {
        "emotional_state": 0.9,
        "symptoms": 0.8,
        "goals": 0.7,
        "triggers": 0.8,
        "coping_methods": 0.6,
        "support_system": 0.5,
        "work_status": 0.7,
        "medication": 0.8,
        "concerns": 0.9,
        "experiences": 0.6,
        "personality": 0.4,
        "daily_routine": 0.3,
        "family": 0.4,
        "age": 0.2,
        "location": 0.1,
    }

    # 感情に関連するキーワードの重要度
    EMOTIONAL_KEYWORDS = {
        "high": ["不安", "苦しい", "辛い", "死にたい", "絶望", "パニック", "発作", "限界"],
        "medium": ["心配", "悩み", "困った", "疲れた", "ストレス", "落ち込み", "憂鬱"],
        "low": ["気になる", "少し", "ちょっと", "時々"],
    }

    @classmethod
    def calculate_importance(
        cls, content: str, memory_type: str, metadata: dict[str, Any] = None
    ) -> float:
        """記憶の重要度を計算"""
        if metadata is None:
            metadata = {}

        # 基本重要度（記憶タイプベース）
        base_score = cls.TYPE_IMPORTANCE_WEIGHTS.get(memory_type, 0.5)

        # 感情的な重要度
        emotional_score = cls._calculate_emotional_importance(content)

        # 時間的な重要度（新しいほど重要）
        temporal_score = cls._calculate_temporal_importance(metadata.get("timestamp"))

        # 文章の長さによる重要度
        length_score = cls._calculate_length_importance(content)

        # 最終スコア計算（乗算方式で差を強調）
        # base_scoreをベースに、他の要素で調整
        multiplier = 1.0

        # 感情スコアが高い場合は大幅に重要度を上げる
        if emotional_score >= 0.9:
            multiplier *= 1.5
        elif emotional_score >= 0.6:
            multiplier *= 1.2
        elif emotional_score <= 0.4:
            multiplier *= 0.7  # 「少し〜」などの弱い表現
        elif emotional_score <= 0.3:
            multiplier *= 0.5  # 非常に弱い表現

        # 新しい記憶は重要度を上げる（ただし感情スコアが低い場合は控えめに）
        if temporal_score >= 0.8 and emotional_score >= 0.5:
            multiplier *= 1.3
        elif temporal_score <= 0.3:
            multiplier *= 0.6

        # 長い文章は詳細情報として重要度を上げる
        if length_score >= 0.8:
            multiplier *= 1.1

        final_score = base_score * multiplier

        return min(max(final_score, 0.1), 1.0)

    @classmethod
    def _calculate_emotional_importance(cls, content: str) -> float:
        """感情的な重要度を計算"""
        content_lower = content.lower()

        high_count = sum(1 for word in cls.EMOTIONAL_KEYWORDS["high"] if word in content_lower)
        medium_count = sum(1 for word in cls.EMOTIONAL_KEYWORDS["medium"] if word in content_lower)
        low_count = sum(1 for word in cls.EMOTIONAL_KEYWORDS["low"] if word in content_lower)

        # 弱める表現があれば、感情強度を下げる
        if low_count > 0:
            if high_count > 0:
                return 0.6  # 「少し不安」など
            elif medium_count > 0:
                return 0.4  # 「少し心配」など
            else:
                return 0.3  # 「少し気になる」など

        if high_count > 0:
            return 0.9
        elif medium_count > 0:
            return 0.6
        else:
            return 0.5

    @classmethod
    def _calculate_temporal_importance(cls, timestamp_str: Optional[str]) -> float:
        """時間的な重要度を計算（新しいほど重要）"""
        if not timestamp_str:
            return 0.5

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            days_ago = (datetime.now() - timestamp).days

            # 1日以内は最高重要度、30日で半減
            if days_ago <= 1:
                return 1.0
            elif days_ago <= 7:
                return 0.8
            elif days_ago <= 30:
                return 0.6
            else:
                return 0.3
        except:
            return 0.5

    @classmethod
    def _calculate_length_importance(cls, content: str) -> float:
        """文章の長さによる重要度"""
        length = len(content)
        if length > 100:
            return 0.8
        elif length > 50:
            return 0.6
        elif length > 20:
            return 0.4
        else:
            return 0.2


class LangChainMemorySystem:
    """LangChainベースの高度な記憶システム（SQLite永続化対応）"""

    def __init__(self, openai_api_key: Optional[str] = None, db_path: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.vector_store = None
        self.embeddings = None
        self.llm = None
        self.memory_items: dict[str, list[MemoryItem]] = {}
        self.db_path = str(db_path or MEMORIES_DB_PATH)

        # SQLiteデータベースを初期化
        self._initialize_database()

        # 既存の記憶を読み込み
        self._load_memories_from_db()

        if LANGCHAIN_AVAILABLE and self.openai_api_key:
            self._initialize_langchain()
        else:
            print("Using fallback memory system")

    def _initialize_database(self):
        """SQLiteデータベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                importance_score REAL NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
        """
        )

        # インデックスを作成してパフォーマンス向上
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")

        conn.commit()
        conn.close()
        print(f"SQLite database initialized at {self.db_path}")

    def _load_memories_from_db(self):
        """データベースから記憶を読み込み"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, user_id, content, memory_type, importance_score, timestamp, metadata FROM memories"
        )
        rows = cursor.fetchall()

        for row in rows:
            (
                memory_id,
                user_id,
                content,
                memory_type,
                importance_score,
                timestamp_str,
                metadata_str,
            ) = row

            memory_item = MemoryItem(
                id=memory_id,
                user_id=user_id,
                content=content,
                memory_type=memory_type,
                importance_score=importance_score,
                timestamp=datetime.fromisoformat(timestamp_str),
                metadata=json.loads(metadata_str),
            )

            if user_id not in self.memory_items:
                self.memory_items[user_id] = []
            self.memory_items[user_id].append(memory_item)

        conn.close()
        print(f"Loaded {len(rows)} memories from database")

    def _save_memory_to_db(self, memory: MemoryItem):
        """単一の記憶をデータベースに保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO memories (id, user_id, content, memory_type, importance_score, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                memory.id,
                memory.user_id,
                memory.content,
                memory.memory_type,
                memory.importance_score,
                memory.timestamp.isoformat(),
                json.dumps(memory.metadata, ensure_ascii=False),
            ),
        )

        conn.commit()
        conn.close()

    def _initialize_langchain(self):
        """LangChainコンポーネントを初期化"""
        try:
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            self.llm = OpenAI(openai_api_key=self.openai_api_key, temperature=0.3)

            # ChromaDBセットアップ
            self.vector_store = Chroma(
                collection_name="user_memories",
                embedding_function=self.embeddings,
                persist_directory="./chroma_db",
            )
            print("LangChain memory system initialized successfully")
        except Exception as e:
            print(f"Failed to initialize LangChain: {e}")
            LANGCHAIN_AVAILABLE = False

    def _is_quality_memory(self, content: str, memory_type: str, user_id: str) -> tuple[bool, str]:
        """
        記憶の品質をチェック
        Returns: (is_valid, reason)
        """
        # 最小文字数チェック
        MIN_LENGTH = 5
        if len(content.strip()) < MIN_LENGTH:
            return False, f"短すぎる（{len(content)}文字 < {MIN_LENGTH}文字）"

        # 意味のない記憶（単一単語のみ）をフィルタ
        if len(content.split()) == 1 and len(content) < 10:
            return False, "単一単語のみ"

        # 重複チェック
        if user_id in self.memory_items:
            for existing_memory in self.memory_items[user_id]:
                # 完全一致
                if existing_memory.content.strip() == content.strip():
                    return False, "完全重複"

                # 高い類似度（90%以上同じ）
                if (
                    existing_memory.memory_type == memory_type
                    and len(content) > 20
                    and self._similarity_ratio(existing_memory.content, content) > 0.9
                ):
                    return False, "類似重複（90%以上）"

        # 情報量チェック（あまりに一般的すぎる表現を除外）
        generic_patterns = ["はい", "いいえ", "そうです", "ありがとう", "よろしく"]
        if content.strip() in generic_patterns:
            return False, "一般的すぎる表現"

        return True, "OK"

    def _similarity_ratio(self, s1: str, s2: str) -> float:
        """2つの文字列の類似度を計算（簡易版）"""
        s1_lower = s1.lower().strip()
        s2_lower = s2.lower().strip()

        if not s1_lower or not s2_lower:
            return 0.0

        # 共通部分の割合を計算
        longer = max(len(s1_lower), len(s2_lower))
        shorter = min(len(s1_lower), len(s2_lower))

        # 簡易的な類似度（含まれる割合）
        if s1_lower in s2_lower or s2_lower in s1_lower:
            return shorter / longer

        # 単語レベルの一致
        words1 = set(s1_lower.split())
        words2 = set(s2_lower.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    async def store_memory(
        self, user_id: str, content: str, memory_type: str, metadata: dict[str, Any] = None
    ) -> str:
        """記憶を保存（SQLiteに永続化）with品質フィルタリング"""
        if metadata is None:
            metadata = {}

        # ★ 品質チェック
        is_valid, reason = self._is_quality_memory(content, memory_type, user_id)
        if not is_valid:
            print(f"Memory rejected: {reason} - '{content[:50]}'")
            return ""  # 空文字列を返して保存しない

        # 重要度を計算
        importance_score = MemoryImportanceCalculator.calculate_importance(
            content, memory_type, metadata
        )

        # 低重要度記憶のフィルタリング（閾値以下は保存しない）
        MIN_IMPORTANCE = 0.15
        if importance_score < MIN_IMPORTANCE:
            print(f"Memory rejected: Low importance ({importance_score:.2f}) - '{content[:50]}'")
            return ""

        # 記憶アイテムを作成
        memory_id = f"{user_id}_{datetime.now().isoformat()}_{memory_type}"
        memory_item = MemoryItem(
            id=memory_id,
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            importance_score=importance_score,
            timestamp=datetime.now(),
            metadata=metadata,
        )

        # ユーザーの記憶リストに追加
        if user_id not in self.memory_items:
            self.memory_items[user_id] = []
        self.memory_items[user_id].append(memory_item)

        print(
            f"Memory stored: [{memory_type}] importance={importance_score:.2f} - '{content[:50]}'..."
        )

        # SQLiteに保存（永続化）
        self._save_memory_to_db(memory_item)

        # ベクトルストアに保存（LangChain使用時）
        if LANGCHAIN_AVAILABLE and self.vector_store:
            try:
                document = Document(
                    page_content=content,
                    metadata={
                        "user_id": user_id,
                        "memory_type": memory_type,
                        "importance_score": importance_score,
                        "timestamp": memory_item.timestamp.isoformat(),
                        "memory_id": memory_id,
                        **metadata,
                    },
                )
                self.vector_store.add_documents([document])
            except Exception as e:
                print(f"Failed to store in vector database: {e}")

        # 記憶の制限管理（重要度の低いものから削除）
        await self._manage_memory_limit(user_id)

        return memory_id

    async def retrieve_relevant_memories(
        self, user_id: str, query: str, limit: int = 10
    ) -> list[MemoryItem]:
        """関連する記憶を検索"""
        if LANGCHAIN_AVAILABLE and self.vector_store:
            try:
                # ベクトル検索
                docs = self.vector_store.similarity_search(
                    query, k=limit, filter={"user_id": user_id}
                )

                # MemoryItemに変換
                memories = []
                for doc in docs:
                    metadata = doc.metadata
                    memory_item = MemoryItem(
                        id=metadata.get("memory_id", ""),
                        user_id=metadata.get("user_id", ""),
                        content=doc.page_content,
                        memory_type=metadata.get("memory_type", ""),
                        importance_score=metadata.get("importance_score", 0.5),
                        timestamp=datetime.fromisoformat(
                            metadata.get("timestamp", datetime.now().isoformat())
                        ),
                        metadata=metadata,
                    )
                    memories.append(memory_item)

                return memories
            except Exception as e:
                print(f"Vector search failed: {e}")

        # フォールバック：キーワード検索
        return self._fallback_memory_search(user_id, query, limit)

    def _fallback_memory_search(self, user_id: str, query: str, limit: int) -> list[MemoryItem]:
        """フォールバック記憶検索（キーワードベース）"""
        if user_id not in self.memory_items:
            return []

        query_lower = query.lower()
        scored_memories = []

        for memory in self.memory_items[user_id]:
            # 簡単なスコアリング
            content_lower = memory.content.lower()
            score = 0.0

            # キーワードマッチング
            query_words = query_lower.split()
            for word in query_words:
                if word in content_lower:
                    score += 1.0

            # 重要度スコアを加味
            score *= memory.importance_score

            if score > 0:
                scored_memories.append((score, memory))

        # スコア順でソート
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in scored_memories[:limit]]

    async def _manage_memory_limit(self, user_id: str, max_memories: int = 200):
        """記憶の制限管理（SQLiteからも削除）"""
        if user_id not in self.memory_items:
            return

        memories = self.memory_items[user_id]
        if len(memories) <= max_memories:
            return

        # 重要度と時間でソート（重要度が高く、新しいものを優先）
        memories.sort(key=lambda m: (m.importance_score, m.timestamp), reverse=True)

        # 制限を超えた分を削除
        removed_memories = memories[max_memories:]
        self.memory_items[user_id] = memories[:max_memories]

        # SQLiteからも削除
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for memory in removed_memories:
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory.id,))
        conn.commit()
        conn.close()

        # ベクトルストアからも削除
        if LANGCHAIN_AVAILABLE and self.vector_store:
            try:
                for memory in removed_memories:
                    # Note: ChromaDBの個別削除は複雑なので、定期的な再構築を推奨
                    pass
            except Exception as e:
                print(f"Failed to remove from vector store: {e}")

    async def summarize_memories(self, user_id: str, memory_type: Optional[str] = None) -> str:
        """記憶を要約"""
        if user_id not in self.memory_items:
            return "記憶がありません。"

        memories = self.memory_items[user_id]
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        if not memories:
            return "該当する記憶がありません。"

        # 重要度でソート
        memories.sort(key=lambda m: m.importance_score, reverse=True)

        # 上位の記憶を要約
        top_memories = memories[:20]
        content_list = [m.content for m in top_memories]

        if LANGCHAIN_AVAILABLE and self.llm:
            try:
                # LangChainで要約
                combined_content = "\n".join(content_list)
                summary_prompt = f"""
以下はユーザーの記憶の断片です。メンタルヘルスの観点から重要なポイントを簡潔にまとめてください：

{combined_content}

要約:"""
                summary = self.llm(summary_prompt)
                return summary.strip()
            except Exception as e:
                print(f"Summarization failed: {e}")

        # フォールバック要約
        return f"記録された内容：{len(content_list)}件の記憶があります。主な内容：{content_list[0][:100]}..."

    def get_memory_stats(self, user_id: str) -> dict[str, Any]:
        """記憶の統計情報を取得"""
        if user_id not in self.memory_items:
            return {"total_memories": 0, "by_type": {}, "avg_importance": 0.0}

        memories = self.memory_items[user_id]

        by_type = {}
        total_importance = 0.0

        for memory in memories:
            if memory.memory_type not in by_type:
                by_type[memory.memory_type] = 0
            by_type[memory.memory_type] += 1
            total_importance += memory.importance_score

        avg_importance = total_importance / len(memories) if memories else 0.0

        return {
            "total_memories": len(memories),
            "by_type": by_type,
            "avg_importance": avg_importance,
            "langchain_enabled": LANGCHAIN_AVAILABLE,
        }


# グローバルインスタンス
memory_system = LangChainMemorySystem()
