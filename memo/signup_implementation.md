# アカウント作成機能の実装計画

## 概要

現在のチャットアプリはログインページのみで、ユーザーはAWS CLIで手動作成する必要がある。セルフサインアップ機能(メール認証付き)を追加し、ユーザーが自分でアカウントを作成できるようにする。

**ユーザーフロー**: サインアップフォーム → メールで確認コード受信 → コード入力 → ログインページへリダイレクト

## 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `cdk/stacks/auth_stack.py` | 修正 | email属性追加、メール検証設定 |
| `frontend/src/lib/cognito.ts` | 修正 | signUp/confirmSignUp/resendCode関数追加 |
| `frontend/src/app/signup/page.tsx` | 新規 | 2ステップのサインアップページ |
| `frontend/src/app/login/page.tsx` | 修正 | サインアップへのリンク追加 + 確認完了メッセージ |

---

## 1. CDK: `cdk/stacks/auth_stack.py`

Cognito User Poolに以下のパラメータを追加する。

```python
self.user_pool = cognito.UserPool(
    self, "BedrockChatUserPool",
    user_pool_name="bedrock-chat-users",
    sign_in_aliases=cognito.SignInAliases(
        username=True,
        email=False,  # サインインはユーザー名のみ（emailはサインアップ時に収集）
    ),
    self_sign_up_enabled=True,
    # ★追加: メール検証設定
    user_verification=cognito.UserVerificationConfig(
        email_subject="Bedrock Chat - 確認コード",
        email_body="あなたの確認コードは {####} です。",
        email_style=cognito.VerificationEmailStyle.CODE,
    ),
    # ★追加: emailを必須属性に
    standard_attributes=cognito.StandardAttributes(
        email=cognito.StandardAttribute(
            required=True,
            mutable=True,
        ),
    ),
    # ★追加: メールによる自動検証
    auto_verify=cognito.AutoVerifiedAttributes(
        email=True,
    ),
    password_policy=cognito.PasswordPolicy(
        min_length=8,
        require_lowercase=True,
        require_uppercase=True,
        require_digits=True,
        require_symbols=False,
    ),
    # ★変更: NONE → EMAIL_ONLY
    account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
    removal_policy=RemovalPolicy.DESTROY,
)
```

### 注意事項

- User Poolのスキーマ変更(email属性追加)によりUser Poolが**再作成**される（既存ユーザーは失われる）
- `RemovalPolicy.DESTROY`設定済みのため開発環境では問題なし
- デプロイ後に新しいUser Pool ID / Client IDで`.env`を更新する必要あり
- Cognito デフォルトメール送信の上限は50通/日（開発用途では十分、本番ではSES連携が必要）

---

## 2. Frontend: `frontend/src/lib/cognito.ts`

既存の`login()`パターンに準拠して3つの関数とインターフェースを追加する。

### 追加するimport

```typescript
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserSession,
  CognitoUserAttribute,  // 追加
  ISignUpResult,          // 追加
} from 'amazon-cognito-identity-js';
```

### 追加するインターフェース

```typescript
export interface SignUpResult {
  success: boolean;
  userConfirmed?: boolean;
  error?: string;
}

export interface ConfirmResult {
  success: boolean;
  error?: string;
}

export interface ResendCodeResult {
  success: boolean;
  error?: string;
}
```

### signUp関数

