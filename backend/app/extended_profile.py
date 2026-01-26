"""
拡張ユーザープロファイルシステム
JSONフォーマットでの入出力に対応
"""

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from app.config import EXTENDED_PROFILES_JSON_PATH


@dataclass
class ProfileSettings:
    """プロファイル設定"""

    display_name: str = "ユーザー"
    ai_name: str = "カウンセラー"
    ai_personality: str = "優しく寄り添うガイド"
    ai_expectation: str = "2"  # 1-3の期待レベル
    response_length_style: str = "medium"  # short/medium/long
    profile_initialized_at: int = field(default_factory=lambda: int(datetime.now().timestamp()))


@dataclass
class GeneralProfile:
    """一般的なプロファイル情報"""

    hobbies: list[str] = field(default_factory=list)
    occupation: str | None = None
    location: str | None = None
    age: str | None = None
    family: str | None = None


@dataclass
class MentalProfile:
    """メンタルヘルス関連プロファイル"""

    recent_medication_change: str | None = None
    current_mental_state: str | None = None
    symptoms: str | None = None
    triggers: str | None = None
    coping_methods: str | None = None
    support_system: str | None = None


@dataclass
class Favorites:
    """お気に入り情報"""

    comedian: str | None = None
    favorite_food: str | None = None
    favorite_animal: str | None = None
    tv_drama: str | None = None
    comedians: list[str] = field(default_factory=list)
    food: str | None = None
    beverage: str | None = None
    drink: str | None = None
    # 動的に追加されるフィールド用
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportantMemory:
    """重要な記憶"""

    text: str
    importance: str = "medium"  # low/medium/high
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))


@dataclass
class Concern:
    """悩み・懸念事項"""

    id: str = field(
        default_factory=lambda: hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()
    )
    summary: str = ""
    details: str = ""
    category: str = "その他"
    status: str = "継続中"  # 継続中/解決済み/一時保留
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    sources: list[int] = field(default_factory=list)


@dataclass
class Goal:
    """目標"""

    goal: str
    importance: str = "medium"  # low/medium/high
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    timeline: str = "ongoing"  # short-term/ongoing/long-term
    status: str = "active"  # active/completed/abandoned


@dataclass
class MoodEntry:
    """気分エントリー"""

    mood: str
    intensity: str = "中"  # 低/中/高
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    session_id: str = ""


@dataclass
class TimePattern:
    """時間パターン"""

    key: str
    tendency: str  # positive/negative/neutral
    description: str
    stats: dict[str, int] = field(default_factory=dict)


@dataclass
class UserTendency:
    """ユーザー傾向"""

    dominant_mood: str = "普通"
    counts: dict[str, int] = field(default_factory=dict)
    recent_intensity: str = "中"
    last_observed: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    insight: str = ""
    time_patterns: list[TimePattern] = field(default_factory=list)
    weekday_patterns: list[TimePattern] = field(default_factory=list)


