"""
メンタルヘルスRAG用の知識ベースシステム
"""

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional

import openai

from app.config import KNOWLEDGE_BASE_DB_PATH


@dataclass
class KnowledgeItem:
    """知識アイテムの構造"""

    id: str
    category: str  # cbt_technique, symptom_management, coping_strategy, etc.
    title: str
    content: str
    tags: list[str]
    relevance_keywords: list[str]
    created_at: str


class KnowledgeBaseSystem:
    """RAG用の知識ベース管理システム"""

    def __init__(self, db_path: str = None, openai_api_key: Optional[str] = None):
        self.db_path = str(db_path or KNOWLEDGE_BASE_DB_PATH)
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self._initialize_database()

    def _initialize_database(self):
        """データベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                relevance_keywords TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """
        )

        # インデックス作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON knowledge_items(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags ON knowledge_items(tags)")

        conn.commit()
        conn.close()
        print(f"Knowledge base database initialized at {self.db_path}")

    def add_knowledge(self, item: KnowledgeItem):
        """知識を追加"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge_items (id, category, title, content, tags, relevance_keywords, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item.id,
                item.category,
                item.title,
                item.content,
                json.dumps(item.tags, ensure_ascii=False),
                json.dumps(item.relevance_keywords, ensure_ascii=False),
                item.created_at,
            ),
        )

        conn.commit()
        conn.close()

    def search_knowledge(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> list[KnowledgeItem]:
        """知識を検索（キーワードベース）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query_lower = query.lower()

        # 日本語の一般的なキーワードを抽出（簡易形態素解析の代替）
        japanese_keywords = [
            "不安",
            "心配",
            "悩み",
            "困",
            "辛",
            "苦し",
            "疲れ",
            "ストレス",
            "眠れ",
            "不眠",
            "睡眠",
            "寝",
            "起き",
            "パニック",
            "発作",
            "うつ",
            "落ち込",
            "憂鬱",
            "呼吸",
            "リラックス",
            "落ち着",
            "対処",
            "方法",
            "認知",
            "思考",
            "マインドフルネス",
            "瞑想",
            "危機",
            "自殺",
            "自傷",
        ]

        # クエリに含まれるキーワードを抽出
        query_words = []
        for keyword in japanese_keywords:
            if keyword in query_lower:
                query_words.append(keyword)

        # スペース区切りの単語も追加
        query_words.extend(query_lower.split())

        if category:
            cursor.execute("SELECT * FROM knowledge_items WHERE category = ?", (category,))
        else:
            cursor.execute("SELECT * FROM knowledge_items")

        rows = cursor.fetchall()
        conn.close()

        # スコアリング
        scored_items = []
        for row in rows:
            item_id, cat, title, content, tags_str, keywords_str, created_at = row
            tags = json.loads(tags_str)
            keywords = json.loads(keywords_str)

            score = 0.0
            content_lower = content.lower()
            title_lower = title.lower()

            # タイトルマッチ（高スコア）
            for word in query_words:
                if word in title_lower:
                    score += 3.0

            # コンテンツマッチ
            for word in query_words:
                if word in content_lower:
                    score += 1.0

            # キーワードマッチ
            for word in query_words:
                if any(word in kw.lower() for kw in keywords):
                    score += 2.0

            # タグマッチ
            for word in query_words:
                if any(word in tag.lower() for tag in tags):
                    score += 1.5

            if score > 0:
                item = KnowledgeItem(
                    id=item_id,
                    category=cat,
                    title=title,
                    content=content,
                    tags=tags,
                    relevance_keywords=keywords,
                    created_at=created_at,
                )
                scored_items.append((score, item))

        # スコア順でソート
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:limit]]

    def get_all_knowledge(self, category: Optional[str] = None) -> list[KnowledgeItem]:
        """全知識を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if category:
            cursor.execute("SELECT * FROM knowledge_items WHERE category = ?", (category,))
        else:
            cursor.execute("SELECT * FROM knowledge_items")

        rows = cursor.fetchall()
        conn.close()

        items = []
        for row in rows:
            item_id, cat, title, content, tags_str, keywords_str, created_at = row
            items.append(
                KnowledgeItem(
                    id=item_id,
                    category=cat,
                    title=title,
                    content=content,
                    tags=json.loads(tags_str),
                    relevance_keywords=json.loads(keywords_str),
                    created_at=created_at,
                )
            )

        return items

    def get_stats(self) -> dict[str, Any]:
        """統計情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM knowledge_items")
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT category, COUNT(*) FROM knowledge_items GROUP BY category")
        by_category = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {"total_items": total_count, "by_category": by_category}


# グローバルインスタンス
knowledge_base = KnowledgeBaseSystem()
