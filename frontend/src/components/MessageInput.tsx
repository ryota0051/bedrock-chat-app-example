'use client';

import { useState, useRef, useEffect, KeyboardEvent, FormEvent } from 'react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-[#565656] bg-[#212121] p-4">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="relative flex items-end bg-[#2f2f2f] rounded-2xl border border-[#565656] focus-within:border-[#8e8ea0] transition-colors">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="メッセージを入力..."
            disabled={disabled}
            rows={1}
            className="flex-1 resize-none bg-transparent text-white placeholder-gray-500 px-4 py-3 focus:outline-none max-h-[200px] scrollbar-thin"
          />
          <button
            type="submit"
            disabled={!message.trim() || disabled}
            className="p-2 m-1.5 rounded-lg bg-white disabled:bg-[#565656] disabled:cursor-not-allowed transition-colors"
          >
            <svg
              className={`w-5 h-5 ${message.trim() && !disabled ? 'text-black' : 'text-[#8e8ea0]'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19V5m0 0l-7 7m7-7l7 7"
              />
            </svg>
          </button>
        </div>
        <p className="text-center text-xs text-gray-500 mt-2">
          Enterで送信、Shift+Enterで改行
        </p>
      </form>
    </div>
  );
}
