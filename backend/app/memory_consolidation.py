"""
記憶の統合・要約システム
類似した記憶をマージし、長期的な記憶を要約する
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import openai

from .memory_system import MemoryItem, memory_system
from .episodic_memory import Episode, episodic_memory_system


class MemoryConsolidation:
    """記憶の統合と要約を行うクラス"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    async def consolidate_similar_memories(
        self,
        user_id: str,
        memory_type: str,
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        類似した記憶を統合する
        Returns: 統合された記憶のリスト
        """
        # 特定タイプの記憶を取得
        if user_id not in memory_system.memory_items:
            return []

        memories = [m for m in memory_system.memory_items[user_id] if m.memory_type == memory_type]

        if len(memories) < 2:
            return []

        # 類似グループを検出
        groups = self._find_similar_groups(memories, similarity_threshold)

        consolidated = []

        for group in groups:
            if len(group) > 1:
                # グループをマージ
                merged = await self._merge_memories(group)
                if merged:
                    consolidated.append({
                        "original_count": len(group),
                        "merged_content": merged,
                        "memory_ids": [m.id for m in group]
                    })

        return consolidated

    def _find_similar_groups(
        self,
        memories: List[MemoryItem],
        threshold: float
    ) -> List[List[MemoryItem]]:
        """類似記憶のグループを検出"""
        groups = []
        processed = set()

        for i, mem1 in enumerate(memories):
            if mem1.id in processed:
                continue

            group = [mem1]
            processed.add(mem1.id)

            for mem2 in memories[i+1:]:
                if mem2.id in processed:
                    continue

                similarity = self._calculate_similarity(mem1.content, mem2.content)

                if similarity >= threshold:
                    group.append(mem2)
                    processed.add(mem2.id)

            if len(group) > 1:
                groups.append(group)

        return groups

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """2つのテキストの類似度を計算（改良版）"""
        # 単語レベルの類似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        jaccard = intersection / union if union > 0 else 0.0

        # 文字列の包含関係もチェック
        if text1.lower() in text2.lower() or text2.lower() in text1.lower():
            jaccard = max(jaccard, 0.7)

        return jaccard

    async def _merge_memories(self, memories: List[MemoryItem]) -> Optional[str]:
        """複数の記憶を統合して1つの要約を生成"""
        if not self.client:
            # フォールバック：単純に結合
            return " / ".join([m.content for m in memories])

        contents = [m.content for m in memories]
        timestamps = [m.timestamp.strftime('%Y-%m-%d') for m in memories]

        merge_prompt = f"""
以下は同じテーマに関する複数の記憶です。これらを1つの統合された記憶として要約してください。

記憶リスト:
{chr(10).join([f'{i+1}. [{timestamps[i]}] {content}' for i, content in enumerate(contents)])}

要約のポイント:
- 重複を排除
- 時系列の変化があれば記載
- 最も重要な情報を保持
- 100文字程度で簡潔に

