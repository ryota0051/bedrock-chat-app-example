'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Message, Conversation } from '@/types';
import {
  sendMessage,
  getConversations,
  getMessages,
  deleteConversation,
} from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import ChatArea from '@/components/ChatArea';

export default function Home() {
  const { user, isLoading: authLoading, logout, getToken } = useAuth();
  const router = useRouter();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  // Load conversations on mount
  const loadConversations = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) return;

      const data = await getConversations(token);
      setConversations(data.conversations);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, [getToken]);

  useEffect(() => {
    if (user && !authLoading) {
      loadConversations();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.username]);

  // Load messages when conversation changes
  const loadMessages = useCallback(async (conversationId: string) => {
    try {
      const token = await getToken();
      if (!token) return;

      const data = await getMessages(conversationId, token);
      // Sort messages by timestamp (ascending)
      const sortedMessages = data.messages.sort((a, b) => a.timestamp - b.timestamp);
      setMessages(sortedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  }, [getToken]);

  const handleSelectConversation = async (conversationId: string) => {
    setCurrentConversationId(conversationId);
    await loadMessages(conversationId);
  };

  const handleNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      const token = await getToken();
      if (!token) return;

      await deleteConversation(conversationId, token);
      setConversations((prev) =>
        prev.filter((conv) => conv.conversationId !== conversationId)
      );

      if (currentConversationId === conversationId) {
        setCurrentConversationId(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!user) return;

    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const token = await getToken();
      if (!token) return;

      const response = await sendMessage(content, token, currentConversationId || undefined);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Update conversation ID if new
      if (!currentConversationId) {
        setCurrentConversationId(response.conversationId);
        // Reload conversations to get the new one
        await loadConversations();
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove the user message on error
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#212121] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-[#10a37f] border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="h-screen bg-[#212121] flex overflow-hidden">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onLogout={handleLogout}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        username={user.username}
      />
      <ChatArea
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        onToggleSidebar={() => setIsSidebarOpen(true)}
      />
    </div>
  );
}
