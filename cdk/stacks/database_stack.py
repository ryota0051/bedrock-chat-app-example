from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Conversationsテーブル
        self.conversations_table = dynamodb.Table(
            self, "ConversationsTable",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="conversationId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # 開発用（本番ではRETAINに変更）
        )
        
        # GSI: userId-updatedAt-index
        self.conversations_table.add_global_secondary_index(
            index_name="userId-updatedAt-index",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updatedAt",
                type=dynamodb.AttributeType.NUMBER
            ),
        )

        # Messagesテーブル
        self.messages_table = dynamodb.Table(
            self, "MessagesTable",
            partition_key=dynamodb.Attribute(
                name="conversationId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # 開発用
        )

        # 出力
        from aws_cdk import CfnOutput
        CfnOutput(
            self, "ConversationsTableName",
            value=self.conversations_table.table_name,
            description="Conversations table name"
        )

        CfnOutput(
            self, "MessagesTableName",
            value=self.messages_table.table_name,
            description="Messages table name"
        )