統合された記憶:
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは記憶を統合する専門家です。"},
                    {"role": "user", "content": merge_prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error merging memories: {e}")
            return None

    async def generate_memory_summary(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        特定期間の記憶を要約
        """
        if user_id not in memory_system.memory_items:
            return {"has_data": False, "message": "記憶がありません"}

        memories = memory_system.memory_items[user_id]

        # 日付フィルタ
        cutoff = datetime.now() - timedelta(days=days)
        memories = [m for m in memories if m.timestamp >= cutoff]

        # タイプフィルタ
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        if not memories:
            return {"has_data": False, "message": "該当する記憶がありません"}

        # タイプ別にグループ化
        by_type = defaultdict(list)
        for m in memories:
            by_type[m.memory_type].append(m)

        # 各タイプの要約を生成
        summaries = {}

        for mtype, type_memories in by_type.items():
            # 重要度順にソート
            type_memories.sort(key=lambda m: m.importance_score, reverse=True)

            # 上位5件を要約
            top_memories = type_memories[:5]

            if self.client:
                summary = await self._generate_type_summary(mtype, top_memories)
            else:
                summary = f"{len(type_memories)}件の記憶（最新: {top_memories[0].content[:50]}...）"

            summaries[mtype] = {
                "count": len(type_memories),
                "summary": summary,
                "latest": top_memories[0].content if top_memories else ""
            }

        return {
            "has_data": True,
            "period_days": days,
            "total_memories": len(memories),
            "by_type": summaries
        }

    async def _generate_type_summary(
        self,
        memory_type: str,
        memories: List[MemoryItem]
    ) -> str:
        """特定タイプの記憶を要約"""
        contents = [m.content for m in memories]

        summary_prompt = f"""
以下は「{memory_type}」に関する記憶です。これらを要約してください。

{chr(10).join([f'- {content}' for content in contents])}

50文字程度で簡潔に要約:
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは記憶を要約する専門家です。"},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error summarizing memories: {e}")
            return contents[0][:50] + "..." if contents else ""


class MemoryRelationship:
    """記憶間の関連性を分析するクラス"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    def find_related_memories(
        self,
        user_id: str,
        target_memory: MemoryItem,
        limit: int = 5
    ) -> List[Tuple[MemoryItem, float, str]]:
        """
        特定の記憶に関連する他の記憶を検索
        Returns: List[(記憶, 関連度スコア, 関連理由)]
        """
        if user_id not in memory_system.memory_items:
            return []

        all_memories = [m for m in memory_system.memory_items[user_id] if m.id != target_memory.id]

        if not all_memories:
            return []

        # 関連性スコアリング
        scored = []

        for memory in all_memories:
            score, reason = self._calculate_relationship_score(target_memory, memory)

            if score > 0.3:  # 閾値
                scored.append((memory, score, reason))

        # スコア順にソート
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:limit]

    def _calculate_relationship_score(
        self,
        mem1: MemoryItem,
        mem2: MemoryItem
    ) -> Tuple[float, str]:
        """
        2つの記憶の関連性スコアと理由を計算
        """
        score = 0.0
        reasons = []

        # 1. 同じタイプの記憶
        if mem1.memory_type == mem2.memory_type:
            score += 0.3
            reasons.append("同じカテゴリ")

        # 2. 時間的近接性
        time_diff = abs((mem1.timestamp - mem2.timestamp).days)
        if time_diff <= 1:
            score += 0.3
            reasons.append("同時期")
        elif time_diff <= 7:
            score += 0.2
            reasons.append("近い時期")

        # 3. 内容の類似性
        content_similarity = self._content_similarity(mem1.content, mem2.content)
        if content_similarity > 0.5:
            score += content_similarity * 0.5
            reasons.append("内容が類似")

        # 4. 因果関係の可能性（キーワードベース）
        if self._has_causal_relationship(mem1, mem2):
            score += 0.4
            reasons.append("因果関係の可能性")

        reason_text = "、".join(reasons) if reasons else "関連性低"

        return score, reason_text

    def _content_similarity(self, text1: str, text2: str) -> float:
        """内容の類似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _has_causal_relationship(self, mem1: MemoryItem, mem2: MemoryItem) -> bool:
        """因果関係の可能性をチェック"""
        # トリガー → 症状/感情
        trigger_types = ['triggers', 'work_status']
        effect_types = ['symptoms', 'emotional_state', 'concerns']

        if mem1.memory_type in trigger_types and mem2.memory_type in effect_types:
            return True

        if mem2.memory_type in trigger_types and mem1.memory_type in effect_types:
            return True

        # 対処法 → 症状改善
        if mem1.memory_type == 'coping_methods' and mem2.memory_type in effect_types:
            return True

        return False

    async def generate_memory_graph(self, user_id: str) -> Dict[str, Any]:
        """
        記憶の関連性グラフを生成
        """
        if user_id not in memory_system.memory_items:
            return {"nodes": [], "edges": []}

        memories = memory_system.memory_items[user_id]

        # 重要な記憶のみ（上位30件）
        memories = sorted(memories, key=lambda m: m.importance_score, reverse=True)[:30]

        nodes = []
        edges = []

        # ノード作成
        for memory in memories:
            nodes.append({
                "id": memory.id,
                "label": memory.content[:30] + "...",
                "type": memory.memory_type,
                "importance": memory.importance_score,
                "timestamp": memory.timestamp.isoformat()
            })

        # エッジ作成（関連性）
        for i, mem1 in enumerate(memories):
            for mem2 in memories[i+1:]:
                score, reason = self._calculate_relationship_score(mem1, mem2)

                if score > 0.5:  # 強い関連性のみ
                    edges.append({
                        "source": mem1.id,
                        "target": mem2.id,
                        "weight": score,
                        "reason": reason
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }


# グローバルインスタンス
memory_consolidation = MemoryConsolidation()
memory_relationship = MemoryRelationship()
