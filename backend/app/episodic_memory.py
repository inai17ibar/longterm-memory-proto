"""
エピソード記憶システム
時系列的なイベントと感情を記録し、ユーザーの経験を物語として保持
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import openai


@dataclass
class Episode:
    """エピソード記憶の構造"""
    id: str
    user_id: str
    title: str  # エピソードのタイトル（自動生成）
    content: str  # エピソードの詳細内容
    emotion: str  # 主な感情（happy, sad, anxious, angry, neutral, etc.）
    emotion_intensity: float  # 感情の強度 0.0-1.0
    timestamp: datetime
    context: Dict[str, Any]  # 状況（場所、人物、時間帯など）
    related_episodes: List[str]  # 関連エピソードのID
    importance_score: float  # 重要度 0.0-1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "emotion": self.emotion,
            "emotion_intensity": self.emotion_intensity,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "related_episodes": self.related_episodes,
            "importance_score": self.importance_score
        }


@dataclass
class EmotionRecord:
    """感情履歴の記録"""
    id: str
    user_id: str
    timestamp: datetime
    mood: int  # 0-10
    energy: int  # 0-10
    anxiety: int  # 0-10
    primary_emotion: str  # 主な感情
    triggers: List[str]  # 感情のトリガー
    notes: str  # メモ


class EpisodicMemorySystem:
    """エピソード記憶と感情履歴を管理するシステム"""

    def __init__(self, db_path: str = "./episodic_memory.db", openai_api_key: Optional[str] = None):
        self.db_path = db_path
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

        self._initialize_database()

    def _initialize_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # エピソード記憶テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                emotion TEXT NOT NULL,
                emotion_intensity REAL NOT NULL,
                timestamp TEXT NOT NULL,
                context TEXT NOT NULL,
                related_episodes TEXT NOT NULL,
                importance_score REAL NOT NULL
            )
        ''')

        # 感情履歴テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                mood INTEGER NOT NULL,
                energy INTEGER NOT NULL,
                anxiety INTEGER NOT NULL,
                primary_emotion TEXT NOT NULL,
                triggers TEXT NOT NULL,
                notes TEXT
            )
        ''')

        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_episodes_user_id ON episodes(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_episodes_timestamp ON episodes(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emotion_user_id ON emotion_history(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emotion_timestamp ON emotion_history(timestamp)')

        conn.commit()
        conn.close()
        print(f"Episodic memory database initialized at {self.db_path}")

    async def extract_episode_from_conversation(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        current_emotion_state: Dict[str, Any]
    ) -> Optional[Episode]:
        """
        会話からエピソード記憶を抽出
        重要なイベントや経験のみをエピソードとして保存
        """
        # エピソード抽出のためのプロンプト
        extraction_prompt = f"""
以下の会話から、ユーザーの重要な経験やエピソードを抽出してください。

【ユーザーの発言】
{user_message}

【現在の感情状態】
- 気分: {current_emotion_state.get('mood', 'N/A')}
- エネルギー: {current_emotion_state.get('energy', 'N/A')}
- 不安: {current_emotion_state.get('anxiety', 'N/A')}

エピソードとして記録すべき基準:
1. 具体的な出来事や経験が語られている
2. 強い感情を伴っている
3. ユーザーにとって意味のある体験である
4. 将来の会話で参照する価値がある

以下のJSON形式で返してください。エピソードが含まれていない場合は null を返してください。

