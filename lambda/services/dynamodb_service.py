import boto3
import uuid
import os


class DynamoDBService:
    def __init__(self):
        dynamodb = boto3.resource('dynamodb')
        self.conversations_table = dynamodb.Table(
            os.environ['CONVERSATIONS_TABLE_NAME']
        )
        self.messages_table = dynamodb.Table(
            os.environ['MESSAGES_TABLE_NAME']
        )

    def create_conversation(self, user_id, conversation_id, title, timestamp):
        """新規会話を作成"""
        self.conversations_table.put_item(
            Item={
                'userId': user_id,
                'conversationId': conversation_id,
                'title': title,
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'messageCount': 0
            }
        )

    def save_message(self, conversation_id, role, content, timestamp):
        """メッセージを保存"""
        self.messages_table.put_item(
            Item={
                'conversationId': conversation_id,
                'timestamp': timestamp,
                'messageId': str(uuid.uuid4()),
                'role': role,
                'content': content
            }
        )

    def get_conversation_history(self, conversation_id):
        """会話履歴を取得"""
        response = self.messages_table.query(
            KeyConditionExpression='conversationId = :cid',
            ExpressionAttributeValues={':cid': conversation_id},
            ScanIndexForward=True  # 古い順
        )
        return response['Items']

    def update_conversation_metadata(self, user_id, conversation_id, updated_at):
        """会話のメタデータを更新"""
        self.conversations_table.update_item(
            Key={
                'userId': user_id,
                'conversationId': conversation_id
            },
            UpdateExpression='SET updatedAt = :ua, messageCount = messageCount + :inc',
            ExpressionAttributeValues={
                ':ua': updated_at,
                ':inc': 2  # userとassistantの2メッセージ
            }
        )
