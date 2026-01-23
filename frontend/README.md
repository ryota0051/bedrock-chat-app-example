# Bedrock Chat Frontend

Amazon Bedrockを使用したChatGPT/Claudeライクなチャットアプリケーションのフロントエンドです。

## 技術スタック

- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- Amazon Cognito (認証)
- react-markdown (Markdown/コードブロック表示)

## 前提条件

- Node.js 18以上
- CDKでバックエンド（API Gateway, Lambda, DynamoDB, Cognito）がデプロイ済みであること

## セットアップ

### 1. 依存関係のインストール

```bash
cd frontend
npm install
```

### 2. 環境変数の設定

`.env.local.example` をコピーして `.env.local` を作成します。

```bash
cp .env.local.example .env.local
```

`.env.local` を編集し、CDKデプロイ時の出力値を設定します。

```env
# API Gateway URL (CDK出力の ApiUrl)
NEXT_PUBLIC_API_URL=https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod

# Cognito User Pool ID (CDK出力の UserPoolId)
NEXT_PUBLIC_COGNITO_USER_POOL_ID=ap-northeast-1_xxxxxxxxx

# Cognito User Pool Client ID (CDK出力の UserPoolClientId)
NEXT_PUBLIC_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx

# Cognito Region
NEXT_PUBLIC_COGNITO_REGION=ap-northeast-1
```

CDKの出力値は以下の方法で確認できます：

- `cdk deploy` 実行時のターミナル出力
- AWSコンソール > CloudFormation > スタック > 出力タブ
- AWSコンソール > API Gateway / Cognito から直接確認

## ローカル開発

### 開発サーバーの起動

```bash
npm run dev
```

ブラウザで http://localhost:3000 にアクセスします。

### ビルド

```bash
npm run build
```

### 本番モードで起動

```bash
npm run start
```

## Vercelへのデプロイ

### 1. GitHubにプッシュ

```bash
git add .
git commit -m "Add frontend"
git push
```

### 2. Vercelでプロジェクトをインポート

1. [Vercel](https://vercel.com) にログイン
2. 「Add New...」→「Project」を選択
3. GitHubリポジトリを選択
4. 以下を設定：
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
5. **Environment Variables** に以下を追加：
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_COGNITO_USER_POOL_ID`
   - `NEXT_PUBLIC_COGNITO_CLIENT_ID`
   - `NEXT_PUBLIC_COGNITO_REGION`
6. 「Deploy」をクリック

### 3. CORSの確認

API GatewayのCORS設定で、Vercelのドメイン（`https://your-app.vercel.app`）からのアクセスが許可されていることを確認してください。現在の設定では全オリジン（`*`）を許可しています。

## 機能

- Cognito認証（ログイン/ログアウト）
- チャットメッセージの送受信
- 会話履歴の保存・読み込み
- 会話の削除
- Markdown/コードブロックのシンタックスハイライト表示
- レスポンシブデザイン（モバイル対応）

## ディレクトリ構成

```
src/
├── app/
│   ├── layout.tsx          # ルートレイアウト
│   ├── page.tsx            # メインページ（チャット）
│   ├── login/page.tsx      # ログインページ
│   └── globals.css         # グローバルスタイル
├── components/
│   ├── ChatArea.tsx        # チャットエリア
│   ├── MessageBubble.tsx   # メッセージ表示
│   ├── MessageInput.tsx    # 入力フォーム
│   ├── Sidebar.tsx         # サイドバー
│   └── ConversationItem.tsx # 会話アイテム
├── contexts/
│   └── AuthContext.tsx     # 認証コンテキスト
├── lib/
│   ├── api.ts              # API通信
│   └── cognito.ts          # Cognito認証
└── types/
    └── index.ts            # 型定義
```

## トラブルシューティング

### ログインできない

- `.env.local` の値が正しいか確認
- Cognitoユーザープールにユーザーが作成されているか確認
- ブラウザの開発者ツールでエラーを確認

### APIエラーが発生する

- API Gateway URLが正しいか確認
- Lambda関数が正常にデプロイされているか確認
- CORSの設定を確認

### ビルドエラー

```bash
# node_modulesを削除して再インストール
rm -rf node_modules
npm install
```
