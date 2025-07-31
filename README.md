# 長期記憶機能付きAIメンタルヘルスカウンセラー

## 概要
このプロジェクトは、うつ病で休職中の方や復職を目指している方をサポートするAIメンタルヘルスカウンセラーを提供します。AIは会話の文脈を理解し、ユーザーの過去の発言や状況を記憶しながら、継続的なサポートを提供します。

## 主な機能
- 長期記憶機能による個別化されたカウンセリング
- ユーザー情報の自動抽出と保存
- 会話履歴の保存とCSVエクスポート
- RESTful APIによるフロントエンド・バックエンド間の通信

## 技術スタック
### バックエンド
- FastAPI (Python)
- OpenAI GPT-4
- In-memory データストレージ

### フロントエンド
- React (TypeScript)

## セットアップ手順

### 環境変数の設定
1. プロジェクトのルートディレクトリに `.env` ファイルを作成
2. 以下の環境変数を設定:
```
OPENAI_API_KEY=your_api_key_here
```

### バックエンドのセットアップ
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### フロントエンドのセットアップ
```bash
cd frontend
npm install
npm start
```

## API エンドポイント

### ユーザー関連
- `POST /api/users` - ユーザー情報の作成/更新
- `GET /api/users/{user_id}` - ユーザー情報の取得
- `DELETE /api/users/{user_id}` - ユーザーデータの削除

### チャット関連
- `POST /api/chat` - AIカウンセラーとのチャット
- `GET /api/conversations/{user_id}` - 会話履歴の取得
- `GET /api/export-conversations/{user_id}` - 会話履歴のCSVエクスポート

## 注意事項
- このAIカウンセラーは医療行為や診断を行いません
- 緊急時や危機的状況では、必ず専門家に相談してください
- ユーザーデータは現在メモリ上に保存されており、サーバー再起動時にクリアされます

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。

---

## 仮想環境（venv）の適用手順

1. **コマンドプロンプトまたはPowerShellを開く**  
   ※ できれば「管理者として実行」で開くとトラブルが少ないです。

2. **`backend`ディレクトリに移動**
   ```bash
   cd backend
   ```

3. **仮想環境を作成**
   ```bash
   python -m venv venv
   ```

4. **仮想環境を有効化**
   - コマンドプロンプトの場合:
     ```bash
     venv\Scripts\activate
     ```
   - PowerShellの場合:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```

5. **依存パッケージをインストール**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

これで仮想環境上に依存パッケージがインストールされ、グローバル環境の競合や権限エラーを回避できます。

---

**補足：**  
仮想環境を有効化した状態で`uvicorn app.main:app --reload`などのコマンドを実行してください。  
作業が終わったら`deactivate`で仮想環境を終了できます。

---

もし自動でコマンドを実行したい場合はお知らせください。