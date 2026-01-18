# Cognito認証 完全ガイド

このガイドでは、デプロイ後のCognito認証からAPI呼び出しまでの手順を説明します。

## 前提条件

- AWS CLIがインストールされている
- CDKでバックエンドがデプロイ済み
- PowerShellまたはBashが使える環境

---

## ステップ1: デプロイ情報の取得

### PowerShellの場合

```powershell
# Cognito情報を取得
aws cloudformation describe-stacks --stack-name BedrockChatAuthStack --region us-east-1 --query "Stacks[0].Outputs"

# API URL を取得
aws cloudformation describe-stacks --stack-name BedrockChatApiStack --region us-east-1 --query "Stacks[0].Outputs"
```

### Bashの場合

```bash
# Cognito情報を取得
aws cloudformation describe-stacks --stack-name BedrockChatAuthStack --region us-east-1 --query "Stacks[0].Outputs"

# API URL を取得
aws cloudformation describe-stacks --stack-name BedrockChatApiStack --region us-east-1 --query "Stacks[0].Outputs"
```

### 取得する情報

出力から以下の値をメモしてください：

- **UserPoolId**: `us-east-1_XXXXXXX`
- **UserPoolClientId**: `xxxxxxxxxxxxxxxxxxxxxxxxxx`
- **ApiUrl**: `https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/`

---

## ステップ2: テストユーザーの作成

### 方法A: AWSマネジメントコンソール（推奨・簡単）

1. **AWSコンソール** にログイン
2. **Amazon Cognito** を開く
3. **ユーザープール** → `bedrock-chat-users` を選択
4. 左メニュー **ユーザー** → **ユーザーを作成** をクリック
5. 以下を入力：
   - **ユーザー名**: `testuser`（任意）
   - **パスワード**: `TestPass123!`（8文字以上、大文字・小文字・数字を含む）
   - **Eメールアドレス**: 空欄でOK
6. **ユーザーを作成** をクリック

### 方法B: AWS CLI

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

---

## ステップ3: パスワードの永続化（重要）

コンソールまたはCLIで作成したユーザーは、初回ログイン時にパスワード変更が必要です。
これをスキップするため、管理者としてパスワードを永続化します。

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

**成功すると何も出力されません（エラーがなければOK）**

---

## ステップ4: トークンの取得

### PowerShellの場合

```powershell
aws cognito-idp initiate-auth `
  --client-id xxxxxxxxxxxxxxxxxxxxxxxxxx `
  --auth-flow USER_PASSWORD_AUTH `
  --auth-parameters USERNAME=testuser,PASSWORD=TestPass123! `
  --region us-east-1
```

### Bashの場合

```bash
aws cognito-idp initiate-auth \
  --client-id xxxxxxxxxxxxxxxxxxxxxxxxxx \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPass123! \
  --region us-east-1
```

### 成功レスポンス例

```json
{
  "AuthenticationResult": {
    "AccessToken": "eyJraWQiOiJ...",
    "IdToken": "eyJraWQiOiJ...",  ← このIdTokenを使用
    "RefreshToken": "eyJjdHkiOi...",
    "ExpiresIn": 3600,
    "TokenType": "Bearer"
  }
}
```

**重要**: `IdToken` の値をコピーしてください（`AccessToken` ではありません）

---

## ステップ5: API呼び出しテスト

### PowerShellの場合

```powershell
# 変数に保存
$IdToken = "eyJraWQiOiJ...（ステップ4でコピーしたIdToken）"
$ApiUrl = "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod"

# 新規会話を開始
$Body = @{
    message = "こんにちは！私の名前はトムです"
} | ConvertTo-Json -Compress

Invoke-RestMethod -Uri "$ApiUrl/chat" `
  -Method Post `
  -Headers @{
    "Authorization" = "Bearer $IdToken"
    "Content-Type" = "application/json"
  } `
  -Body $Body
```

### Bash（WSL/Linux）の場合

```bash
# 変数に保存
ID_TOKEN="eyJraWQiOiJ...（ステップ4でコピーしたIdToken）"
API_URL="https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod"

# 新規会話を開始
curl -X POST "$API_URL/chat" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"こんにちは！私の名前はトムです"}'
```

### 成功レスポンス例

```json
{
  "conversationId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "response": "こんにちは、トムさん！お会いできて嬉しいです。",
  "timestamp": 1737388800
}
```

---

## ステップ6: 会話を継続

### PowerShellの場合

```powershell
# conversationIdを変数に保存（ステップ5のレスポンスから取得）
$ConversationId = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# 会話を継続
$Body = @{
    message = "私の名前は？"
    conversationId = $ConversationId
} | ConvertTo-Json -Compress

