'use client';

import { useState, useEffect, useCallback } from 'react';
import { AppShell } from '@/components/app-shell';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Spinner } from '@/components/ui/spinner';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { getMistakes, updateMistakeStatus } from '@/lib/api';
import type { Mistake, MistakeStatus } from '@/lib/types';
import { toast } from 'sonner';
import {
  AlertTriangle,
  CheckCircle2,
  Archive,
  RefreshCw,
  MessageSquare,
  Bot,
  Clock,
  ChevronDown,
  ChevronUp,
  Wrench,
  Sparkles,
} from 'lucide-react';

const STATUS_CONFIG: Record<MistakeStatus, { label: string; color: string; icon: React.ElementType }> = {
  open: { label: 'Open', color: 'bg-warning/10 text-warning', icon: AlertTriangle },
  patched: { label: 'Patched', color: 'bg-info/10 text-info', icon: Wrench },
  fixed: { label: 'Fixed', color: 'bg-success/10 text-success', icon: CheckCircle2 },
  archived: { label: 'Archived', color: 'bg-muted text-muted-foreground', icon: Archive },
};

interface MistakeCardProps {
  mistake: Mistake;
  onStatusChange: (id: number, status: MistakeStatus) => Promise<void>;
}

function MistakeCard({ mistake, onStatusChange }: MistakeCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const statusConfig = STATUS_CONFIG[mistake.status];
  const StatusIcon = statusConfig.icon;

  const handleStatusChange = async (newStatus: MistakeStatus) => {
    setIsUpdating(true);
    try {
      await onStatusChange(mistake.id, newStatus);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="rounded-2xl bg-surface-container-lowest p-4 transition-all sm:p-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 sm:gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <Badge className={statusConfig.color}>
              <StatusIcon className="mr-1 size-3" />
              {statusConfig.label}
            </Badge>
            {mistake.route && (
              <Badge variant="outline" className="border-surface-container-high">
                {mistake.route}
              </Badge>
            )}
            <span className="text-xs text-muted-foreground">
              #{mistake.id}
            </span>
          </div>
          
          {/* User Query Preview */}
          <p className="mt-3 line-clamp-2 text-sm font-medium text-foreground">
            {mistake.user_query}
          </p>
          
          {/* Feedback Preview */}
          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
            {mistake.feedback}
          </p>
        </div>

        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="shrink-0"
        >
          {isExpanded ? (
            <ChevronUp className="size-4" />
          ) : (
            <ChevronDown className="size-4" />
          )}
        </Button>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-4 space-y-4 border-t border-surface-container-high pt-4 sm:mt-6 sm:pt-6">
          {/* User Query */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <MessageSquare className="size-3.5" />
              User Query
            </div>
            <div className="rounded-xl bg-surface-container p-3 text-sm text-foreground sm:p-4">
              {mistake.user_query}
            </div>
          </div>

          {/* Bot Answer */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Bot className="size-3.5" />
              Bot Answer
            </div>
            <div className="rounded-xl bg-surface-container p-3 text-sm text-foreground sm:p-4">
              {mistake.bot_answer}
            </div>
          </div>

          {/* Customer Feedback */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-destructive">
              <AlertTriangle className="size-3.5" />
              Customer Feedback
            </div>
            <div className="rounded-xl bg-destructive/5 p-3 text-sm text-foreground sm:p-4">
              {mistake.feedback}
            </div>
          </div>

          {/* Root Cause & Suggested Fix (if available) */}
          {(mistake.root_cause || mistake.suggested_fix) && (
            <div className="grid gap-3 sm:grid-cols-2 sm:gap-4">
              {mistake.root_cause && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-info">
                    <Sparkles className="size-3.5" />
                    Root Cause Analysis
                  </div>
                  <div className="rounded-xl bg-info/5 p-3 text-sm text-foreground sm:p-4">
                    {mistake.root_cause}
                  </div>
                </div>
              )}
              {mistake.suggested_fix && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-success">
                    <Wrench className="size-3.5" />
                    Suggested Fix
                  </div>
                  <div className="rounded-xl bg-success/5 p-3 text-sm text-foreground sm:p-4">
                    {mistake.suggested_fix}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Applied Fix & Rerun Answer */}
          {(mistake.applied_fix || mistake.rerun_answer) && (
            <div className="grid gap-3 sm:grid-cols-2 sm:gap-4">
              {mistake.applied_fix && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-success">
                    <CheckCircle2 className="size-3.5" />
                    Applied Fix
                  </div>
                  <div className="rounded-xl bg-success/5 p-3 text-sm text-foreground sm:p-4">
                    {mistake.applied_fix}
                  </div>
                </div>
              )}
              {mistake.rerun_answer && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-primary">
                    <RefreshCw className="size-3.5" />
                    Rerun Answer
                  </div>
                  <div className="rounded-xl bg-primary/5 p-3 text-sm text-foreground sm:p-4">
                    {mistake.rerun_answer}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Timestamps */}
          <div className="flex flex-col gap-2 text-xs text-muted-foreground sm:flex-row sm:items-center sm:gap-4">
            <div className="flex items-center gap-1">
              <Clock className="size-3.5" />
              Created: {new Date(mistake.created_at).toLocaleString()}
            </div>
            <div className="flex items-center gap-1">
              <RefreshCw className="size-3.5" />
              Updated: {new Date(mistake.updated_at).toLocaleString()}
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-2 border-t border-surface-container-high pt-4 sm:gap-3">
            {mistake.status === 'open' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleStatusChange('fixed')}
                disabled={isUpdating}
                className="flex-1 gap-2 border-surface-container-high bg-surface-container hover:bg-surface-container-high sm:flex-none"
              >
                {isUpdating ? <Spinner className="size-4" /> : <CheckCircle2 className="size-4" />}
                Mark as Fixed
              </Button>
            )}
            {mistake.status === 'patched' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleStatusChange('fixed')}
                disabled={isUpdating}
                className="flex-1 gap-2 border-surface-container-high bg-surface-container hover:bg-surface-container-high sm:flex-none"
              >
                {isUpdating ? <Spinner className="size-4" /> : <CheckCircle2 className="size-4" />}
                Confirm Fix
              </Button>
            )}
            {(mistake.status === 'fixed' || mistake.status === 'patched') && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleStatusChange('archived')}
                disabled={isUpdating}
                className="flex-1 gap-2 border-surface-container-high bg-surface-container hover:bg-surface-container-high sm:flex-none"
              >
                {isUpdating ? <Spinner className="size-4" /> : <Archive className="size-4" />}
                Archive
              </Button>
            )}
            {mistake.status === 'archived' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleStatusChange('open')}
                disabled={isUpdating}
                className="flex-1 gap-2 border-surface-container-high bg-surface-container hover:bg-surface-container-high sm:flex-none"
              >
                {isUpdating ? <Spinner className="size-4" /> : <RefreshCw className="size-4" />}
                Reopen
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function MistakesPage() {
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('all');

  const fetchMistakes = useCallback(async (status?: MistakeStatus) => {
    setIsLoading(true);
    try {
      const data = await getMistakes(status);
      setMistakes(data);
    } catch (error) {
      toast.error('Failed to load mistakes');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const status = activeTab === 'all' ? undefined : (activeTab as MistakeStatus);
    fetchMistakes(status);
  }, [activeTab, fetchMistakes]);

  const handleStatusChange = async (id: number, newStatus: MistakeStatus) => {
    try {
      const updated = await updateMistakeStatus(id, { status: newStatus });
      setMistakes((prev) =>
        prev.map((m) => (m.id === id ? updated : m))
      );
      toast.success('Status updated');
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  // Filter mistakes based on active tab
  const filteredMistakes = activeTab === 'all'
    ? mistakes
    : mistakes.filter((m) => m.status === activeTab);

  // Count by status
  const statusCounts = {
    all: mistakes.length,
    open: mistakes.filter((m) => m.status === 'open').length,
    patched: mistakes.filter((m) => m.status === 'patched').length,
    fixed: mistakes.filter((m) => m.status === 'fixed').length,
    archived: mistakes.filter((m) => m.status === 'archived').length,
  };

  return (
    <AppShell>
      <div className="min-h-screen bg-surface">
        {/* Header */}
        <header className="border-b border-surface-container-high bg-surface-container-lowest px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="font-display text-xl font-bold text-foreground sm:text-2xl">
                Mistake Reports
              </h1>
              <p className="mt-1 text-sm text-muted-foreground sm:text-base">
                Review and manage AI response issues
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => fetchMistakes(activeTab === 'all' ? undefined : (activeTab as MistakeStatus))}
              disabled={isLoading}
              className="w-full gap-2 border-surface-container-high bg-surface-container hover:bg-surface-container-high sm:w-auto"
            >
              {isLoading ? <Spinner className="size-4" /> : <RefreshCw className="size-4" />}
              Refresh
            </Button>
          </div>

          {/* Stats */}
          <div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3 lg:grid-cols-5 lg:gap-4">
            {[
              { key: 'all', label: 'Total', icon: MessageSquare },
              { key: 'open', label: 'Open', icon: AlertTriangle },
              { key: 'patched', label: 'Patched', icon: Wrench },
              { key: 'fixed', label: 'Fixed', icon: CheckCircle2 },
              { key: 'archived', label: 'Archived', icon: Archive },
            ].map((item) => {
              const Icon = item.icon;
              const count = statusCounts[item.key as keyof typeof statusCounts];
              return (
                <div
                  key={item.key}
                  className="rounded-xl bg-surface-container p-3 sm:p-4"
                >
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Icon className="size-4" />
                    <span className="text-xs font-medium">{item.label}</span>
                  </div>
                  <p className="mt-1 font-display text-xl font-bold text-foreground sm:mt-2 sm:text-2xl">
                    {count}
                  </p>
                </div>
              );
            })}
          </div>
        </header>

        {/* Content */}
        <div className="p-4 sm:p-6 lg:p-8">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-6 flex w-full flex-wrap bg-surface-container-low sm:w-auto">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="open">Open</TabsTrigger>
              <TabsTrigger value="patched">Patched</TabsTrigger>
              <TabsTrigger value="fixed">Fixed</TabsTrigger>
              <TabsTrigger value="archived">Archived</TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab}>
              {isLoading ? (
                <div className="flex items-center justify-center py-20">
                  <Spinner className="size-8 text-primary" />
                </div>
              ) : filteredMistakes.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-2xl bg-surface-container-lowest py-20">
                  <div className="flex size-16 items-center justify-center rounded-2xl bg-surface-container">
                    <CheckCircle2 className="size-8 text-success" />
                  </div>
                  <h3 className="mt-4 font-display text-lg font-semibold text-foreground">
                    No mistakes found
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {activeTab === 'all'
                      ? 'No mistake reports have been submitted yet'
                      : `No ${activeTab} mistakes at the moment`}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredMistakes.map((mistake) => (
                    <MistakeCard
                      key={mistake.id}
                      mistake={mistake}
                      onStatusChange={handleStatusChange}
                    />
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </AppShell>
  );
}
