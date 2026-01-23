export interface Message {
  messageId?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface Conversation {
  conversationId: string;
  userId: string;
  title: string;
  messageCount: number;
  createdAt: number;
  updatedAt: number;
}

export interface ChatResponse {
  conversationId: string;
  response: string;
  timestamp: number;
}

export interface ConversationsResponse {
  conversations: Conversation[];
  lastEvaluatedKey?: Record<string, unknown>;
}

export interface MessagesResponse {
  conversationId: string;
  messages: Message[];
  lastEvaluatedKey?: Record<string, unknown>;
}

export interface User {
  username: string;
  idToken: string;
}
