import { ChatResponse, ConversationsResponse, MessagesResponse } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

async function fetchWithAuth(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<Response> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP Error: ${response.status}`);
  }

  return response;
}

export async function sendMessage(
  message: string,
  token: string,
  conversationId?: string
): Promise<ChatResponse> {
  const body: { message: string; conversationId?: string } = { message };
  if (conversationId) {
    body.conversationId = conversationId;
  }

  const response = await fetchWithAuth('/chat', token, {
    method: 'POST',
    body: JSON.stringify(body),
  });

  return response.json();
}

export async function getConversations(
  token: string,
  limit: number = 20
): Promise<ConversationsResponse> {
  const response = await fetchWithAuth(`/conversations?limit=${limit}`, token);
  return response.json();
}

export async function getMessages(
  conversationId: string,
  token: string,
  limit: number = 50
): Promise<MessagesResponse> {
  const response = await fetchWithAuth(
    `/conversations/${conversationId}?limit=${limit}`,
    token
  );
  return response.json();
}

export async function deleteConversation(
  conversationId: string,
  token: string
): Promise<void> {
  await fetchWithAuth(`/conversations/${conversationId}`, token, {
    method: 'DELETE',
  });
}