@dataclass
class ExtendedUserProfile:
    """拡張ユーザープロファイル"""

    user_id: str
    profile_settings: ProfileSettings = field(default_factory=ProfileSettings)
    general_profile: GeneralProfile = field(default_factory=GeneralProfile)
    mental_profile: MentalProfile = field(default_factory=MentalProfile)
    favorites: Favorites = field(default_factory=Favorites)
    important_memories: list[ImportantMemory] = field(default_factory=list)
    recent_concerns: dict[str, list[Concern]] = field(default_factory=dict)
    goals: list[Goal] = field(default_factory=list)
    relationships: dict[str, Any] = field(default_factory=dict)
    environments: dict[str, Any] = field(default_factory=dict)
    mood_trend: list[MoodEntry] = field(default_factory=list)
    user_tendency: UserTendency = field(default_factory=UserTendency)
    time_patterns: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, dict | list):
                result[key] = value
            else:
                result[key] = value

        # profile_settingsからcustom_system_promptを除外（Noneまたは存在する場合）
        if "profile_settings" in result and isinstance(result["profile_settings"], dict):
            result["profile_settings"].pop("custom_system_prompt", None)

        return result

    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, user_id: str, data: dict[str, Any]) -> "ExtendedUserProfile":
        """辞書からインスタンスを作成"""
        profile = cls(user_id=user_id)

        # profile_settings
        if "profile_settings" in data:
            settings_data = data["profile_settings"].copy()
            # custom_system_promptを除外
            settings_data.pop("custom_system_prompt", None)
            profile.profile_settings = ProfileSettings(**settings_data)

        # general_profile
        if "general_profile" in data:
            profile.general_profile = GeneralProfile(**data["general_profile"])

        # mental_profile
        if "mental_profile" in data:
            profile.mental_profile = MentalProfile(**data["mental_profile"])

        # favorites
        if "favorites" in data:
            fav_data = data["favorites"].copy()
            # extra フィールドに未定義のキーを格納
            known_keys = {
                "comedian",
                "favorite_food",
                "favorite_animal",
                "tv_drama",
                "comedians",
                "food",
                "beverage",
                "drink",
            }
            # 既存のextraキーを除外して、新しいextraを作成（無限ネストを防ぐ）
            # known_keysにもextraにも含まれないキーのみを抽出
            extra = {k: v for k, v in fav_data.items() if k not in known_keys and k != "extra"}
            fav_data["extra"] = extra
            # 既知のキーのみで Favorites を作成
            filtered_fav = {k: v for k, v in fav_data.items() if k in known_keys or k == "extra"}
            profile.favorites = Favorites(**filtered_fav)

        # important_memories
        if "important_memories" in data:
            memories = []
            for m in data["important_memories"]:
                if isinstance(m, str):
                    # 文字列の場合は、textフィールドに設定してImportantMemoryオブジェクトを作成
                    memories.append(ImportantMemory(text=m))
                elif isinstance(m, dict):
                    # 辞書の場合は、そのまま展開
                    memories.append(ImportantMemory(**m))
            profile.important_memories = memories

        # recent_concerns
        if "recent_concerns" in data:
            profile.recent_concerns = {
                category: [Concern(**c) for c in concerns]
                for category, concerns in data["recent_concerns"].items()
            }

        # goals
        if "goals" in data:
            goals = []
            for g in data["goals"]:
                if isinstance(g, str):
                    # 文字列の場合は、goalフィールドに設定してGoalオブジェクトを作成
                    goals.append(Goal(goal=g))
                elif isinstance(g, dict):
                    # 辞書の場合は、そのまま展開
                    goals.append(Goal(**g))
            profile.goals = goals

        # relationships, environments
        profile.relationships = data.get("relationships", {})
        profile.environments = data.get("environments", {})

        # mood_trend
        if "mood_trend" in data:
            profile.mood_trend = [MoodEntry(**m) for m in data["mood_trend"]]

        # user_tendency
        if "user_tendency" in data:
            tendency_data = data["user_tendency"].copy()
            if "time_patterns" in tendency_data:
                tendency_data["time_patterns"] = [
                    TimePattern(**p) for p in tendency_data["time_patterns"]
                ]
            if "weekday_patterns" in tendency_data:
                tendency_data["weekday_patterns"] = [
                    TimePattern(**p) for p in tendency_data["weekday_patterns"]
                ]
            profile.user_tendency = UserTendency(**tendency_data)

        # time_patterns（トップレベルのフィールド）
        if "time_patterns" in data:
            profile.time_patterns = data["time_patterns"]

        return profile


