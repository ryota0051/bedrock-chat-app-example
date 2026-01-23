'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Message } from '@/types';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`py-6 ${isUser ? 'bg-transparent' : 'bg-[#2f2f2f]'}`}>
      <div className="max-w-3xl mx-auto px-4 flex gap-4">
        <div
          className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-medium ${
            isUser
              ? 'bg-[#5436DA] text-white'
              : 'bg-[#10a37f] text-white'
          }`}
        >
          {isUser ? 'U' : 'AI'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-white mb-1">
            {isUser ? 'You' : 'Assistant'}
          </div>
          <div className="prose prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const isInline = !match && !className;

                  if (isInline) {
                    return (
                      <code
                        className="px-1.5 py-0.5 bg-[#404040] rounded text-[#e6e6e6] text-sm"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  }

                  return (
                    <SyntaxHighlighter
                      style={oneDark}
                      language={match?.[1] || 'text'}
                      PreTag="div"
                      customStyle={{
                        margin: '1rem 0',
                        borderRadius: '0.5rem',
                        fontSize: '0.875rem',
                      }}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  );
                },
                p({ children }) {
                  return <p className="mb-4 last:mb-0 text-[#ececec] leading-7">{children}</p>;
                },
                ul({ children }) {
                  return <ul className="list-disc list-inside mb-4 text-[#ececec]">{children}</ul>;
                },
                ol({ children }) {
                  return <ol className="list-decimal list-inside mb-4 text-[#ececec]">{children}</ol>;
                },
                li({ children }) {
                  return <li className="mb-1">{children}</li>;
                },
                a({ href, children }) {
                  return (
                    <a href={href} className="text-[#10a37f] hover:underline" target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  );
                },
                blockquote({ children }) {
                  return (
                    <blockquote className="border-l-4 border-[#565656] pl-4 my-4 text-gray-400 italic">
                      {children}
                    </blockquote>
                  );
                },
                h1({ children }) {
                  return <h1 className="text-2xl font-bold text-white mb-4 mt-6">{children}</h1>;
                },
                h2({ children }) {
                  return <h2 className="text-xl font-bold text-white mb-3 mt-5">{children}</h2>;
                },
                h3({ children }) {
                  return <h3 className="text-lg font-bold text-white mb-2 mt-4">{children}</h3>;
                },
                table({ children }) {
                  return (
                    <div className="overflow-x-auto my-4">
                      <table className="min-w-full border border-[#565656]">{children}</table>
                    </div>
                  );
                },
                th({ children }) {
                  return (
                    <th className="border border-[#565656] px-4 py-2 bg-[#404040] text-white font-medium">
                      {children}
                    </th>
                  );
                },
                td({ children }) {
                  return (
                    <td className="border border-[#565656] px-4 py-2 text-[#ececec]">{children}</td>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}
