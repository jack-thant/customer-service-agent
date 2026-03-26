'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  followupField?: string | null;
}

export function ChatInput({ onSend, isLoading, placeholder, followupField }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [input]);

  // Determine placeholder text
  const placeholderText = followupField
    ? `Please provide your ${followupField} (e.g., TX123)...`
    : placeholder || 'Type your message...';

  return (
    <form onSubmit={handleSubmit} className='w-full'>
      <div
        className={cn(
          'flex items-center gap-2 rounded-2xl bg-surface-container-low p-2 transition-all duration-200 sm:gap-3 sm:p-3',
          'focus-within:bg-surface-container-lowest focus-within:ring-2 focus-within:ring-primary/20'
        )}
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholderText}
          disabled={isLoading}
          rows={1}
          className={cn(
            'flex-1 resize-none self-center bg-transparent py-2 h-full text-sm leading-relaxed text-foreground',
            'placeholder:text-muted-foreground',
            'focus:outline-none',
            'disabled:opacity-50'
          )}
        />
        <Button
          type="submit"
          size="icon"
          disabled={!input.trim() || isLoading}
          className={cn(
            'size-9 shrink-0 rounded-xl sm:size-10',
            'bg-gradient-to-br from-primary to-primary-dim',
            'hover:from-primary/90 hover:to-primary-dim/90',
            'disabled:opacity-50'
          )}
        >
          {isLoading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Send className="size-4" />
          )}
        </Button>
      </div>

      {/* Followup hint */}
      {followupField && (
        <p className="mt-2 text-center text-xs text-muted-foreground">
          The bot is waiting for your <span className="font-medium text-foreground">{followupField}</span>
        </p>
      )}
    </form>
  );
}