```typescript
export async function signUp(
  username: string,
  email: string,
  password: string
): Promise<SignUpResult> {
  return new Promise((resolve) => {
    try {
      const pool = getUserPool();
      const attributeList: CognitoUserAttribute[] = [
        new CognitoUserAttribute({ Name: 'email', Value: email }),
      ];

      pool.signUp(username, password, attributeList, [], (err, result) => {
        if (err) {
          let errorMessage = 'アカウントの作成に失敗しました';
          if (err.name === 'UsernameExistsException') {
            errorMessage = 'アカウントの作成に失敗しました。入力内容を確認してください';
          } else if (err.name === 'InvalidPasswordException') {
            errorMessage = 'パスワードがポリシーを満たしていません';
          } else if (err.name === 'InvalidParameterException') {
            errorMessage = '入力内容に不正な値があります';
          } else if (err.name === 'TooManyRequestsException' || err.name === 'LimitExceededException') {
            errorMessage = 'リクエストが多すぎます。しばらく待ってから再試行してください';
          } else if (err.name === 'NetworkError') {
            errorMessage = 'ネットワークエラーが発生しました。接続を確認してください';
          }
          resolve({ success: false, error: errorMessage });
          return;
        }
        resolve({ success: true, userConfirmed: result?.userConfirmed ?? false });
      });
    } catch (error) {
      resolve({
        success: false,
        error: error instanceof Error ? error.message : 'アカウントの作成に失敗しました',
      });
    }
  });
}
```

### confirmSignUp関数

```typescript
export async function confirmSignUp(
  username: string,
  code: string
): Promise<ConfirmResult> {
  return new Promise((resolve) => {
    try {
      const pool = getUserPool();
      const cognitoUser = new CognitoUser({ Username: username, Pool: pool });

      cognitoUser.confirmRegistration(code, false, (err) => {
        if (err) {
          let errorMessage = '確認に失敗しました';
          if (err.name === 'CodeMismatchException') {
            errorMessage = '確認コードが正しくありません';
          } else if (err.name === 'ExpiredCodeException') {
            errorMessage = '確認コードの有効期限が切れています。再送信してください';
          } else if (err.name === 'TooManyRequestsException' || err.name === 'LimitExceededException') {
            errorMessage = 'リクエストが多すぎます。しばらく待ってから再試行してください';
          } else if (err.name === 'NotAuthorizedException') {
            errorMessage = 'このアカウントは既に確認済みです';
          } else if (err.name === 'NetworkError') {
            errorMessage = 'ネットワークエラーが発生しました。接続を確認してください';
          }
          resolve({ success: false, error: errorMessage });
          return;
        }
        resolve({ success: true });
      });
    } catch (error) {
      resolve({
        success: false,
        error: error instanceof Error ? error.message : '確認に失敗しました',
      });
    }
  });
}
```

### resendConfirmationCode関数

```typescript
export async function resendConfirmationCode(
  username: string
): Promise<ResendCodeResult> {
  return new Promise((resolve) => {
    try {
      const pool = getUserPool();
      const cognitoUser = new CognitoUser({ Username: username, Pool: pool });

      cognitoUser.resendConfirmationCode((err) => {
        if (err) {
          let errorMessage = '確認コードの再送信に失敗しました';
          if (err.name === 'TooManyRequestsException' || err.name === 'LimitExceededException') {
            errorMessage = 'リクエストが多すぎます。しばらく待ってから再試行してください';
          } else if (err.name === 'NetworkError') {
            errorMessage = 'ネットワークエラーが発生しました。接続を確認してください';
          }
          resolve({ success: false, error: errorMessage });
          return;
        }
        resolve({ success: true });
      });
    } catch (error) {
      resolve({
        success: false,
        error: error instanceof Error ? error.message : '確認コードの再送信に失敗しました',
      });
    }
  });
}
```

### 既存login()への追加

`login()`のエラーハンドリングに`UserNotConfirmedException`を追加:

```typescript
// 既存のonFailureハンドラー内に追加
} else if (err.code === 'UserNotConfirmedException') {
  errorMessage = 'アカウントが未確認です。メールに送信された確認コードを入力してください';
}
```

---

## 3. Frontend: `frontend/src/app/signup/page.tsx` (新規作成)

ログインページと同じダークテーマ・カードレイアウトで2ステップのページを作成する。

### ステップ1 - サインアップフォーム

- ユーザー名、メールアドレス、パスワード、パスワード確認の4フィールド
- パスワード要件のリアルタイム表示
- 「ログイン」ページへのリンク

### パスワードバリデーション（クライアント側）

Cognitoのパスワードポリシーをミラーする:

