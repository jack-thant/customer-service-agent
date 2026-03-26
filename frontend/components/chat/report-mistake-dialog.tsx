'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Spinner } from '@/components/ui/spinner';
import { AlertTriangle, MessageSquare, Bot } from 'lucide-react';
import type { ChatMessage } from '@/lib/types';

interface ReportMistakeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  message: ChatMessage | null;
  userQuery: string;
  onSubmit: (feedback: string) => Promise<void>;
}

export function ReportMistakeDialog({
  open,
  onOpenChange,
  message,
  userQuery,
  onSubmit,
}: ReportMistakeDialogProps) {
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!feedback.trim()) return;
    
    setIsSubmitting(true);
    try {
      await onSubmit(feedback.trim());
      setFeedback('');
      onOpenChange(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg border-none bg-surface-container-lowest shadow-[0_20px_40px_rgba(0,52,94,0.06)]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-destructive/10">
              <AlertTriangle className="size-5 text-destructive" />
            </div>
            <div>
              <DialogTitle className="font-display text-lg">
                Report a Mistake
              </DialogTitle>
              <DialogDescription>
                Help improve the AI by reporting incorrect responses
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* User Query */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <MessageSquare className="size-3.5" />
              Your Question
            </div>
            <div className="rounded-xl bg-surface-container p-4 text-sm text-foreground">
              {userQuery || 'N/A'}
            </div>
          </div>

          {/* Bot Response */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Bot className="size-3.5" />
              Bot Response
            </div>
            <div className="max-h-32 overflow-y-auto rounded-xl bg-surface-container p-4 text-sm text-foreground">
              {message?.content || 'N/A'}
            </div>
          </div>

          {/* Feedback */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              What was wrong with this response?
            </label>
            <Textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Describe the issue: incorrect information, missing details, confusing explanation, etc."
              className="min-h-24 resize-none border-none bg-surface-container focus:bg-surface-container-low"
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!feedback.trim() || isSubmitting}
            className="bg-gradient-to-br from-destructive to-destructive/80"
          >
            {isSubmitting ? (
              <>
                <Spinner className="size-4" />
                Submitting...
              </>
            ) : (
              'Submit Report'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
