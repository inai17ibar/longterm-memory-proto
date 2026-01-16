"""
分析・推論層
ユーザーの内部状態を予測し、適切な応答スタイルを提案
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Optional

import openai

from .memory_system import MemoryItem
from .user_profile import UserProfile


class AnalysisLayer:
    """分析・推論層クラス"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    async def analyze_user_state(
        self,
        user_id: str,
        user_message: str,
        user_profile: Optional[UserProfile],
        recent_conversations: list[dict[str, Any]],
        relevant_memories: list[MemoryItem],
    ) -> dict[str, Any]:
        """
        ユーザーの現在の感情・ニーズ・推奨モードをLLMで推定

        返り値:
        {
            "mood": 0-10 (全体的な気分),
            "energy": 0-10 (エネルギー・やる気),
            "anxiety": 0-10 (不安の強さ),
            "main_topics": ["テーマ1", "テーマ2"],
            "need": "共感してほしい / 解決のヒント / 話を整理したい 等",
            "modes": ["empathy", "emotion_labeling", ...],
            "state_comment": "状態の簡単な説明",
            "contextual_patterns": {  # 文脈パターン分析
                "night_mood": "夜22時以降で不安が高い",
                "weekday_stress": "平日に職場ストレスが高い",
                "trend_analysis": "感情スコアが3日連続で下降傾向"
            }
        }
        """
        # 会話履歴の要約
        history_summary = self._summarize_conversations(recent_conversations)

        # 関連記憶の要約
        relevant_summary = self._summarize_memories(relevant_memories)

        # プロファイル情報の要約
        profile_summary = self._summarize_profile(user_profile)

        # LLMで状態推定
        state = await self._estimate_state_with_llm(
            user_message=user_message,
            history_summary=history_summary,
            relevant_summary=relevant_summary,
            profile_summary=profile_summary,
        )

        # 文脈パターン分析を追加
        contextual_patterns = self._analyze_contextual_patterns(
            user_profile=user_profile,
            recent_conversations=recent_conversations,
            current_state=state,
        )

        state["contextual_patterns"] = contextual_patterns

        return state

    def _summarize_conversations(self, conversations: list[dict[str, Any]]) -> str:
        """会話履歴を要約"""
        if not conversations:
            return "（会話履歴なし）"

        last_few = conversations[-5:]
        summary = ""
        for conv in last_few:
            summary += f"ユーザー: {conv['user_message']}\nカウンセラー: {conv['ai_response']}\n"

        return summary

    def _summarize_memories(self, memories: list[MemoryItem]) -> str:
        """関連記憶を要約"""
        if not memories:
            return "（関連記憶なし）"

        summary = ""
        for m in memories[:3]:
            summary += f"- [{m.memory_type}] {m.content}\n"

        return summary

    def _summarize_profile(self, profile: Optional[UserProfile]) -> str:
        """プロファイル情報を要約"""
        if not profile:
            return "（プロファイル情報なし）"

        parts = []

        if profile.job:
            parts.append(f"職業: {profile.job}")
        if profile.work_status:
            parts.append(f"勤務状況: {profile.work_status}")
        if profile.concerns:
            parts.append(f"主な悩み: {profile.concerns[:100]}")
        if profile.goals:
            parts.append(f"目標: {profile.goals[:100]}")
        if profile.symptoms:
            parts.append(f"症状: {profile.symptoms[:100]}")
        if profile.triggers:
            parts.append(f"ストレス要因: {profile.triggers[:100]}")

        return "\n".join(parts) if parts else "（プロファイル情報なし）"

    async def _estimate_state_with_llm(
        self, user_message: str, history_summary: str, relevant_summary: str, profile_summary: str
    ) -> dict[str, Any]:
        """LLMで状態推定"""
        prompt = f"""
あなたはメンタルヘルスカウンセリングの専門家です。
以下の情報から、ユーザーの現在の状態を分析し、JSON形式で返してください。

【現在の発言】
{user_message}

【直近の会話（最大5ターン）】
{history_summary}

【関連する記憶（最大3件）】
{relevant_summary}

【ユーザープロファイル】
{profile_summary}

以下のフォーマットで、日本語の自由記述を含むJSONを返してください（推測しすぎず、書かれていないことは null）。

{{
  "mood": 0～10の整数（全体的な気分。0=最悪、10=最高。よくわからなければ null）,
  "energy": 0～10の整数（エネルギー・やる気。0=全くない、10=非常に高い。よくわからなければ null）,
  "anxiety": 0～10の整数（不安の強さ。0=全くない、10=極度の不安。よくわからなければ null）,
  "main_topics": ["主なテーマ1", "主なテーマ2"],
  "need": "今ユーザーが一番求めていそうなこと（例: 共感してほしい、解決のヒントがほしい、ただ聞いてほしい、小さな行動を考えたい 等）",
  "modes": [
    "empathy",           // 共感・受容
    "emotion_labeling",  // 感情の言語化を助ける
    "problem_sorting",   // 問題の整理
    "small_action",      // 小さな行動の提案
    "psychoeducation"    // 情報提供・解説
  ] の中から2つ程度を選んで並べる,
  "state_comment": "状態の簡単な説明（1〜2文）"
}}
"""

        try:
            if not self.client:
                # モック状態推定
                return self._mock_state_estimation(user_message)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたはメンタルヘルスの状態を分析するアシスタントです。JSONのみで返答してください。",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.2,
            )

            text = response.choices[0].message.content.strip()

            # JSONパース
            if text.startswith("```"):
                text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
                text = re.sub(r"\n?```$", "", text)

            try:
                state = json.loads(text)
            except json.JSONDecodeError:
                state = self._mock_state_estimation(user_message)

            return state

        except Exception as e:
            print(f"Error in analyze_user_state: {e}")
            return self._mock_state_estimation(user_message)

    def _mock_state_estimation(self, user_message: str = "") -> dict[str, Any]:
        """モック状態推定（キーワード分析ベース）"""
        # メッセージが渡されない場合は中立状態
        if not user_message:
            return {
                "mood": 5,
                "energy": 5,
                "anxiety": 5,
                "main_topics": ["メンタルヘルス"],
                "need": "共感してほしい",
                "modes": ["empathy", "emotion_labeling"],
                "state_comment": "現在の状態を分析中です",
            }

        msg_lower = user_message.lower()

        # 気分の推定
        mood = 5
        if any(word in msg_lower for word in ["嬉しい", "楽しい", "良い", "幸せ", "いい"]):
            mood = 8
        elif any(word in msg_lower for word in ["最高", "素晴らしい", "完璧"]):
            mood = 9
        elif any(word in msg_lower for word in ["辛い", "苦しい", "悲しい", "悔しい", "つらい"]):
            mood = 2
        elif any(word in msg_lower for word in ["最悪", "何もしたくない", "無理"]):
            mood = 1
        elif any(word in msg_lower for word in ["不安", "心配", "怖い", "怖れ"]):
            mood = 3
        elif any(word in msg_lower for word in ["落ち着いた", "リラックス"]):
            mood = 7

        # エネルギーの推定
        energy = 5
        if any(word in msg_lower for word in ["全く動けない", "何もできない", "極度の疲労"]):
            energy = 1
        elif any(word in msg_lower for word in ["疲れた", "疲れ", "眠い", "休みたい", "疲労"]):
            energy = 2
        elif any(word in msg_lower for word in ["非常に活発", "躍起", "やる気満々"]):
            energy = 9
        elif any(
            word in msg_lower
            for word in ["頑張り", "やる気", "モチベ", "やる", "楽しい", "楽しかった", "嬉しい"]
        ):
            energy = 8
        elif any(word in msg_lower for word in ["元気", "いい感じ", "調子いい"]):
            energy = 7

        # 不安度の推定
        anxiety = 5
        if any(word in msg_lower for word in ["極度の不安", "パニック発作", "襲われた"]):
            anxiety = 10
        elif any(word in msg_lower for word in ["全く不安がない", "穏やかそのもの"]):
            anxiety = 0
        elif any(word in msg_lower for word in ["落ち着いた", "リラックス", "穏やか", "平穏"]):
            anxiety = 2
        elif any(
            word in msg_lower for word in ["不安", "心配", "怖い", "パニック", "ストレス", "緊張"]
        ):
            anxiety = 8

        # トピック抽出
        topics = []
        if any(word in msg_lower for word in ["仕事", "職場", "勤務", "業務"]):
            topics.append("仕事・職場")
        if any(word in msg_lower for word in ["家族", "親", "両親"]):
            topics.append("家族関係")
        if any(word in msg_lower for word in ["友人", "友達", "人間関係", "対人"]):
            topics.append("人間関係")
        if any(word in msg_lower for word in ["睡眠", "眠り", "眠い", "不眠"]):
            topics.append("睡眠")
        if any(word in msg_lower for word in ["恋愛", "恋人", "パートナー"]):
            topics.append("恋愛")
        if not topics:
            topics = ["メンタルヘルス"]

        # ニーズ推定
        need = "共感してほしい"
        if any(
            word in msg_lower for word in ["どうしたら", "どうすれば", "対策", "対処", "アドバイス"]
        ):
            need = "解決のヒント・アドバイス"
        if any(word in msg_lower for word in ["聞いて", "聴いて", "話したい", "吐き出したい"]):
            need = "話を聞いてほしい・受け入れてもらいたい"
        if any(word in msg_lower for word in ["整理", "整りー", "何が問題か", "気持ちの整理"]):
            need = "気持ちや問題の整理"

        return {
            "mood": mood,
            "energy": energy,
            "anxiety": anxiety,
            "main_topics": topics,
            "need": need,
            "modes": ["empathy", "emotion_labeling"],
            "state_comment": f"会話内容から推定した状態（気分:{mood}, エネルギー:{energy}, 不安:{anxiety}）",
        }

    def _analyze_contextual_patterns(
        self,
        user_profile: Optional[UserProfile],
        recent_conversations: list[dict[str, Any]],
        current_state: dict[str, Any],
    ) -> dict[str, Any]:
        """文脈パターンを分析"""
        patterns = {}

        # 時間帯分析
        current_hour = datetime.now().hour
        if current_hour >= 22 or current_hour <= 5:
            anxiety = current_state.get("anxiety")
            if anxiety and anxiety >= 7:
                patterns["night_mood"] = "深夜で不安が高い状態です"

        # 週末・平日分析
        current_weekday = datetime.now().weekday()
        if current_weekday < 5:  # 月〜金
            if user_profile and user_profile.work_status:
                if "休職" not in user_profile.work_status:
                    patterns["weekday_stress"] = "平日の勤務日です"

        # トレンド分析（過去3日の会話から）
        if len(recent_conversations) >= 3:
            # 簡易的なトレンド分析
            patterns["trend_analysis"] = f"過去{len(recent_conversations)}件の会話を分析"

        return patterns

    def suggest_response_approach(
        self, user_state: dict[str, Any], user_profile: Optional[UserProfile]
    ) -> dict[str, Any]:
        """応答アプローチを提案"""
        suggestions = {
            "priority_modes": user_state.get("modes", ["empathy"]),
            "tone": "supportive",  # supportive, gentle, informative
            "length": "medium",  # short, medium, long
            "specific_tips": [],
        }

        # 不安が高い場合
        anxiety = user_state.get("anxiety")
        if anxiety and anxiety >= 8:
            suggestions["tone"] = "gentle"
            suggestions["specific_tips"].append(
                "不安が非常に高いため、安心感を最優先にしてください"
            )

        # エネルギーが低い場合
        energy = user_state.get("energy")
        if energy and energy <= 3:
            suggestions["length"] = "short"
            suggestions["specific_tips"].append("エネルギーが低いため、短く簡潔に応答してください")

        # 目標が明確な場合
        if user_profile and user_profile.goals:
            if "small_action" not in suggestions["priority_modes"]:
                suggestions["priority_modes"].append("small_action")
            suggestions["specific_tips"].append("目標に向けた小さな行動を提案できます")

        return suggestions


# グローバルインスタンス
analysis_layer = AnalysisLayer()