| ルール | チェック | 表示テキスト |
|---|---|---|
| 最小8文字 | `pwd.length >= 8` | 8文字以上 |
| 大文字必須 | `/[A-Z]/.test(pwd)` | 大文字(A-Z)を含む |
| 小文字必須 | `/[a-z]/.test(pwd)` | 小文字(a-z)を含む |
| 数字必須 | `/[0-9]/.test(pwd)` | 数字(0-9)を含む |
| 一致確認 | `pwd === confirmPwd` | パスワードが一致 |

各ルールは満たされると緑色(`text-[#10a37f]`)、未達成は灰色(`text-gray-500`)で表示。

### ステップ2 - 確認コード入力

- 6桁コード入力フィールド（`inputMode="numeric"`, `maxLength={6}`）
- 「確認コードを再送信」リンク
- 成功時 → `/login?verified=true` へリダイレクト

### UIスタイル（ログインページと統一）

- 外枠: `min-h-screen bg-[#212121] flex items-center justify-center p-4`
- カード: `w-full max-w-md` > `bg-[#2f2f2f] rounded-2xl p-8 shadow-xl`
- 入力フィールド: `w-full px-4 py-3 bg-[#404040] border border-[#565656] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#10a37f] focus:ring-1 focus:ring-[#10a37f] transition-colors`
- エラー表示: `p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-400 text-sm`
- 成功表示: `p-3 bg-green-900/30 border border-green-700/50 rounded-lg text-green-400 text-sm`
- ボタン: `w-full py-3 bg-[#10a37f] hover:bg-[#1a7f64] text-white font-medium rounded-lg`

---

## 4. Frontend: `frontend/src/app/login/page.tsx`

### 変更点

1. **サインアップリンク追加**: フォーム下部に「アカウントをお持ちでないですか？ アカウント作成」リンク
2. **確認完了メッセージ**: `useSearchParams()`で`?verified=true`を検出し、緑色の成功バナー表示
3. **Suspenseラッパー追加**: `useSearchParams()`使用のためコンポーネントを`Suspense`で囲む

```tsx
// サインアップリンク
<div className="text-center mt-4">
  <p className="text-gray-400 text-sm">
    アカウントをお持ちでないですか？{' '}
    <Link href="/signup" className="text-[#10a37f] hover:text-[#1a7f64] transition-colors">
      アカウント作成
    </Link>
  </p>
</div>

// 確認完了メッセージ（verified=trueの場合）
{verified && (
  <div className="p-3 bg-green-900/30 border border-green-700/50 rounded-lg text-green-400 text-sm mb-4">
    メールアドレスの確認が完了しました。ログインしてください。
  </div>
)}
```

---

## 変更不要なファイル

- **`frontend/src/contexts/AuthContext.tsx`**: サインアップは認証前の処理であり、`cognito.ts`の関数を直接呼び出す
- **`frontend/src/types/index.ts`**: 新しい型は`cognito.ts`内で定義（既存の`LoginResult`と同じパターン）

---

## 実装順序

1. `cdk/stacks/auth_stack.py` を修正
2. `cdk deploy BedrockChatAuthStack` でデプロイ → 新しいPool ID/Client IDで`.env`更新
3. `frontend/src/lib/cognito.ts` に関数追加
4. `frontend/src/app/signup/page.tsx` を作成
5. `frontend/src/app/login/page.tsx` を修正

## 検証手順

1. `cdk diff` で変更内容確認 → `cdk deploy` でデプロイ
2. 新しいUser Pool ID / Client IDで`.env.local`を更新
3. `/signup`にアクセスしてフォーム表示を確認
4. パスワード入力時にリアルタイムバリデーションが動作することを確認
5. 有効なデータでサインアップ → メールに確認コードが届くことを確認
6. 確認コード入力 → `/login?verified=true`にリダイレクト + 成功メッセージ表示を確認
7. 新規アカウントでログインできることを確認
8. ログイン ⇔ サインアップ間のリンクが動作することを確認
