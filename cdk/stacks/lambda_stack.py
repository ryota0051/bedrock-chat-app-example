from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class LambdaStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        conversations_table: dynamodb.Table,
        messages_table: dynamodb.Table,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Lambda実行ロール
        lambda_role = iam.Role(
            self, "BedrockChatLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Bedrock呼び出し権限
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=["*"]
            )
        )

        # Lambda関数
        self.chat_function = lambda_.Function(
            self, "BedrockChatFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "BEDROCK_MODEL_ID": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
                "CONVERSATIONS_TABLE_NAME": conversations_table.table_name,
                "MESSAGES_TABLE_NAME": messages_table.table_name,
            }
        )

        # DynamoDBアクセス権限を付与
        conversations_table.grant_read_write_data(self.chat_function)
        messages_table.grant_read_write_data(self.chat_function)

        # 出力
        from aws_cdk import CfnOutput
        CfnOutput(
            self, "LambdaFunctionName",
            value=self.chat_function.function_name,
            description="Lambda function name"
        )

        CfnOutput(
            self, "LambdaFunctionArn",
            value=self.chat_function.function_arn,
            description="Lambda function ARN"
        )