Invoke-RestMethod -Uri "$ApiUrl/chat" `
  -Method Post `
  -Headers @{
    "Authorization" = "Bearer $IdToken"
    "Content-Type" = "application/json"
  } `
  -Body $Body
```

### Bashの場合

```bash
# conversationIdを変数に保存（ステップ5のレスポンスから取得）
CONVERSATION_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# 会話を継続
curl -X POST "$API_URL/chat" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"私の名前は？\",\"conversationId\":\"$CONVERSATION_ID\"}"
```

### 期待される応答

```json
{
  "conversationId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "response": "あなたの名前はトムさんですね。先ほど教えていただきました。",
  "timestamp": 1737388850
}
```

---

## その他のエンドポイント

### 会話一覧を取得

#### PowerShell

```powershell
Invoke-RestMethod -Uri "$ApiUrl/conversations" `
  -Method Get `
  -Headers @{
    "Authorization" = "Bearer $IdToken"
  }
```

#### Bash

```bash
curl -X GET "$API_URL/conversations" \
  -H "Authorization: Bearer $ID_TOKEN"
```

### 特定の会話のメッセージ履歴を取得

#### PowerShell

```powershell
Invoke-RestMethod -Uri "$ApiUrl/conversations/$ConversationId" `
  -Method Get `
  -Headers @{
    "Authorization" = "Bearer $IdToken"
  }
```

#### Bash

```bash
curl -X GET "$API_URL/conversations/$CONVERSATION_ID" \
  -H "Authorization: Bearer $ID_TOKEN"
```

### 会話を削除

#### PowerShell

```powershell
Invoke-RestMethod -Uri "$ApiUrl/conversations/$ConversationId" `
  -Method Delete `
  -Headers @{
    "Authorization" = "Bearer $IdToken"
  }
```

#### Bash

```bash
curl -X DELETE "$API_URL/conversations/$CONVERSATION_ID" \
  -H "Authorization: Bearer $ID_TOKEN"
```

---

## よくあるエラーと対処法

### エラー1: `User pool client does not exist`

**原因**: クライアントIDが間違っている、またはリージョンが違う

**対処**:
```bash
# 正しい情報を再取得
aws cloudformation describe-stacks --stack-name BedrockChatAuthStack --region us-east-1 --query "Stacks[0].Outputs"
```

---

### エラー2: `NEW_PASSWORD_REQUIRED`

**原因**: パスワードが一時的なまま（ステップ3をスキップした）

**対処**:
```bash
# パスワードを永続化
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_XXXXXXX \
  --username testuser \
  --password TestPass123! \
  --permanent \
  --region us-east-1
```

---

### エラー3: `USER_PASSWORD_AUTH flow not enabled`

**原因**: アプリクライアントで認証フローが有効になっていない

**対処**:

#### オプションA: CDKで修正（推奨）

`cdk/stacks/auth_stack.py`を確認し、以下が含まれていることを確認：

```python
auth_flows=cognito.AuthFlow(
    user_password=True,  # これが重要
    user_srp=True,
)
```

その後、再デプロイ：
```bash
cd cdk
cdk deploy BedrockChatAuthStack
```

#### オプションB: コンソールで修正

1. Cognitoコンソール → ユーザープール → アプリケーションクライアント
2. クライアントを選択 → 編集
3. 認証フロー → `ALLOW_USER_PASSWORD_AUTH` にチェック
4. 保存

---

### エラー4: トークンの有効期限切れ

**原因**: IdTokenは1時間で期限切れ

**対処**: ステップ4を再実行して新しいトークンを取得

---

### エラー5: `{"error": "Internal server error"}`

**原因**: Lambda関数内でエラーが発生

**対処**:

1. CloudWatch Logsでエラー内容を確認：

```bash
# Lambda関数名を取得
aws cloudformation describe-stacks \
  --stack-name BedrockChatLambdaStack \
  --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
  --output text
```

2. ログを確認：

```bash
# 関数名を変数に保存
FUNCTION_NAME="取得した関数名"

# 最新のログを表示
aws logs tail /aws/lambda/$FUNCTION_NAME --region us-east-1 --follow
```

---

## 完全な実行例（コピペ用）

### PowerShellバージョン

