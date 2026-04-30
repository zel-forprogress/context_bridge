import type { MessageOut } from '../types'

export default function MessageBubble({ message }: { message: MessageOut }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-md'
            : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md'
        }`}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-medium ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
            {isUser ? 'User' : 'Assistant'}
          </span>
          {message.token_count > 0 && (
            <span className={`text-xs ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
              ~{message.token_count} tokens
            </span>
          )}
        </div>
        <div className="text-sm whitespace-pre-wrap break-words">{message.content}</div>
        {message.timestamp && (
          <div className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
            {new Date(message.timestamp).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  )
}
