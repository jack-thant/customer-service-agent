'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/app-shell';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Spinner } from '@/components/ui/spinner';
import { getConfig, updateConfig, reingestKnowledgeBase } from '@/lib/api';
import type { BotConfig } from '@/lib/types';
import { toast } from 'sonner';
import {
  Database,
  RefreshCw,
  Save,
  Globe,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

export default function ConfigPage() {
  const [config, setConfig] = useState<BotConfig | null>(null);
  const [kbUrl, setKbUrl] = useState('');
  const [guidelines, setGuidelines] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isReingesting, setIsReingesting] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Fetch current config
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await getConfig();
        setConfig(data);
        setKbUrl(data.kb_url);
        setGuidelines(data.additional_guidelines);
      } catch (error) {
        toast.error('Failed to load configuration');
      } finally {
        setIsLoading(false);
      }
    };

    fetchConfig();
  }, []);

  // Track changes
  useEffect(() => {
    if (config) {
      const changed = kbUrl !== config.kb_url || guidelines !== config.additional_guidelines;
      setHasChanges(changed);
    }
  }, [kbUrl, guidelines, config]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updatedConfig = await updateConfig({
        kb_url: kbUrl,
        additional_guidelines: guidelines,
      });
      setConfig(updatedConfig);
      toast.success('Configuration saved');
    } catch (error) {
      toast.error('Failed to save configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReingest = async (force = false) => {
    setIsReingesting(true);
    try {
      const result = await reingestKnowledgeBase(force);
      toast.success('Knowledge base updated');
    } catch (error) {
      toast.error('Re-ingestion failed');
    } finally {
      setIsReingesting(false);
    }
  };

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex h-screen items-center justify-center">
          <Spinner className="size-8 text-primary" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="min-h-screen bg-surface">
        {/* Header */}
        <header className="border-b border-surface-container-high bg-surface-container-lowest px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-foreground sm:text-2xl">
                  Bot Configuration
                </h1>
                {config?.updated_at && (
                  <span className="inline-flex items-center gap-1.5 rounded-md bg-surface-container-high px-2 py-1 text-xs font-medium text-muted-foreground">
                    <Clock className="size-3" />
                    Updated {new Date(config.updated_at).toLocaleDateString()}
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm text-muted-foreground sm:text-base">
                Manage knowledge base and AI guidelines
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <Button
                variant="outline"
                onClick={() => handleReingest(true)}
                disabled={isReingesting || kbUrl !== config?.kb_url}
                className="w-full gap-2 border-surface-container-high hover:bg-surface-container sm:w-auto"
                title={kbUrl !== config?.kb_url ? "Save changes before re-ingesting" : "Sync Knowledge Base"}
              >
                {isReingesting ? (
                  <>
                    <Spinner className="size-4" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="size-4" />
                    Sync Knowledge Base
                  </>
                )}
              </Button>
              <Button
                onClick={handleSave}
                disabled={!hasChanges || isSaving}
                className="w-full gap-2 bg-linear-to-br from-primary to-primary-dim sm:w-auto"
              >
                {isSaving ? (
                  <>
                    <Spinner className="size-4" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="size-4" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-4xl space-y-6 sm:space-y-8">
            {/* Knowledge Base URL */}
            <section className="rounded-2xl bg-surface-container-lowest p-4 sm:p-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-surface-container sm:size-12">
                  <Globe className="size-5 text-primary sm:size-6" />
                </div>
                <div className="flex-1">
                  <h2 className="font-display text-base font-semibold text-foreground sm:text-lg">
                    Knowledge Base URL
                  </h2>
                  <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
                    The URL where your help articles or documentation are hosted
                  </p>
                  <div className="mt-4">
                    <input
                      type="url"
                      value={kbUrl}
                      onChange={(e) => setKbUrl(e.target.value)}
                      placeholder="https://help.example.com/categories/123"
                      className="w-full rounded-xl bg-surface-container-low px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:bg-surface-container focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* Additional Guidelines */}
            <section className="rounded-2xl bg-surface-container-lowest p-4 sm:p-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-surface-container sm:size-12">
                  <FileText className="size-5 text-primary sm:size-6" />
                </div>
                <div className="flex-1">
                  <h2 className="font-display text-base font-semibold text-foreground sm:text-lg">
                    Additional Guidelines
                  </h2>
                  <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
                    Custom instructions for the AI to follow when responding to customers
                  </p>
                  <div className="mt-4">
                    <Textarea
                      value={guidelines}
                      onChange={(e) => setGuidelines(e.target.value)}
                      placeholder="Enter any additional instructions or guidelines for the AI assistant..."
                      className="min-h-36 resize-none border-none bg-surface-container-low focus:bg-surface-container sm:min-h-48"
                    />
                    <p className="mt-2 text-xs text-muted-foreground">
                      {guidelines.length} / 10,000 characters
                    </p>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