class ExtendedProfileSystem:
    """拡張プロファイルシステム"""

    def __init__(self, json_file_path: str = None):
        self.json_file_path = str(json_file_path or EXTENDED_PROFILES_JSON_PATH)
        self.profiles: dict[str, ExtendedUserProfile] = {}
        self.load_from_file()

    def load_from_file(self):
        """JSONファイルから全プロファイルを読み込み"""
        if not os.path.exists(self.json_file_path):
            self.profiles = {}
            return

        try:
            with open(self.json_file_path, encoding="utf-8") as f:
                data = json.load(f)

            if "users" in data:
                for user_id, user_data in data["users"].items():
                    self.profiles[user_id] = ExtendedUserProfile.from_dict(user_id, user_data)

            print(f"Loaded {len(self.profiles)} extended profiles from {self.json_file_path}")
        except Exception as e:
            print(f"Error loading extended profiles: {e}")
            self.profiles = {}

    def save_to_file(self):
        """全プロファイルをJSONファイルに保存"""
        data = {"users": {user_id: profile.to_dict() for user_id, profile in self.profiles.items()}}

        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(self.profiles)} extended profiles to {self.json_file_path}")

    def get_profile(self, user_id: str) -> ExtendedUserProfile | None:
        """プロファイルを取得"""
        return self.profiles.get(user_id)

    def create_or_update_profile(self, profile: ExtendedUserProfile) -> bool:
        """プロファイルを作成または更新"""
        self.profiles[profile.user_id] = profile
        self.save_to_file()
        return True

    def delete_profile(self, user_id: str) -> bool:
        """プロファイルを削除"""
        if user_id in self.profiles:
            del self.profiles[user_id]
            self.save_to_file()
            return True
        return False

    def sync_from_user_profile(self, user_id: str, user_profile: Any) -> ExtendedUserProfile:
        """
        旧来のUserProfileから拡張プロファイルにデータを同期
        user_profileの情報を拡張プロファイルに反映させる
        """
        # 既存の拡張プロファイルを取得、なければ新規作成
        profile = self.get_profile(user_id)
        if not profile:
            profile = ExtendedUserProfile(user_id=user_id)

        # GeneralProfileのマッピング
        if hasattr(user_profile, "name") and user_profile.name:
            profile.profile_settings.display_name = user_profile.name
        if hasattr(user_profile, "job") and user_profile.job:
            profile.general_profile.occupation = user_profile.job
        if hasattr(user_profile, "location") and user_profile.location:
            profile.general_profile.location = user_profile.location
        if hasattr(user_profile, "age") and user_profile.age:
            profile.general_profile.age = user_profile.age
        if hasattr(user_profile, "family") and user_profile.family:
            profile.general_profile.family = user_profile.family
        if hasattr(user_profile, "hobbies") and user_profile.hobbies:
            profile.general_profile.hobbies = user_profile.hobbies

        # MentalProfileのマッピング
        if hasattr(user_profile, "emotional_state") and user_profile.emotional_state:
            profile.mental_profile.current_mental_state = user_profile.emotional_state
        if hasattr(user_profile, "medication") and user_profile.medication:
            profile.mental_profile.recent_medication_change = user_profile.medication
        if hasattr(user_profile, "symptoms") and user_profile.symptoms:
            profile.mental_profile.symptoms = user_profile.symptoms
        if hasattr(user_profile, "triggers") and user_profile.triggers:
            profile.mental_profile.triggers = user_profile.triggers
        if hasattr(user_profile, "coping_methods") and user_profile.coping_methods:
            profile.mental_profile.coping_methods = user_profile.coping_methods
        if hasattr(user_profile, "support_system") and user_profile.support_system:
            profile.mental_profile.support_system = user_profile.support_system

        # Concerns（悩み）を recent_concerns に追加
        if hasattr(user_profile, "concerns") and user_profile.concerns:
            if "その他" not in profile.recent_concerns:
                profile.recent_concerns["その他"] = []
            # 既存の悩みと重複しないようにチェック
            existing_summaries = {
                c.summary for cat in profile.recent_concerns.values() for c in cat
            }
            if user_profile.concerns not in existing_summaries:
                new_concern = Concern(
                    summary=user_profile.concerns[:50]
                    if len(user_profile.concerns) > 50
                    else user_profile.concerns,
                    details=user_profile.concerns,
                    category="その他",
                    status="継続中",
                )
                profile.recent_concerns["その他"].append(new_concern)

        # Goals（目標）を goals に追加
        if hasattr(user_profile, "goals") and user_profile.goals:
            # 既存の目標と重複しないようにチェック
            existing_goals = {g.goal for g in profile.goals}
            if user_profile.goals not in existing_goals:
                new_goal = Goal(goal=user_profile.goals, importance="medium", status="active")
                profile.goals.append(new_goal)

        self.create_or_update_profile(profile)
        return profile

    def generate_profile_summary(self, user_id: str) -> str:
        """プロファイル要約を生成（プロンプト用）"""
        profile = self.get_profile(user_id)
        if not profile:
            return "プロファイル情報がありません。"

        summary_parts = []

        # プロファイル設定
        settings = profile.profile_settings
        summary_parts.append("## プロファイル設定")
        summary_parts.append(f"- 表示名: {settings.display_name}")
        summary_parts.append(f"- AI名: {settings.ai_name}")
        summary_parts.append(f"- AI性格: {settings.ai_personality}")
        summary_parts.append(f"- 応答スタイル: {settings.response_length_style}")

        # 一般プロファイル
        general = profile.general_profile
        if (
            general.occupation
            or general.location
            or general.hobbies
            or general.age
            or general.family
        ):
            summary_parts.append("\n## 基本情報")
            if general.age:
                summary_parts.append(f"- 年齢: {general.age}")
            if general.occupation:
                summary_parts.append(f"- 職業: {general.occupation}")
            if general.location:
                summary_parts.append(f"- 住所: {general.location}")
            if general.family:
                summary_parts.append(f"- 家族: {general.family}")
            if general.hobbies:
                summary_parts.append(f"- 趣味: {', '.join(general.hobbies)}")

        # メンタルプロファイル
        mental = profile.mental_profile
        if (
            mental.current_mental_state
            or mental.recent_medication_change
            or mental.symptoms
            or mental.triggers
            or mental.coping_methods
            or mental.support_system
        ):
            summary_parts.append("\n## メンタルヘルス状況")
            if mental.current_mental_state:
                summary_parts.append(f"- 現在の状態: {mental.current_mental_state}")
            if mental.recent_medication_change:
                summary_parts.append(f"- 服薬・通院: {mental.recent_medication_change}")
            if mental.symptoms:
                summary_parts.append(f"- 症状: {mental.symptoms}")
            if mental.triggers:
                summary_parts.append(f"- ストレス要因: {mental.triggers}")
            if mental.coping_methods:
                summary_parts.append(f"- 対処法: {mental.coping_methods}")
            if mental.support_system:
                summary_parts.append(f"- サポート体制: {mental.support_system}")

        # お気に入り
        fav = profile.favorites
        fav_items = []
        if fav.favorite_food:
            fav_items.append(f"食べ物: {fav.favorite_food}")
        if fav.drink:
            fav_items.append(f"飲み物: {fav.drink}")
        if fav.favorite_animal:
            fav_items.append(f"動物: {fav.favorite_animal}")
        if fav.tv_drama:
            fav_items.append(f"ドラマ: {fav.tv_drama}")
        if fav.comedian:
            fav_items.append(f"芸人: {fav.comedian}")
        if fav_items:
            summary_parts.append("\n## お気に入り")
            for item in fav_items:
                summary_parts.append(f"- {item}")

        # 重要な記憶
        if profile.important_memories:
            summary_parts.append("\n## 重要な記憶")
            for mem in profile.important_memories[-5:]:  # 最新5件
                summary_parts.append(f"- [{mem.importance}] {mem.text}")

        # 現在の悩み
        if profile.recent_concerns:
            summary_parts.append("\n## 現在の悩み・懸念")
            for category, concerns in profile.recent_concerns.items():
                active_concerns = [c for c in concerns if c.status == "継続中"]
                if active_concerns:
                    summary_parts.append(f"### {category}")
                    for concern in active_concerns[-3:]:  # カテゴリごとに最新3件
                        summary_parts.append(f"  - {concern.summary}: {concern.details}")

        # 目標
        if profile.goals:
            summary_parts.append("\n## 目標")
            active_goals = [g for g in profile.goals if g.status == "active"]
            for goal in active_goals[-5:]:  # 最新5件
                summary_parts.append(f"- [{goal.importance}] {goal.goal}")

        # 気分傾向
        tendency = profile.user_tendency
        if tendency.insight:
            summary_parts.append("\n## 気分傾向")
            summary_parts.append(f"- {tendency.insight}")
            summary_parts.append(f"- 最近の主な気分: {tendency.dominant_mood}")

        return "\n".join(summary_parts)


# グローバルインスタンス
extended_profile_system = ExtendedProfileSystem()
