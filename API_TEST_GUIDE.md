# 拡張プロファイルAPI テストガイド

## 動作確認済み機能

すべてのプロファイルAPI機能が正常に動作することを確認しました。

## APIエンドポイント一覧

### 1. プロファイル読込
```bash
curl -X GET http://127.0.0.1:8000/api/extended-profile/{user_id}
```

**例:**
```bash
curl -X GET http://127.0.0.1:8000/api/extended-profile/test_user_001
```

**レスポンス:** ユーザーのプロファイル全体がJSON形式で返されます。

---

### 2. プロファイル更新
```bash
curl -X POST http://127.0.0.1:8000/api/extended-profile/{user_id} \
  -H "Content-Type: application/json" \
  -d @profile_data.json
```

**テスト例:**
```bash
curl -X POST http://127.0.0.1:8000/api/extended-profile/test_user_001 \
  -H "Content-Type: application/json" \
  -d @test_profile_update.json
```

**JSONファイル例 (test_profile_update.json):**
```json
{
  "profile_settings": {
    "display_name": "テスト太郎",
    "ai_name": "AIカウンセラー",
    "ai_personality": "優しく寄り添うガイド",
    "response_length_style": "medium"
  },
  "general_profile": {
    "hobbies": ["読書", "散歩"],
    "occupation": "エンジニア",
    "age": "30代"
  },
  "mental_profile": {
    "symptoms": "軽度の不安",
    "coping_methods": "深呼吸、散歩"
  }
}
```

---

### 3. JSONインポート（推奨：ファイルアップロード経由）
```bash
curl -X POST http://127.0.0.1:8000/api/extended-profile/{user_id}/import-file \
  -F "file=@import_data.json"
```

**テスト例:**
```bash
curl -X POST http://127.0.0.1:8000/api/extended-profile/test_user_003/import-file \
  -F "file=@test_profile_import.json"
```

### 3-B. JSONインポート（JSON直接送信）
```bash
curl -X POST http://127.0.0.1:8000/api/extended-profile/{user_id}/import \
  -H "Content-Type: application/json" \
  -d @import_data.json
```

**注意:** JSON直接送信の場合、エスケープの問題が発生する可能性があります。ファイルアップロード経由（`/import-file`）の使用を推奨します。

**JSONファイル例 (test_profile_import.json):**
```json
{
  "profile_settings": {
    "display_name": "インポートユーザー",
    "ai_name": "インポートAI",
    "ai_personality": "明るくポジティブなサポーター",
    "response_length_style": "long"
  },
  "general_profile": {
    "hobbies": ["料理", "ヨガ", "映画鑑賞"],
    "occupation": "デザイナー",
    "age": "20代",
    "location": "東京"
  },
  "mental_profile": {
    "symptoms": "軽度のストレス",
    "triggers": "仕事の締め切り",
    "coping_methods": "ヨガ、音楽鑑賞",
    "support_system": "友人、家族"
  },
  "favorites": {
    "food": "パスタ",
    "beverage": "コーヒー",
    "extra": {
      "movie_genre": "コメディ",
      "music_genre": "ジャズ"
    }
  },
  "important_memories": [
    "2024年に転職を成功させた",
    "週末はヨガ教室に通っている"
  ],
  "goals": [
    "毎日30分の瞑想を習慣化する",
    "来年までに新しいスキルを習得する"
  ]
}
```

**重要な仕様:**
- `important_memories` は文字列の配列またはオブジェクトの配列の両方に対応
- `goals` も文字列の配列またはオブジェクトの配列の両方に対応

---

### 4. JSONエクスポート
```bash
curl -X GET http://127.0.0.1:8000/api/extended-profile/{user_id}/json
```

**テスト例:**
```bash
curl -X GET http://127.0.0.1:8000/api/extended-profile/test_user_002/json
```

**レスポンス:** プロファイル全体がJSON文字列として返されます（ダウンロード/保存用）。

---

### 5. サマリー表示
```bash
curl -X GET http://127.0.0.1:8000/api/extended-profile/{user_id}/summary
```

**テスト例:**
```bash
curl -X GET http://127.0.0.1:8000/api/extended-profile/test_user_002/summary
```

**レスポンス例:**
```json
{
  "user_id": "test_user_002",
  "summary": "## プロファイル設定\n- 表示名: インポートユーザー\n- AI名: インポートAI\n- AI性格: 明るくポジティブなサポーター\n- 応答スタイル: long\n\n## 基本情報\n- 年齢: 20代\n- 職業: デザイナー\n- 住所: 東京\n- 趣味: 料理, ヨガ, 映画鑑賞\n\n## メンタルヘルス状況\n- 症状: 軽度のストレス\n- ストレス要因: 仕事の締め切り\n- 対処法: ヨガ、音楽鑑賞\n- サポート体制: 友人、家族\n\n## 重要な記憶\n- [medium] 2024年に転職を成功させた\n- [medium] 週末はヨガ教室に通っている\n\n## 目標\n- [medium] 毎日30分の瞑想を習慣化する\n- [medium] 来年までに新しいスキルを習得する"
}
```

---

## 修正・追加内容

### 機能追加 (main.py)

1. **ファイルアップロード経由のインポート機能を追加**
   - 新エンドポイント: `POST /api/extended-profile/{user_id}/import-file`
   - ファイルアップロード経由でJSONをインポート可能
   - エスケープの問題が発生しないため、こちらを推奨

### バグ修正 (extended_profile.py)

1. **important_memories のインポート対応**
   - 文字列の配列とオブジェクトの配列の両方に対応
   - 文字列の場合は自動的に `ImportantMemory(text=...)` に変換

2. **goals のインポート対応**
   - 文字列の配列とオブジェクトの配列の両方に対応
   - 文字列の場合は自動的に `Goal(goal=...)` に変換

---

## テスト結果

| 機能 | ステータス |
|------|-----------|
| プロファイル読込 | ✅ 成功 |
| プロファイル更新 | ✅ 成功 |
| JSONインポート | ✅ 成功 |
| JSONエクスポート | ✅ 成功 |
| サマリー表示 | ✅ 成功 |

---

## サーバー起動方法

### バックエンド
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### フロントエンド
```bash
cd frontend
PORT=3000 npm start
```

---

## 注意事項

- curlコマンドでJSONを直接渡す場合、エスケープの問題が発生する可能性があるため、ファイル経由（`-d @file.json`）を推奨
- インポートする際、`important_memories` と `goals` は簡潔な文字列配列形式でも構いません
- すべてのプロファイルデータは `backend/extended_profiles.json` に保存されます
