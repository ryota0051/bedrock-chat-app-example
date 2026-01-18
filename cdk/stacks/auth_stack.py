from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_cognito as cognito,
)
from constructs import Construct


class AuthStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognitoユーザープール
        self.user_pool = cognito.UserPool(
            self, "BedrockChatUserPool",
            user_pool_name="bedrock-chat-users",
            # サインイン設定
            sign_in_aliases=cognito.SignInAliases(
                username=True,
                email=False  # Phase 1ではユーザー名のみ
            ),
            # セルフサインアップを有効化
            self_sign_up_enabled=True,
            # パスワードポリシー
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,
            ),
            # アカウント復旧設定（Phase 1では無効）
            account_recovery=cognito.AccountRecovery.NONE,
            # 削除ポリシー（開発用）
            removal_policy=RemovalPolicy.DESTROY,
        )

        # アプリクライアント
        self.user_pool_client = self.user_pool.add_client(
            "BedrockChatAppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,  # USER_PASSWORD_AUTH を有効化
                user_srp=True,
            ),
            # トークンの有効期限
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30),
            # セキュリティ設定
            prevent_user_existence_errors=True,
        )

        # 出力
        from aws_cdk import CfnOutput
        CfnOutput(
            self, "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        CfnOutput(
            self, "UserPoolArn",
            value=self.user_pool.user_pool_arn,
            description="Cognito User Pool ARN"
        )

        CfnOutput(
            self, "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )
