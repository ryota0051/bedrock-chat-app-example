import json
import uuid
import time
from decimal import Decimal

from services.bedrock_service import BedrockService
from services.dynamodb_service import DynamoDBService


class DecimalEncoder(json.JSONEncoder):
    """DynamoDBのDecimal型をJSONシリアライズ可能にする"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


bedrock_service = BedrockService()
dynamodb_service = DynamoDBService()


def lambda_handler(event, context):
    """メインハンドラー"""
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        # CognitoからユーザーIDを取得
        user_id = event['requestContext']['authorizer']['claims']['sub']

        # ルーティング
        if http_method == 'POST' and path == '/chat':
            body = json.loads(event['body'])
            return handle_chat(body, user_id)

        elif http_method == 'GET' and path == '/conversations':
            params = event.get('queryStringParameters') or {}
            return handle_get_conversations(user_id, params)

        elif http_method == 'GET' and path.startswith('/conversations/'):
            conversation_id = path.split('/')[-1]
            params = event.get('queryStringParameters') or {}
            return handle_get_messages(conversation_id, user_id, params)

        elif http_method == 'DELETE' and path.startswith('/conversations/'):
            conversation_id = path.split('/')[-1]
            return handle_delete_conversation(conversation_id, user_id)

        return response(404, {'error': 'Not found'})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': 'Internal server error'})


def handle_chat(body, user_id):
    """POST /chat のハンドラー"""
    message = body.get('message')
    conversation_id = body.get('conversationId')

    if not message:
        return response(400, {'error': 'message is required'})

    # 新規会話の場合
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        timestamp = int(time.time())
        title = message[:50] + '...' if len(message) > 50 else message

        dynamodb_service.create_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            title=title,
            timestamp=timestamp
        )

    # ユーザーメッセージを保存
    timestamp = int(time.time())
    dynamodb_service.save_message(conversation_id, 'user', message, timestamp)

    # 会話履歴を取得
    history = dynamodb_service.get_conversation_history(conversation_id)

    # Bedrock呼び出し
    ai_response = bedrock_service.generate_response_with_history(history)

    # AI応答を保存
    ai_timestamp = int(time.time())
    dynamodb_service.save_message(conversation_id, 'assistant', ai_response, ai_timestamp)

    # 会話メタデータを更新
    dynamodb_service.update_conversation_metadata(user_id, conversation_id, ai_timestamp)

    return response(200, {
        'conversationId': conversation_id,
        'response': ai_response,
        'timestamp': ai_timestamp
    })


def handle_get_conversations(user_id, params):
    """GET /conversations"""
    limit = int(params.get('limit', 20))

    kwargs = {
        'IndexName': 'userId-updatedAt-index',
        'KeyConditionExpression': 'userId = :uid',
        'ExpressionAttributeValues': {':uid': user_id},
        'ScanIndexForward': False,
        'Limit': limit
    }

    if 'lastEvaluatedKey' in params:
        kwargs['ExclusiveStartKey'] = json.loads(params['lastEvaluatedKey'])

    result = dynamodb_service.conversations_table.query(**kwargs)

    return response(200, {
        'conversations': result['Items'],
        'lastEvaluatedKey': result.get('LastEvaluatedKey')
    })


def handle_get_messages(conversation_id, user_id, params):
    """GET /conversations/{id}"""
    # 権限チェック
    conv = dynamodb_service.conversations_table.get_item(
        Key={'userId': user_id, 'conversationId': conversation_id}
    )
    if 'Item' not in conv:
        return response(404, {'error': 'Conversation not found'})

    limit = int(params.get('limit', 50))

    kwargs = {
        'KeyConditionExpression': 'conversationId = :cid',
        'ExpressionAttributeValues': {':cid': conversation_id},
        'ScanIndexForward': False,
        'Limit': limit
    }

    if 'lastEvaluatedKey' in params:
        kwargs['ExclusiveStartKey'] = json.loads(params['lastEvaluatedKey'])

    result = dynamodb_service.messages_table.query(**kwargs)

    return response(200, {
        'conversationId': conversation_id,
        'messages': result['Items'],
        'lastEvaluatedKey': result.get('LastEvaluatedKey')
    })


def handle_delete_conversation(conversation_id, user_id):
    """DELETE /conversations/{id}"""
    # 権限チェック
    conv = dynamodb_service.conversations_table.get_item(
        Key={'userId': user_id, 'conversationId': conversation_id}
    )
    if 'Item' not in conv:
        return response(404, {'error': 'Conversation not found'})

    # 会話削除
    dynamodb_service.conversations_table.delete_item(
        Key={'userId': user_id, 'conversationId': conversation_id}
    )

    # メッセージ全削除
    messages = dynamodb_service.get_conversation_history(conversation_id)

    with dynamodb_service.messages_table.batch_writer() as batch:
        for msg in messages:
            batch.delete_item(
                Key={'conversationId': conversation_id, 'timestamp': msg['timestamp']}
            )

    return response(200, {
        'message': 'Conversation deleted successfully',
        'conversationId': conversation_id
    })


def response(status_code, body):
    """レスポンスヘルパー"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
