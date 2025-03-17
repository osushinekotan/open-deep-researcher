# Open Deep Researcher

あらゆるトピックについて深い調査を行い、最小限の人間の介入で包括的なレポートを生成するインテリジェントリサーチアシスタントです。

## 特徴

- **包括的な調査**: 複数のデータソースに対してクエリを実行し、自動的にトピックを調査
- **マルチソース検索**: Tavily（ウェブ検索）、arXiv（学術論文）、ローカルドキュメント検索を統合
- **インタラクティブなフィードバック**: 実行前にリサーチ計画へのフィードバックを要求可能
- **構造化されたレポート**: 導入部、構造化されたセクション、結論を含む整理されたレポートを生成
- **深い調査機能**: 有効にすると、サブトピックを動的に深く掘り下げる
- **ドキュメント管理**: 調査用の独自ドキュメントをアップロードして管理
- **マルチユーザーサポート**: 異なるユーザーごとの作業スペースとリサーチ履歴

## アーキテクチャ

Open Deep Researcher は、最新の拡張性のあるアーキテクチャで構築されています：

- **バックエンド**: RESTful API エンドポイントを提供する FastAPI アプリケーション
- **リサーチエンジン**: 複雑な調査ワークフローを編成する LangGraph を使用
- **ストレージ**: ドキュメント用のローカルストレージとリサーチ結果用の SQLite
- **検索プロバイダー**: ウェブとローカル検索メカニズムとの柔軟な統合

## 始め方

### 前提条件

- Python 3.11 以上
- Docker と Docker Compose（オプション）
- 以下の API キー：
  - OpenAI
  - Anthropic（オプション）
  - Tavily

### インストール

#### 方法 1: Docker Compose（推奨）

1. リポジトリをクローンする
2. 環境変数を設定する
   ```bash
   cp backend/.env.example backend/.env
   # backend/.envにAPIキーを編集
   ```
3. サービスを起動する
   ```bash
   docker-compose up -d
   ```
4. http://localhost:3000 でサービスにアクセス

#### 方法 2: ローカル開発

1. リポジトリをクローンする
2. バックエンドのセットアップ：

   ```bash
   cd backend
   cp .env.example .env
   # .envにAPIキーを編集

   # uvパッケージマネージャーをインストール
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv venv

   # 依存関係をインストール
   uv pip install -r requirements.txt
   uv pip install --editable ../

   # 仮想環境を有効化
   source .venv/bin/activate

   # バックエンドを起動
   uvicorn app.main:app --reload
   ```

3. フロントエンドのセットアップ（別のターミナルで）：
   ```bash
   cd frontend
   # 依存関係のインストールとサーバーの起動
   # （フロントエンドのセットアップ手順がここに入ります）
   ```

### LangGraph Studio UI をローカルで実行する

LangGraph Studio は、リサーチワークフローのデバッグと開発のためのビジュアルインターフェイスを提供します：

1. リポジトリをクローンする：

   ```bash
   git clone https://github.com/osushinekotan/open-deep-researcher.git
   cd open-deep-researcher
   ```

2. 環境変数を設定する：

   ```bash
   cp .env.example .env
   # .envにAPIキーを編集
   ```

3. 依存関係をインストールして LangGraph サーバーを起動する：

   ```bash
   # uvパッケージマネージャーをインストール
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # 依存関係をインストールしてLangGraphサーバーを起動
   uv sync
   uv run langgraph dev
   ```

4. サーバーが起動すると、以下が表示されます：

   ```
           Welcome to

   ╦  ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬
   ║  ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤
   ╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴  ┴ ┴

   - 🚀 API: http://127.0.0.1:2024
   - 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
   - 📚 API Docs: http://127.0.0.1:2024/docs
   ```

5. URL をクリックするか、ブラウザにコピーして Studio UI にアクセスします

## API エンドポイント

バックエンドは以下の API エンドポイントを提供します：

### リサーチ

- `POST /api/research/start`: 新しいリサーチを開始
- `GET /api/research/{research_id}/status`: リサーチのステータスを取得
- `GET /api/research/{research_id}/plan`: フィードバック用のリサーチ計画を取得
- `GET /api/research/{research_id}/result`: 完了したリサーチの結果を取得
- `GET /api/research/list`: すべてのリサーチジョブを一覧表示
- `DELETE /api/research/{research_id}`: リサーチジョブを削除

### フィードバック

- `POST /api/feedback/submit`: リサーチ計画にフィードバックを提出

### ドキュメント

- `POST /api/documents/upload`: ドキュメントをアップロード
- `GET /api/documents/list`: アップロードされたドキュメントを一覧表示
- `DELETE /api/documents/{filename}`: ドキュメントを削除
- `PUT /api/documents/{filename}/enable`: リサーチ用のドキュメントを有効/無効化

### ユーザー

- `POST /api/users/create`: 新しいユーザーを作成
- `POST /api/users/login`: ユーザー名でログイン
- `GET /api/users/{username}`: ユーザー情報を取得
- `GET /api/users/{username}/researches`: ユーザーのリサーチ履歴を取得
- `GET /api/users/{username}/documents`: ユーザーのドキュメントを取得

## 設定

システムは様々なパラメータで設定でき、リサーチプロセスをカスタマイズできます：

- 検索プロバイダーの選択と設定
- リサーチの深さと幅
- セクション制限と単語数制約
- 言語モデルの選択
- 出力言語の設定
