import boto3
import os


class BedrockService:
    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name="us-east-1")
        self.model_id = os.environ.get(
            'BEDROCK_MODEL_ID',
            'us.anthropic.claude-haiku-4-5-20251001-v1:0'
        )
    
    def generate_response(self, user_message):
        """単一メッセージからAI応答を生成"""
        messages = [
            {
                "role": "user",
                "content": [{"text": user_message}]
            }
        ]
        
        response = self.client.converse(
            modelId=self.model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": 2048,
                "temperature": 1.0
            }
        )
        
        return response["output"]["message"]["content"][0]["text"]
    
    def generate_response_with_history(self, history):
        """会話履歴からAI応答を生成"""
        # DynamoDB形式をBedrock形式に変換
        messages = [
            {
                "role": msg['role'],
                "content": [{"text": msg['content']}]
            }
            for msg in history
        ]
        
        response = self.client.converse(
            modelId=self.model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": 2048,
                "temperature": 1.0
            }
        )
        
        return response["output"]["message"]["content"][0]["text"]
