# リポジトリガイドライン（for Coding Agents）

## 目的 / 成果物
- **このリポジトリの目的**: 長期記憶機能付きAIメンタルヘルスカウンセラーシステム
- **主な機能**: カテゴリ別記憶管理、ユーザープロファイル、感情分析、エピソード記憶
- **技術スタック**: FastAPI (Python) + React (TypeScript) + SQLite + OpenAI GPT
- **変更のゴール**: メンタルヘルスサポート機能の追加・改善、記憶システムの精度向上、UI/UX改善
- **変更しないもの**: 記憶カテゴリ構造、データベーススキーマ、既存API互換性

## 必須ルール（最重要）
- 既存のコードスタイルを維持する（特にバックエンドのコメント、型ヒント）
- 変更は最小差分（不要なリファクタはしない）
- **秘密情報厳守**: `.env`にOpenAI APIキーを保存、Gitには絶対コミットしない
- データベースファイル（`*.db`、`*.db-journal`）はコミットしない
- 依存追加は最小限。追加した理由と代替案を説明する
- ユーザーデータのプライバシーを最優先（個人情報の取り扱いに注意）

## 開発の進め方（推奨フロー）
1. 目的と制約を要約（README.mdとこのファイルを参照）
2. 調査が必要なら先に調査（既存のmain.py、memory_system.py、user_profile.pyなど）
3. 実装 → 動作確認 → フォーマット → 変更点サマリ
4. コミットメッセージは日本語で簡潔に（絵文字+Co-Authored-By: Claude付き）

## ビルド / テスト
### セットアップ
**バックエンド:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install --upgrade pip
pip install -r requirements.txt
```

**フロントエンド:**
```bash
cd frontend
npm install
```

### 代表コマンド
**バックエンド:**
```bash
cd backend
uvicorn app.main:app --reload  # 開発サーバー起動（http://localhost:8000）
```

**フロントエンド:**
```bash
cd frontend
npm start  # 開発サーバー起動（http://localhost:3000）
```

**pytest実行:**
```bash
cd backend
pytest  # テスト実行
pytest -v  # 詳細表示
```

## コーディング規約
- **Python**:
  - 関数/変数は snake_case
  - クラスは PascalCase
  - 定数は UPPER_SNAKE_CASE
  - 型ヒントを必ず使用（`from typing import ...`）
  - Docstringは日本語でOK（「"""説明"""」形式）
- **TypeScript/React**:
  - 関数/変数は camelCase
  - コンポーネントは PascalCase
  - インターフェースは PascalCase + `Props`サフィックス（例: `ModelSettingsProps`）
  - propsの型は必ず定義
- **例外処理**: "静かに握りつぶさない"。`try-except`でキャッチしたら必ずログ出力
- **ログ**: `print()`ではなく適切なロギング（バックエンドはコンソール出力でOK）

## リポジトリ構造（重要ディレクトリ）
```
longterm-memory-proto/
├── backend/
│   ├── app/
│   │   ├── main.py                    # メインAPIエンドポイント
│   │   ├── memory_system.py           # カテゴリ別記憶システム
│   │   ├── user_profile.py            # ユーザープロファイル管理
│   │   ├── extended_profile.py        # 拡張プロファイルシステム
│   │   ├── analysis_layer.py          # 状態分析・推論エンジン
│   │   ├── episodic_memory.py         # エピソード記憶+感情履歴
│   │   ├── memory_consolidation.py    # 記憶統合+関連性分析
│   │   ├── knowledge_base.py          # 知識ベース（RAG用）
│   │   └── config.py                  # 設定ファイル
│   ├── tests/                         # pytest テストファイル
│   ├── requirements.txt               # Python依存関係
│   ├── .env                          # 環境変数（Gitに含めない）
│   └── pytest.ini                    # pytest設定
├── frontend/
│   ├── src/
│   │   ├── App.tsx                    # メインアプリケーション
│   │   ├── ModelSettings.tsx          # GPTモデル設定UI
│   │   ├── ExtendedProfileManager.tsx # プロファイル管理UI
│   │   ├── SystemPromptEditor.tsx     # システムプロンプト編集UI
│   │   ├── MemoryDisplay.tsx          # 記憶表示UI
│   │   └── *.css                      # CSSファイル
│   ├── package.json                   # npm依存関係
│   └── tsconfig.json                  # TypeScript設定
├── data/                              # データファイル（Gitに含めない）
├── .gitignore                         # Git除外設定
├── README.md                          # プロジェクト説明
└── AGENT.md                           # このファイル
```

## よくある落とし穴（Known pitfalls）
- **Windowsパス**: バックスラッシュ（`\`）の扱いに注意。`Path`オブジェクトまたは`os.path.join()`を使用
- **データベースファイル**: `*.db`はGit管理外。コミットしない
- **OpenAI APIキー**: 絶対にコミットしない。`.env`のみに保存
- **ポート番号**: バックエンド（8000）、フロントエンド（3000）が標準
- **CORS**: フロントエンドからのAPIアクセスにはCORS設定が必要（`main.py`で設定済み）
- **データ永続化**:
  - SQLite: ユーザープロファイル、エピソード記憶、感情履歴
  - In-memory: 会話履歴、短期記憶（サーバー再起動で消える）
- **記憶品質**: 5文字未満の記憶、重複記憶（90%以上類似）は自動除外される
- **型チェック**: TypeScriptの型エラーは必ず解消してからコミット

## PR/コミットの方針
- **1コミット = 1目的**（機能追加、バグ修正、リファクタリングを混ぜない）
- **コミットメッセージ形式**:
  ```
  機能追加の簡潔な説明

  - 詳細な変更内容1
  - 詳細な変更内容2

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
- **日本語でOK**: コミットメッセージは日本語で記述
- **変更点サマリ**: 主要な変更をコミットメッセージに明記

## データベース設計ポリシー
- **スキーマ変更は慎重に**: 既存データとの互換性を保つ
- **マイグレーション**: スキーマ変更時は手動マイグレーションスクリプトを用意
- **バックアップ**: 重要な変更前にデータベースファイルをバックアップ

## 記憶システムのルール
- **カテゴリ**: 10種類固定（concerns, goals, symptoms, triggers, coping_methods, support_system, medication, work_status, daily_routine, emotional_state）
- **最小文字数**: 5文字未満の記憶は保存しない
- **重複検出**: Jaccard類似度90%以上は重複とみなす
- **重要度閾値**: 0.15未満の記憶は保存しない
- **最大保存数**: 各カテゴリ最大100件（古いものから削除）

## プロファイルシステムのルール
- **自動抽出**: LLMが会話から18種類の属性を自動抽出
- **更新タイミング**: 各会話後に自動更新
- **JSON形式**: エクスポートはJSON形式（CSV形式は廃止）
- **プライバシー**: 個人情報は慎重に扱い、必要最小限の情報のみ保存

## メンテナンスポリシー（AGENT.mdの更新）
- "会話で繰り返し指示したこと"が出たら、ここにルールとして追記する
- 冗長なら圧縮して短く保つ（密度優先）
- 30日以上更新がない/READMEや構造が変わったら更新を検討する
- **最終更新**: 2026年1月（プロジェクト初期）
