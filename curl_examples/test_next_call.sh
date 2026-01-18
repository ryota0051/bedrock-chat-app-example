ID_TOKEN="XXXX"
API_URL="XXXX"

CONVERSATION_ID="XXXX"

# POST /chat
curl -X POST "$API_URL/chat" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"先ほどの内容を短く要約して\",\"conversationId\":\"$CONVERSATION_ID\"}" | jq -r '.response'
