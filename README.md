# 長期記憶機能付きAIメンタルヘルスカウンセラー

## 概要
このプロジェクトは、うつ病で休職中の方や復職を目指している方をサポートするAIメンタルヘルスカウンセラーを提供します。AIは会話の文脈を理解し、ユーザーの過去の発言や状況を記憶しながら、継続的なサポートを提供します。

## 主な機能
- **カテゴリ別長期記憶システム**: メンタルヘルス特化の情報分類と保存
  - 悩み・心配事、目標・願望、症状・体調、ストレス要因
  - 対処法、サポート体制、医療情報、勤務・復職状況
  - 日常・生活パターン、感情状態など
- **柔軟なデータ管理**: チャット履歴クリア（記憶保持）と完全削除の選択
- **個別化されたカウンセリング**: 蓄積された記憶に基づく継続的サポート
- **会話履歴の保存とCSVエクスポート**: セッション記録の管理
- **RESTful APIによる通信**: フロントエンド・バックエンド間の効率的な連携

## 技術スタック
### バックエンド
- FastAPI (Python)
- OpenAI GPT-4o / GPT-4o-mini (フォールバック対応)
- In-memory データストレージ
- キーワードベース情報抽出（APIキー不要モード対応）

### フロントエンド
- React (TypeScript)
- インラインCSS（Tailwind CSS代替）
- レスポンシブデザイン

## セットアップ手順

### 環境変数の設定
1. `backend` ディレクトリに `.env` ファイルを作成
2. 以下の環境変数を設定（OpenAI APIキーは任意）:
```
OPENAI_API_KEY=your_api_key_here
```
**注意**: APIキーが設定されていない場合、キーワードベースの記憶抽出が動作します。

### バックエンドのセットアップ
```bash
cd backend
# 仮想環境の作成と有効化
python -m venv venv
venv\Scripts\activate  # Windows
# venv/Scripts/activate #bash
# source venv/bin/activate  # macOS/Linux

# 依存関係のインストール
pip install --upgrade pip
pip install -r requirements.txt

# サーバー起動
uvicorn app.main:app --reload
```

### フロントエンドのセットアップ
```bash
cd frontend
# 依存関係のインストール
npm install

# 開発サーバー起動（ポート3001）
npm start
```

アプリケーションは以下でアクセス可能：
- フロントエンド: http://localhost:3001
- バックエンドAPI: http://localhost:8000

## API エンドポイント

### ユーザー関連
- `POST /api/users` - ユーザー情報の作成/更新
- `GET /api/users/{user_id}` - ユーザー情報の取得（記憶カテゴリ含む）
- `DELETE /api/users/{user_id}` - ユーザーデータの完全削除

### チャット関連
- `POST /api/chat` - AIカウンセラーとのチャット（記憶機能付き）
- `GET /api/conversations/{user_id}` - 会話履歴の取得
- `DELETE /api/conversations/{user_id}` - **NEW**: チャット履歴のみクリア（記憶保持）
- `GET /api/export-conversations/{user_id}` - 会話履歴のCSVエクスポート

### ヘルスチェック
- `GET /healthz` - サーバー稼働状況の確認

## 記憶システムの詳細

### カテゴリ別記憶機能
以下のカテゴリで情報を自動分類・保存：

- **💭 悩み・心配事** (`concerns`): 不安や心配事の記録
- **🎯 目標・願望** (`goals`): 目指していることや願望
- **🩺 症状・体調** (`symptoms`): 睡眠、食欲、気分の変化
- **⚠️ ストレス要因** (`triggers`): ストレスの原因や引き金
- **🛠️ 対処法** (`coping_methods`): 有効な対処法やリラックス方法
- **🤝 サポート体制** (`support_system`): 支援者や相談相手
- **💊 医療・服薬情報** (`medication`): 治療や薬物療法の状況
- **💼 勤務・復職状況** (`work_status`): 就労状況や復職の進捗
- **📅 日常・生活パターン** (`daily_routine`): 生活リズムや習慣
- **💭 感情状態** (`emotional_state`): 現在の気持ちや感情

### データ管理オプション
- **チャット履歴クリア**: 会話のみ削除、記憶情報は保持
- **完全データ削除**: 会話履歴と記憶情報の全削除

## 注意事項
- このAIカウンセラーは医療行為や診断を行いません
- 緊急時や危機的状況では、必ず専門家に相談してください
- ユーザーデータは現在メモリ上に保存されており、サーバー再起動時にクリアされます
- 記憶アイテムは最大100件まで保存され、古いものから自動削除されます

## トラブルシューティング

### よくある問題と解決方法

**1. PowerShellでの実行ポリシーエラー**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**2. 仮想環境の有効化について**
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`
- 終了時: `deactivate`

**3. OpenAI APIキーなしでの動作**
- APIキーが設定されていなくても、キーワードベースの記憶抽出が動作します
- 基本的なカウンセリング機能は利用可能です

**4. ポート番号の確認**
- フロントエンド: http://localhost:3001
- バックエンド: http://localhost:8000

## 開発者向け情報

### デバッグ機能
- ブラウザの開発者ツール（F12）でコンソールログを確認
- 記憶情報の抽出過程や保存状況を確認可能

### 環境変数
```bash
# バックエンド/.env
OPENAI_API_KEY=your_api_key_here

# フロントエンド/.env.local  
PORT=3001
REACT_APP_API_URL=http://localhost:8000
```

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。