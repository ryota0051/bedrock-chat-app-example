from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_cognito as cognito,
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        lambda_function: lambda_.Function,
        user_pool: cognito.UserPool,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito Authorizer
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "BedrockChatAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # REST API
        api = apigateway.RestApi(
            self, "BedrockChatApi",
            rest_api_name="Bedrock Chat API",
            description="ChatGPT-like chat API using Bedrock",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    'Content-Type',
                    'Authorization',
                    'X-Amz-Date',
                    'X-Api-Key',
                    'X-Amz-Security-Token'
                ]
            ),
        )

        # Lambda統合
        lambda_integration = apigateway.LambdaIntegration(
            lambda_function,
            proxy=True,
        )

        # POST /chat
        chat_resource = api.root.add_resource("chat")
        chat_resource.add_method(
            "POST",
            lambda_integration,
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # GET /conversations
        conversations_resource = api.root.add_resource("conversations")
        conversations_resource.add_method(
            "GET",
            lambda_integration,
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # GET /conversations/{conversationId}
        conversation_detail = conversations_resource.add_resource("{conversationId}")
        conversation_detail.add_method(
            "GET",
            lambda_integration,
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # DELETE /conversations/{conversationId}
        conversation_detail.add_method(
            "DELETE",
            lambda_integration,
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # 出力
        from aws_cdk import CfnOutput
        CfnOutput(
            self, "ApiUrl",
            value=api.url,
            description="API Gateway URL"
        )

        CfnOutput(
            self, "ApiId",
            value=api.rest_api_id,
            description="API Gateway ID"
        )
