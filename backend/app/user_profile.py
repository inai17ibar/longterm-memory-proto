"""
ユーザープロファイル管理システム
メンタルヘルスカウンセリングに特化したユーザー情報をSQLiteで永続化
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
import openai


@dataclass
class UserProfile:
    """ユーザープロファイルのデータクラス"""
    user_id: str

    # 基本情報
    name: Optional[str] = None
    job: Optional[str] = None
    hobbies: List[str] = field(default_factory=list)
    age: Optional[str] = None
    location: Optional[str] = None
    family: Optional[str] = None

    # メンタルヘルス関連
    concerns: Optional[str] = None  # 現在の悩みや不安
    goals: Optional[str] = None  # 目標や願望
    personality: Optional[str] = None  # 性格的特徴
    experiences: Optional[str] = None  # 重要な体験
    symptoms: Optional[str] = None  # メンタル・身体的症状
    triggers: Optional[str] = None  # ストレス要因
    coping_methods: Optional[str] = None  # 対処法
    support_system: Optional[str] = None  # サポート体制
    medication: Optional[str] = None  # 服薬・通院状況
    work_status: Optional[str] = None  # 勤務・休職・復職状況
    daily_routine: Optional[str] = None  # 日常の過ごし方
    emotional_state: Optional[str] = None  # 現在の気持ち・感情状態

    # メタデータ
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)

    def to_json(self) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class UserProfileSystem:
    """ユーザープロファイル管理システム"""

    def __init__(self, db_path: str = "./user_profiles.db", openai_api_key: Optional[str] = None):
        self.db_path = db_path
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

        # データベース初期化
        self._initialize_database()

    def _initialize_database(self):
        """SQLiteデータベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                job TEXT,
                hobbies TEXT,
                age TEXT,
                location TEXT,
                family TEXT,
                concerns TEXT,
                goals TEXT,
                personality TEXT,
                experiences TEXT,
                symptoms TEXT,
                triggers TEXT,
                coping_methods TEXT,
                support_system TEXT,
                medication TEXT,
                work_status TEXT,
                daily_routine TEXT,
                emotional_state TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON user_profiles(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_updated_at ON user_profiles(updated_at)')

        conn.commit()
        conn.close()
        print(f"User profile database initialized at {self.db_path}")

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """ユーザープロファイルを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # SQLiteの行をUserProfileに変換
        hobbies_str = row[3]
        hobbies = json.loads(hobbies_str) if hobbies_str else []

        return UserProfile(
            user_id=row[0],
            name=row[1],
            job=row[2],
            hobbies=hobbies,
            age=row[4],
            location=row[5],
            family=row[6],
            concerns=row[7],
            goals=row[8],
            personality=row[9],
            experiences=row[10],
            symptoms=row[11],
            triggers=row[12],
            coping_methods=row[13],
            support_system=row[14],
            medication=row[15],
            work_status=row[16],
            daily_routine=row[17],
            emotional_state=row[18],
            created_at=row[19],
            updated_at=row[20]
        )

    def create_or_update_profile(self, profile: UserProfile) -> bool:
        """ユーザープロファイルを作成または更新"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if not profile.created_at:
            profile.created_at = datetime.now().isoformat()
        profile.updated_at = datetime.now().isoformat()

        hobbies_json = json.dumps(profile.hobbies, ensure_ascii=False)

        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles (
                user_id, name, job, hobbies, age, location, family,
                concerns, goals, personality, experiences, symptoms,
                triggers, coping_methods, support_system, medication,
                work_status, daily_routine, emotional_state,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile.user_id, profile.name, profile.job, hobbies_json,
            profile.age, profile.location, profile.family,
            profile.concerns, profile.goals, profile.personality,
            profile.experiences, profile.symptoms, profile.triggers,
            profile.coping_methods, profile.support_system, profile.medication,
            profile.work_status, profile.daily_routine, profile.emotional_state,
            profile.created_at, profile.updated_at
        ))

        conn.commit()
        conn.close()
        return True

    async def extract_and_update_profile(self, user_id: str, user_message: str,
                                        ai_response: str = "") -> bool:
        """会話からプロファイル情報を抽出して更新"""
        existing_profile = self.get_profile(user_id)

        if not existing_profile:
            existing_profile = UserProfile(user_id=user_id)

        # LLMで情報抽出
        extracted_info = await self._extract_info_from_message(user_message, ai_response)

        if not extracted_info:
            return False

        # 既存のプロファイルを更新
        updated = False

        for field_name, field_value in extracted_info.items():
            if field_value is None:
                continue

            # hobbiesは特別処理（リスト）
            if field_name == "hobbies" and isinstance(field_value, list):
                new_hobbies = [h for h in field_value if h not in existing_profile.hobbies]
                if new_hobbies:
                    existing_profile.hobbies.extend(new_hobbies)
                    updated = True
            else:
                # その他のフィールドは直接更新
                current_value = getattr(existing_profile, field_name, None)
                if field_value and str(field_value).strip() and field_value != current_value:
                    setattr(existing_profile, field_name, field_value)
                    updated = True

        if updated:
            self.create_or_update_profile(existing_profile)

        return updated

    async def _extract_info_from_message(self, user_message: str,
                                         ai_response: str = "") -> Dict[str, Any]:
        """メッセージから情報を抽出"""
        if not self.client:
            # フォールバック：簡易的なキーワードベース抽出
            return self._fallback_extraction(user_message)

        extraction_prompt = f"""
以下のユーザーメッセージからメンタルヘルス関連情報と個人情報を抽出してください。
メンタルバリアフリーの観点から、ユーザーの感情や状況を個性として捉え、細かな変化も記録してください。

ユーザーメッセージ: "{user_message}"

以下のフォーマットで回答してください（JSONのみ）:
{{
    "name": "名前（明確に述べられた場合のみ）",
    "job": "職業・仕事内容",
    "hobbies": ["趣味1", "趣味2"],
    "age": "年齢",
    "location": "住んでいる場所",
    "family": "家族構成に関する情報",
    "concerns": "現在の悩みや不安・心配事",
    "goals": "目標や願望・やりたいこと",
    "personality": "性格的特徴・個性",
    "experiences": "重要な体験や出来事",
    "symptoms": "メンタル・身体的症状（睡眠、食欲、気分変化等）",
    "triggers": "ストレス要因・きっかけ",
    "coping_methods": "対処法・リラックス方法・気分転換",
    "support_system": "サポート体制・相談相手",
    "medication": "服薬・通院状況",
    "work_status": "勤務・休職・復職状況",
    "daily_routine": "日常の過ごし方・生活リズム",
    "emotional_state": "現在の気持ち・感情状態・心境"
}}

注意:
- 明確に言及されていない情報は null にしてください
- 小さな変化や気づきも記録してください
- 感情の変化は特に丁寧に抽出してください
- 推測ではなく、実際に述べられた内容のみ抽出してください
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたはメンタルヘルス情報を正確に抽出するAIアシスタントです。JSONフォーマットでのみ回答してください。"},
                    {"role": "user", "content": extraction_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )

            extracted_text = response.choices[0].message.content.strip()

            # JSONパース
            if extracted_text.startswith('```json'):
                extracted_text = extracted_text[7:-3].strip()
            elif extracted_text.startswith('```'):
                extracted_text = extracted_text[3:-3].strip()

            return json.loads(extracted_text)

        except Exception as e:
            print(f"Error in profile extraction: {e}")
            return self._fallback_extraction(user_message)

    def _fallback_extraction(self, user_message: str) -> Dict[str, Any]:
        """フォールバック：簡易的なキーワードベース抽出"""
        extracted = {}
        message_lower = user_message.lower()

        # メンタルヘルス関連のキーワードマッチング
        if any(word in message_lower for word in ['不安', '心配', '悩み', '困って', '辛い', '苦しい']):
            extracted['concerns'] = user_message
        if any(word in message_lower for word in ['目標', 'やりたい', '頑張り', '復職', '改善']):
            extracted['goals'] = user_message
        if any(word in message_lower for word in ['眠れない', '食欲', '体調', '症状', '痛み', '疲れ']):
            extracted['symptoms'] = user_message
        if any(word in message_lower for word in ['ストレス', 'プレッシャー', '原因', 'きっかけ']):
            extracted['triggers'] = user_message
        if any(word in message_lower for word in ['散歩', 'リラックス', '気分転換', '対処']):
            extracted['coping_methods'] = user_message

        return extracted

    def get_profile_summary(self, user_id: str) -> str:
        """プロファイルの要約を取得"""
        profile = self.get_profile(user_id)

        if not profile:
            return "プロファイル情報がありません。"

        summary_parts = []

        # 基本情報
        if profile.name:
            summary_parts.append(f"名前: {profile.name}")
        if profile.age:
            summary_parts.append(f"年齢: {profile.age}")
        if profile.job:
            summary_parts.append(f"職業: {profile.job}")
        if profile.hobbies:
            summary_parts.append(f"趣味: {', '.join(profile.hobbies)}")

        # メンタルヘルス情報
        if profile.concerns:
            summary_parts.append(f"主な悩み: {profile.concerns[:100]}...")
        if profile.goals:
            summary_parts.append(f"目標: {profile.goals[:100]}...")
        if profile.symptoms:
            summary_parts.append(f"症状: {profile.symptoms[:100]}...")
        if profile.work_status:
            summary_parts.append(f"勤務状況: {profile.work_status[:100]}...")

        return "\n".join(summary_parts) if summary_parts else "プロファイル情報がありません。"

    def delete_profile(self, user_id: str) -> bool:
        """プロファイルを削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM user_profiles WHERE user_id = ?', (user_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted


# グローバルインスタンス
user_profile_system = UserProfileSystem()
