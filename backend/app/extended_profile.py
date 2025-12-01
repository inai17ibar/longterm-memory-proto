"""
拡張ユーザープロファイルシステム
JSONフォーマットでの入出力に対応
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib


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
    hobbies: List[str] = field(default_factory=list)
    occupation: Optional[str] = None
    location: Optional[str] = None
    age: Optional[str] = None
    family: Optional[str] = None


@dataclass
class MentalProfile:
    """メンタルヘルス関連プロファイル"""
    recent_medication_change: Optional[str] = None
    current_mental_state: Optional[str] = None
    symptoms: Optional[str] = None
    triggers: Optional[str] = None
    coping_methods: Optional[str] = None
    support_system: Optional[str] = None


@dataclass
class Favorites:
    """お気に入り情報"""
    comedian: Optional[str] = None
    favorite_food: Optional[str] = None
    favorite_animal: Optional[str] = None
    tv_drama: Optional[str] = None
    comedians: List[str] = field(default_factory=list)
    food: Optional[str] = None
    beverage: Optional[str] = None
    drink: Optional[str] = None
    # 動的に追加されるフィールド用
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportantMemory:
    """重要な記憶"""
    text: str
    importance: str = "medium"  # low/medium/high
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))


@dataclass
class Concern:
    """悩み・懸念事項"""
    id: str = field(default_factory=lambda: hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest())
    summary: str = ""
    details: str = ""
    category: str = "その他"
    status: str = "継続中"  # 継続中/解決済み/一時保留
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    sources: List[int] = field(default_factory=list)


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
    stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class UserTendency:
    """ユーザー傾向"""
    dominant_mood: str = "普通"
    counts: Dict[str, int] = field(default_factory=dict)
    recent_intensity: str = "中"
    last_observed: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    insight: str = ""
    time_patterns: List[TimePattern] = field(default_factory=list)
    weekday_patterns: List[TimePattern] = field(default_factory=list)


@dataclass
class ExtendedUserProfile:
    """拡張ユーザープロファイル"""
    user_id: str
    profile_settings: ProfileSettings = field(default_factory=ProfileSettings)
    general_profile: GeneralProfile = field(default_factory=GeneralProfile)
    mental_profile: MentalProfile = field(default_factory=MentalProfile)
    favorites: Favorites = field(default_factory=Favorites)
    important_memories: List[ImportantMemory] = field(default_factory=list)
    recent_concerns: Dict[str, List[Concern]] = field(default_factory=dict)
    goals: List[Goal] = field(default_factory=list)
    relationships: Dict[str, Any] = field(default_factory=dict)
    environments: Dict[str, Any] = field(default_factory=dict)
    mood_trend: List[MoodEntry] = field(default_factory=list)
    user_tendency: UserTendency = field(default_factory=UserTendency)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, dict):
                result[key] = value
            elif isinstance(value, list):
                result[key] = value
            else:
                result[key] = value
        return result

    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, user_id: str, data: Dict[str, Any]) -> 'ExtendedUserProfile':
        """辞書からインスタンスを作成"""
        profile = cls(user_id=user_id)

        # profile_settings
        if "profile_settings" in data:
            profile.profile_settings = ProfileSettings(**data["profile_settings"])

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
            known_keys = {'comedian', 'favorite_food', 'favorite_animal', 'tv_drama',
                         'comedians', 'food', 'beverage', 'drink'}
            extra = {k: v for k, v in fav_data.items() if k not in known_keys}
            fav_data['extra'] = extra
            # 既知のキーのみで Favorites を作成
            filtered_fav = {k: v for k, v in fav_data.items() if k in known_keys or k == 'extra'}
            profile.favorites = Favorites(**filtered_fav)

        # important_memories
        if "important_memories" in data:
            profile.important_memories = [ImportantMemory(**m) for m in data["important_memories"]]

        # recent_concerns
        if "recent_concerns" in data:
            profile.recent_concerns = {
                category: [Concern(**c) for c in concerns]
                for category, concerns in data["recent_concerns"].items()
            }

        # goals
        if "goals" in data:
            profile.goals = [Goal(**g) for g in data["goals"]]

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

        return profile


class ExtendedProfileSystem:
    """拡張プロファイルシステム"""

    def __init__(self, json_file_path: str = "./extended_profiles.json"):
        self.json_file_path = json_file_path
        self.profiles: Dict[str, ExtendedUserProfile] = {}
        self.load_from_file()

    def load_from_file(self):
        """JSONファイルから全プロファイルを読み込み"""
        if not os.path.exists(self.json_file_path):
            self.profiles = {}
            return

        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
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
        data = {
            "users": {
                user_id: profile.to_dict()
                for user_id, profile in self.profiles.items()
            }
        }

        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(self.profiles)} extended profiles to {self.json_file_path}")

    def get_profile(self, user_id: str) -> Optional[ExtendedUserProfile]:
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

    def generate_profile_summary(self, user_id: str) -> str:
        """プロファイル要約を生成（プロンプト用）"""
        profile = self.get_profile(user_id)
        if not profile:
            return "プロファイル情報がありません。"

        summary_parts = []

        # プロファイル設定
        settings = profile.profile_settings
        summary_parts.append(f"## プロファイル設定")
        summary_parts.append(f"- 表示名: {settings.display_name}")
        summary_parts.append(f"- AI名: {settings.ai_name}")
        summary_parts.append(f"- AI性格: {settings.ai_personality}")
        summary_parts.append(f"- 応答スタイル: {settings.response_length_style}")

        # 一般プロファイル
        general = profile.general_profile
        if general.occupation or general.location or general.hobbies:
            summary_parts.append(f"\n## 基本情報")
            if general.occupation:
                summary_parts.append(f"- 職業: {general.occupation}")
            if general.location:
                summary_parts.append(f"- 住所: {general.location}")
            if general.hobbies:
                summary_parts.append(f"- 趣味: {', '.join(general.hobbies)}")

        # メンタルプロファイル
        mental = profile.mental_profile
        if mental.current_mental_state or mental.recent_medication_change:
            summary_parts.append(f"\n## メンタルヘルス状況")
            if mental.current_mental_state:
                summary_parts.append(f"- 現在の状態: {mental.current_mental_state}")
            if mental.recent_medication_change:
                summary_parts.append(f"- 最近の変化: {mental.recent_medication_change}")

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
            summary_parts.append(f"\n## お気に入り")
            for item in fav_items:
                summary_parts.append(f"- {item}")

        # 重要な記憶
        if profile.important_memories:
            summary_parts.append(f"\n## 重要な記憶")
            for mem in profile.important_memories[-5:]:  # 最新5件
                summary_parts.append(f"- [{mem.importance}] {mem.text}")

        # 現在の悩み
        if profile.recent_concerns:
            summary_parts.append(f"\n## 現在の悩み・懸念")
            for category, concerns in profile.recent_concerns.items():
                active_concerns = [c for c in concerns if c.status == "継続中"]
                if active_concerns:
                    summary_parts.append(f"### {category}")
                    for concern in active_concerns[-3:]:  # カテゴリごとに最新3件
                        summary_parts.append(f"  - {concern.summary}: {concern.details}")

        # 目標
        if profile.goals:
            summary_parts.append(f"\n## 目標")
            active_goals = [g for g in profile.goals if g.status == "active"]
            for goal in active_goals[-5:]:  # 最新5件
                summary_parts.append(f"- [{goal.importance}] {goal.goal}")

        # 気分傾向
        tendency = profile.user_tendency
        if tendency.insight:
            summary_parts.append(f"\n## 気分傾向")
            summary_parts.append(f"- {tendency.insight}")
            summary_parts.append(f"- 最近の主な気分: {tendency.dominant_mood}")

        return "\n".join(summary_parts)


# グローバルインスタンス
extended_profile_system = ExtendedProfileSystem()