{{
  "is_episode": true/false,
  "title": "エピソードの簡潔なタイトル（20文字以内）",
  "content": "エピソードの詳細な内容（100文字程度）",
  "emotion": "主な感情（happy/sad/anxious/angry/frustrated/hopeful/neutral等）",
  "emotion_intensity": 0.0～1.0の数値,
  "context": {{
    "location": "場所（わかれば）",
    "people": "関わった人物（わかれば）",
    "time_period": "時期（最近/先週/去年等）"
  }},
  "importance_score": 0.0～1.0の重要度
}}
"""

        try:
            if not self.client:
                # モック抽出
                return None

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたはエピソード記憶を抽出する専門家です。JSONのみで返答してください。"},
                    {"role": "user", "content": extraction_prompt}
                ],
                max_tokens=500,
                temperature=0.2
            )

            text = response.choices[0].message.content.strip()

            # JSONパース
            if text.startswith("```"):
                import re
                text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
                text = re.sub(r"\n?```$", "", text)

            data = json.loads(text)

            # エピソードでない場合はNone
            if not data.get("is_episode"):
                return None

            # エピソード作成
            episode_id = f"episode_{user_id}_{datetime.now().timestamp()}"
            episode = Episode(
                id=episode_id,
                user_id=user_id,
                title=data.get("title", "無題のエピソード"),
                content=data.get("content", user_message[:200]),
                emotion=data.get("emotion", "neutral"),
                emotion_intensity=data.get("emotion_intensity", 0.5),
                timestamp=datetime.now(),
                context=data.get("context", {}),
                related_episodes=[],
                importance_score=data.get("importance_score", 0.5)
            )

            # データベースに保存
            self._save_episode(episode)

            return episode

        except Exception as e:
            print(f"Error extracting episode: {e}")
            return None

    def _save_episode(self, episode: Episode):
        """エピソードをデータベースに保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO episodes
            (id, user_id, title, content, emotion, emotion_intensity, timestamp, context, related_episodes, importance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            episode.id,
            episode.user_id,
            episode.title,
            episode.content,
            episode.emotion,
            episode.emotion_intensity,
            episode.timestamp.isoformat(),
            json.dumps(episode.context, ensure_ascii=False),
            json.dumps(episode.related_episodes),
            episode.importance_score
        ))

        conn.commit()
        conn.close()

    def record_emotion(
        self,
        user_id: str,
        mood: int,
        energy: int,
        anxiety: int,
        primary_emotion: str,
        triggers: List[str] = None,
        notes: str = ""
    ) -> str:
        """感情状態を記録"""
        emotion_id = f"emotion_{user_id}_{datetime.now().timestamp()}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO emotion_history
            (id, user_id, timestamp, mood, energy, anxiety, primary_emotion, triggers, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            emotion_id,
            user_id,
            datetime.now().isoformat(),
            mood,
            energy,
            anxiety,
            primary_emotion,
            json.dumps(triggers or [], ensure_ascii=False),
            notes
        ))

        conn.commit()
        conn.close()

        return emotion_id

    def get_episodes(
        self,
        user_id: str,
        limit: int = 50,
        emotion_filter: Optional[str] = None,
        days_ago: Optional[int] = None
    ) -> List[Episode]:
        """エピソードを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM episodes WHERE user_id = ?"
        params = [user_id]

        if emotion_filter:
            query += " AND emotion = ?"
            params.append(emotion_filter)

        if days_ago:
            cutoff_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
            query += " AND timestamp >= ?"
            params.append(cutoff_date)

        query += " ORDER BY importance_score DESC, timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        episodes = []
        for row in rows:
            episodes.append(Episode(
                id=row[0],
                user_id=row[1],
                title=row[2],
                content=row[3],
                emotion=row[4],
                emotion_intensity=row[5],
                timestamp=datetime.fromisoformat(row[6]),
                context=json.loads(row[7]),
                related_episodes=json.loads(row[8]),
                importance_score=row[9]
            ))

        return episodes

    def get_emotion_history(
        self,
        user_id: str,
        days: int = 30
    ) -> List[EmotionRecord]:
        """感情履歴を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT * FROM emotion_history
            WHERE user_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (user_id, cutoff_date))

        rows = cursor.fetchall()
        conn.close()

        records = []
        for row in rows:
            records.append(EmotionRecord(
                id=row[0],
                user_id=row[1],
                timestamp=datetime.fromisoformat(row[2]),
                mood=row[3],
                energy=row[4],
                anxiety=row[5],
                primary_emotion=row[6],
                triggers=json.loads(row[7]),
                notes=row[8] or ""
            ))

        return records

    def analyze_emotion_trends(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """感情のトレンドを分析"""
        history = self.get_emotion_history(user_id, days)

        if not history:
            return {
                "has_data": False,
                "message": "十分なデータがありません"
            }

        # 平均値計算
        avg_mood = sum(r.mood for r in history) / len(history)
        avg_energy = sum(r.energy for r in history) / len(history)
        avg_anxiety = sum(r.anxiety for r in history) / len(history)

        # トレンド分析（最近3日 vs 過去）
        recent = history[:min(3, len(history))]
        older = history[min(3, len(history)):]

        trend = {
            "has_data": True,
            "period_days": days,
            "total_records": len(history),
            "averages": {
                "mood": round(avg_mood, 1),
                "energy": round(avg_energy, 1),
                "anxiety": round(avg_anxiety, 1)
            }
        }

        if recent and older:
            recent_avg_mood = sum(r.mood for r in recent) / len(recent)
            older_avg_mood = sum(r.mood for r in older) / len(older)

            trend["trend_analysis"] = {
                "mood_trend": "改善" if recent_avg_mood > older_avg_mood + 0.5 else "悪化" if recent_avg_mood < older_avg_mood - 0.5 else "安定",
                "mood_change": round(recent_avg_mood - older_avg_mood, 1)
            }

        # 最も頻繁な感情
        emotions = [r.primary_emotion for r in history]
        if emotions:
            from collections import Counter
            emotion_counts = Counter(emotions)
            trend["common_emotions"] = emotion_counts.most_common(3)

        return trend

    def get_related_episodes(
        self,
        user_id: str,
        current_message: str,
        limit: int = 5
    ) -> List[Episode]:
        """現在の会話に関連するエピソードを検索（簡易版）"""
        episodes = self.get_episodes(user_id, limit=50)

        # 簡易的なキーワードマッチング
        message_lower = current_message.lower()
        scored_episodes = []

        for episode in episodes:
            score = 0.0

            # タイトルとコンテンツでのマッチング
            if any(word in episode.title.lower() for word in message_lower.split()):
                score += 2.0
            if any(word in episode.content.lower() for word in message_lower.split()):
                score += 1.0

            # 重要度も考慮
            score *= episode.importance_score

            if score > 0:
                scored_episodes.append((score, episode))

        # スコア順にソート
        scored_episodes.sort(key=lambda x: x[0], reverse=True)

        return [ep for _, ep in scored_episodes[:limit]]


# グローバルインスタンス
episodic_memory_system = EpisodicMemorySystem()
