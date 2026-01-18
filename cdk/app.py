#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.database_stack import DatabaseStack
from stacks.auth_stack import AuthStack
from stacks.lambda_stack import LambdaStack
from stacks.api_stack import ApiStack

app = cdk.App()

# 環境設定
env = cdk.Environment(region="us-east-1")

# 1. DynamoDBスタック
database_stack = DatabaseStack(
    app, "BedrockChatDatabaseStack",
    env=env
)

# 2. Cognitoスタック
auth_stack = AuthStack(
    app, "BedrockChatAuthStack",
    env=env
)

# 3. Lambdaスタック
lambda_stack = LambdaStack(
    app, "BedrockChatLambdaStack",
    conversations_table=database_stack.conversations_table,
    messages_table=database_stack.messages_table,
    env=env
)

lambda_stack.add_dependency(database_stack)

# 4. API Gatewayスタック
api_stack = ApiStack(
    app, "BedrockChatApiStack",
    lambda_function=lambda_stack.chat_function,
    user_pool=auth_stack.user_pool,
    env=env
)
api_stack.add_dependency(lambda_stack)
api_stack.add_dependency(auth_stack)

app.synth()