```powershell
# === 設定値（実際の値に置き換え）===
$UserPoolId = "us-east-1_XXXXXXX"
$ClientId = "xxxxxxxxxxxxxxxxxxxxxxxxxx"
$ApiUrl = "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod"
$Username = "testuser"
$Password = "TestPass123!"

# === ユーザー作成 ===
aws cognito-idp admin-create-user `
  --user-pool-id $UserPoolId `
  --username $Username `
  --temporary-password $Password `
  --region us-east-1

# === パスワード永続化 ===
aws cognito-idp admin-set-user-password `
  --user-pool-id $UserPoolId `
  --username $Username `
  --password $Password `
  --permanent `
  --region us-east-1

# === トークン取得 ===
$AuthResponse = aws cognito-idp initiate-auth `
  --client-id $ClientId `
  --auth-flow USER_PASSWORD_AUTH `
  --auth-parameters USERNAME=$Username,PASSWORD=$Password `
  --region us-east-1 | ConvertFrom-Json

$IdToken = $AuthResponse.AuthenticationResult.IdToken

Write-Host "IdToken取得成功: $($IdToken.Substring(0,50))..."

# === API呼び出し ===
$Body = @{
    message = "こんにちは！私の名前はトムです"
} | ConvertTo-Json -Compress

$Response = Invoke-RestMethod -Uri "$ApiUrl/chat" `
  -Method Post `
  -Headers @{
    "Authorization" = "Bearer $IdToken"
    "Content-Type" = "application/json"
  } `
  -Body $Body

Write-Host "ConversationId: $($Response.conversationId)"
Write-Host "Response: $($Response.response)"

# === 会話継続 ===
$ConversationId = $Response.conversationId

$Body2 = @{
    message = "私の名前は？"
    conversationId = $ConversationId
} | ConvertTo-Json -Compress

$Response2 = Invoke-RestMethod -Uri "$ApiUrl/chat" `
  -Method Post `
  -Headers @{
    "Authorization" = "Bearer $IdToken"
    "Content-Type" = "application/json"
  } `
  -Body $Body2

Write-Host "Response: $($Response2.response)"
```

### Bashバージョン

```bash
#!/bin/bash

# === 設定値（実際の値に置き換え）===
USER_POOL_ID="us-east-1_XXXXXXX"
CLIENT_ID="xxxxxxxxxxxxxxxxxxxxxxxxxx"
API_URL="https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod"
USERNAME="testuser"
PASSWORD="TestPass123!"

# === ユーザー作成 ===
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username $USERNAME \
  --temporary-password $PASSWORD \
  --region us-east-1

# === パスワード永続化 ===
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username $USERNAME \
  --password $PASSWORD \
  --permanent \
  --region us-east-1

# === トークン取得 ===
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --client-id $CLIENT_ID \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=$USERNAME,PASSWORD=$PASSWORD \
  --region us-east-1)

ID_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.IdToken')

echo "IdToken取得成功: ${ID_TOKEN:0:50}..."

# === API呼び出し ===
RESPONSE=$(curl -s -X POST "$API_URL/chat" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"こんにちは！私の名前はトムです"}')

echo "Response: $RESPONSE" | jq

CONVERSATION_ID=$(echo $RESPONSE | jq -r '.conversationId')

# === 会話継続 ===
RESPONSE2=$(curl -s -X POST "$API_URL/chat" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"私の名前は？\",\"conversationId\":\"$CONVERSATION_ID\"}")

echo "Response: $RESPONSE2" | jq
```

---

## トラブルシューティング用コマンド

### ユーザーの状態確認

```bash
aws cognito-idp admin-get-user \
  --user-pool-id us-east-1_XXXXXXX \
  --username testuser \
  --region us-east-1
```

### アプリクライアント設定確認

```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_XXXXXXX \
  --client-id xxxxxxxxxxxxxxxxxxxxxxxxxx \
  --region us-east-1
```

### ユーザー一覧確認

```bash
aws cognito-idp list-users \
  --user-pool-id us-east-1_XXXXXXX \
  --region us-east-1
```

### ユーザー削除（やり直す場合）

```bash
aws cognito-idp admin-delete-user \
  --user-pool-id us-east-1_XXXXXXX \
  --username testuser \
  --region us-east-1
```

---

## まとめ

1. **ステップ1**: デプロイ情報を取得
2. **ステップ2**: ユーザーを作成
3. **ステップ3**: パスワードを永続化（重要！）
4. **ステップ4**: IdTokenを取得
5. **ステップ5**: API呼び出し
6. **ステップ6**: 会話継続

**重要なポイント**:
- `IdToken` を使う（`AccessToken` ではない）
- パスワードの永続化を忘れない
- トークンは1時間で期限切れ
- リージョンは必ず `us-east-1` を指定

---

このガイドに従えば、毎回スムーズに認証できるはずです！