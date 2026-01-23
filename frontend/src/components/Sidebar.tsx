'use client';

import { Conversation } from '@/types';
import ConversationItem from './ConversationItem';

interface SidebarProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onLogout: () => void;
  isOpen: boolean;
  onClose: () => void;
  username: string;
}

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onLogout,
  isOpen,
  onClose,
  username,
}: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 bg-[#171717] flex flex-col transform transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* New conversation button */}
        <div className="p-3">
          <button
            onClick={() => {
              onNewConversation();
              onClose();
            }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-[#565656] hover:bg-[#2a2b32] transition-colors text-white text-sm"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            新規チャット
          </button>
        </div>

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto px-2 scrollbar-thin">
          <div className="space-y-1">
            {conversations.map((conv) => (
              <ConversationItem
                key={conv.conversationId}
                conversation={conv}
                isActive={conv.conversationId === currentConversationId}
                onClick={() => {
                  onSelectConversation(conv.conversationId);
                  onClose();
                }}
                onDelete={() => onDeleteConversation(conv.conversationId)}
              />
            ))}
          </div>
          {conversations.length === 0 && (
            <p className="text-gray-500 text-sm text-center py-4">
              会話履歴がありません
            </p>
          )}
        </div>

        {/* User section */}
        <div className="border-t border-[#565656] p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-8 h-8 rounded-full bg-[#5436DA] flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                {username.charAt(0).toUpperCase()}
              </div>
              <span className="text-sm text-gray-200 truncate">{username}</span>
            </div>
            <button
              onClick={onLogout}
              className="p-2 hover:bg-[#2a2b32] rounded-lg transition-colors"
              title="ログアウト"
            >
              <svg
                className="w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
