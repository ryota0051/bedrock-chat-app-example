## 概要

Bedrockを使用したチャットAPIのバックエンド。

## 使用技術

- 認証、認可：Cognito

- API：API Gateway

- バックエンド：Lambda

- 会話履歴保存：DynamoDB

- LLM：Bedrock(Claude 4.5 Haiku)

- UI(ローカル稼働)：Gradio

- インフラ構築：AWS CDK(Python)

## インフラ構築方法

0. `aws login`などで認証を実施する

1. `cdkディレクトリに移動`

2. `python -m venv .venv`で仮想環境を作成(uvでも可能だと思われる)

3. `pip install -r requirements.txt`で必要なライブラリをインストールする

4. `cdk bootstrap`で初期セットアップを行う

5. `cdk deploy --all`でインフラ構築を実施

## Cognitoでユーザー作成方法

今回は簡単のため、ユーザー名による認証としている。

### ステップ1: Cognitoデプロイ情報の取得

`aws cloudformation describe-stacks --stack-name BedrockChatAuthStack --region us-east-1 --query "Stacks[0].Outputs"` から下記をメモしておく

- **UserPoolClientId**: `xxxxxxxxxxxxxxxxxxxxxxxxxx`

### ステップ2: テストユーザーの作成

AWS CLIでユーザーを作成する

#### PowerShellの場合

```powershell
# ユーザー作成
aws cognito-idp admin-create-user `
  --user-pool-id us-east-1_XXXXXXX `
  --username testuser `
  --temporary-password TestPass123! `
  --region us-east-1
```

#### Bashの場合

```bash
# ユーザー作成
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_XXXXXXX \
  --username testuser \
  --temporary-password TestPass123! \
  --region us-east-1
```

### ステップ3: パスワードの永続化

### PowerShellの場合

```powershell
aws cognito-idp admin-set-user-password `
  --user-pool-id us-east-1_XXXXXXX `
  --username testuser `
  --password TestPass123! `
  --permanent `
  --region us-east-1
```

### Bashの場合

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_XXXXXXX \
  --username testuser \
  --password TestPass123! \
  --permanent \
  --region us-east-1
```

**成功すると何も出力されない（エラーがなければOK）**


## gradioを使ったバックエンド呼び出し

1. `aws cloudformation describe-stacks --stack-name BedrockChatApiStack --region us-east-1 --query "Stacks[0].Outputs"` から`ApiUrl`を取得する

2. `gradio`ディレクトリに移動

3. `python -m venv .venv`で仮想環境を作成

4. `pip install -r requirements.txt`で必要なライブラリをインストールする

5. `.env.example`を`.env`という名前でコピーして、下記のように設定する

    ```
    API_URL="<ApiUrlの値>"
    USER_POOL_CLIENT_ID="<UserPoolClientId>"
    REGION="us-east-1"
    ```

6. `python app.py`でgradioを起動させて、ブラウザで`http://localhost:7860/`にアクセス

