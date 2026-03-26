'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { ReportMistakeDialog } from './report-mistake-dialog';
import { sendChatMessage, createMistake } from '@/lib/api';
import type { ChatMessage as ChatMessageType } from '@/lib/types';
import { toast } from 'sonner';
import { MessageSquare, Sparkles } from 'lucide-react';

// Generate unique session ID
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

export function ChatContainer() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const [followupField, setFollowupField] = useState<string | null>(null);
  const [mistakeDialog, setMistakeDialog] = useState<{
    open: boolean;
    message: ChatMessageType | null;
    userQuery: string;
  }>({ open: false, message: null, userQuery: '' });
  
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async (content: string) => {
    // Add user message
    const userMessage: ChatMessageType = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        session_id: sessionId,
        message: content,
      });

      // Add assistant message
      const assistantMessage: ChatMessageType = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        route: response.route,
        requires_followup: response.requires_followup,
        followup_field: response.followup_field,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      
      // Update followup state
      setFollowupField(response.requires_followup ? response.followup_field : null);
    } catch (error) {
      toast.error('Failed to send message', {
        description: error instanceof Error ? error.message : 'Please try again',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReportMistake = (message: ChatMessageType) => {
    // Find the user message that preceded this assistant message
    const messageIndex = messages.findIndex((m) => m.id === message.id);
    const userQuery = messageIndex > 0 ? messages[messageIndex - 1].content : '';
    
    setMistakeDialog({
      open: true,
      message,
      userQuery,
    });
  };

  const handleSubmitMistake = async (feedback: string) => {
    if (!mistakeDialog.message) return;

    try {
      await createMistake({
        user_query: mistakeDialog.userQuery,
        bot_answer: mistakeDialog.message.content,
        feedback,
        route: mistakeDialog.message.route,
        session_id: sessionId,
      });

      toast.success('Mistake reported! Thank you for your feedback');
    } catch (error) {
      toast.error('Failed to submit report, Please try again');
      throw error;
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Messages Area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8"
      >
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center">
            <div className="flex size-20 items-center justify-center rounded-2xl bg-surface-container-low">
              <Sparkles className="size-10 text-primary" />
            </div>
            <h2 className="mt-6 font-display text-2xl font-bold text-foreground">
              How can I help you today?
            </h2>
            <p className="mt-2 max-w-md text-center text-muted-foreground">
              Ask me about your card application status, transaction inquiries, or any other support questions.
            </p>
            
            {/* Quick Actions */}
            <div className="mt-8 grid w-full max-w-md grid-cols-1 gap-3 px-4 sm:grid-cols-2 sm:gap-4 sm:px-0">
              {[
                { label: 'Check application status', query: 'What is the status of my card application?' },
                { label: 'Transaction inquiry', query: 'I have a question about a failed transaction' },
              ].map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleSend(action.query)}
                  className="flex items-center gap-3 rounded-xl bg-surface-container-lowest p-4 text-left transition-all hover:bg-surface-container-low"
                >
                  <MessageSquare className="size-5 shrink-0 text-primary" />
                  <span className="text-sm font-medium text-foreground">{action.label}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onReportMistake={message.role === 'assistant' ? handleReportMistake : undefined}
              />
            ))}
            
            {isLoading && (
              <div className="flex gap-4">
                <div className="flex size-10 items-center justify-center rounded-xl bg-surface-container-highest">
                  <div className="flex gap-1">
                    <span className="size-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                    <span className="size-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                    <span className="size-2 animate-bounce rounded-full bg-muted-foreground" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-surface-container-high bg-surface-container-lowest px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            followupField={followupField}
          />
        </div>
      </div>

      {/* Report Mistake Dialog */}
      <ReportMistakeDialog
        open={mistakeDialog.open}
        onOpenChange={(open) => setMistakeDialog((prev) => ({ ...prev, open }))}
        message={mistakeDialog.message}
        userQuery={mistakeDialog.userQuery}
        onSubmit={handleSubmitMistake}
      />
    </div>
  );
}
