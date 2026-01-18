ID_TOKEN="XXXX"
API_URL="XXXX"

# POST /chat
curl -X POST "$API_URL/chat" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Google Colab（のT4）ではどの大きさのモデルまでSFT可能か？"}' | jq -r '.response'
