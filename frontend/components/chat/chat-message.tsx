'use client';

import { cn } from '@/lib/utils';
import type { ChatMessage as ChatMessageType } from '@/lib/types';
import { Bot, User, ExternalLink, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ChatMessageProps {
  message: ChatMessageType;
  onReportMistake?: (message: ChatMessageType) => void;
}

export function ChatMessage({ message, onReportMistake }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex gap-3 sm:gap-4',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex size-8 shrink-0 items-center justify-center rounded-xl sm:size-10',
          isUser
            ? 'bg-gradient-to-br from-primary to-primary-dim'
            : 'bg-surface-container-highest'
        )}
      >
        {isUser ? (
          <User className="size-4 text-primary-foreground sm:size-5" />
        ) : (
          <Bot className="size-4 text-foreground sm:size-5" />
        )}
      </div>

      {/* Message Content */}
      <div
        className={cn(
          'group relative max-w-[85%] space-y-2 sm:max-w-[75%] sm:space-y-3',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'rounded-xl px-4 py-3 sm:px-5 sm:py-4',
            isUser
              ? 'rounded-br-sm bg-gradient-to-br from-primary to-primary-dim text-primary-foreground'
              : 'rounded-bl-sm bg-surface-container-highest text-foreground'
          )}
        >
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </p>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Sources</p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, index) => (
                <a
                  key={index}
                  href={source.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-surface-container px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-surface-container-high hover:text-foreground"
                >
                  <ExternalLink className="size-3" />
                  {source.title || 'Source'}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Followup indicator */}
        {message.requires_followup && message.followup_field && (
          <div className="flex items-center gap-2 rounded-lg bg-info/10 px-3 py-2 text-xs text-info">
            <AlertCircle className="size-3.5" />
            <span>Please provide: {message.followup_field}</span>
          </div>
        )}

        {/* Report mistake button (only for assistant messages) */}
        {!isUser && onReportMistake && (
          <div className="opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-destructive"
              onClick={() => onReportMistake(message)}
            >
              <AlertCircle className="size-3" />
              Report Mistake
            </Button>
          </div>
        )}

        {/* Timestamp */}
        <p className="text-xs text-muted-foreground">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}
