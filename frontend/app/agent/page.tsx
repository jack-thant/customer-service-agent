'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { AppShell } from '@/components/app-shell';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Spinner } from '@/components/ui/spinner';
import { toast } from 'sonner';
import {
  Upload,
  FileText,
  Send,
  Bot,
  Cpu,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Sparkles,
  AlertCircle,
  MessageSquare,
  User,
  Trash2,
} from 'lucide-react';
import {
  uploadAgentDocument,
  buildAgent,
  getBuildJobStatus,
  sendMetaChat,
  getActiveSpec,
  sendAgentChatMessage,
  createAgentMistake,
} from '@/lib/api';
import type {
  AgentDocument,
  BuildJobStatusResponse,
  AgentSpec,
  AgentChatMessage,
} from '@/lib/types';
import { cn } from '@/lib/utils';

// Generate stable session ID
function generateSessionId(): string {
  return `agent_session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

export default function AgentPage() {
  const [activeTab, setActiveTab] = useState('setup');
  
  // Document Upload State
  const [documents, setDocuments] = useState<AgentDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Meta Chat State
  const [metaChatInput, setMetaChatInput] = useState('');
  const [currentInstructions, setCurrentInstructions] = useState('');
  const [proposedInstructions, setProposedInstructions] = useState('');
  const [isMetaChatLoading, setIsMetaChatLoading] = useState(false);

  // Build State
  const [instructionGoal, setInstructionGoal] = useState('');
  const [selectedDocIds, setSelectedDocIds] = useState<number[]>([]);
  const [buildJob, setBuildJob] = useState<BuildJobStatusResponse | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Active Spec State
  const [activeSpec, setActiveSpec] = useState<AgentSpec | null>(null);
  const [isLoadingSpec, setIsLoadingSpec] = useState(true);

  // Agent Chat State
  const [sessionId] = useState(() => generateSessionId());
  const [chatMessages, setChatMessages] = useState<AgentChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [currentSpecVersion, setCurrentSpecVersion] = useState<number | null>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Report Mistake State
  const [reportingMessageId, setReportingMessageId] = useState<string | null>(null);
  const [feedbackInput, setFeedbackInput] = useState('');

  // Fetch active spec on mount
  useEffect(() => {
    fetchActiveSpec();
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const fetchActiveSpec = async () => {
    setIsLoadingSpec(true);
    try {
      const spec = await getActiveSpec();
      setActiveSpec(spec);
      setCurrentInstructions(spec.instruction_text);
      setCurrentSpecVersion(spec.version);
    } catch {
      // 404 means no active spec, which is okay
      setActiveSpec(null);
    } finally {
      setIsLoadingSpec(false);
    }
  };

  // Document Upload
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const allowedExtensions = ['.txt', '.md', '.html', '.htm'];
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!allowedExtensions.includes(fileExt)) {
      toast.error('Unsupported file type. Please use .txt, .md, .html, or .htm files.');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 5MB.');
      return;
    }

    setIsUploading(true);
    try {
      const doc = await uploadAgentDocument(file);
      setDocuments((prev) => [...prev, doc]);
      setSelectedDocIds((prev) => [...prev, doc.id]);
      toast.success(`Uploaded: ${doc.original_filename}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const removeDocument = (docId: number) => {
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
    setSelectedDocIds((prev) => prev.filter((id) => id !== docId));
  };

  // Meta Chat
  const handleMetaChat = async () => {
    if (!metaChatInput.trim()) return;

    setIsMetaChatLoading(true);
    try {
      const response = await sendMetaChat({
        message: metaChatInput,
        current_instructions: currentInstructions,
      });
      setProposedInstructions(response.proposed_instructions);
      toast.success('Instructions refined');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Meta chat failed');
    } finally {
      setIsMetaChatLoading(false);
      setMetaChatInput('');
    }
  };

  const acceptProposedInstructions = () => {
    setCurrentInstructions(proposedInstructions);
    setInstructionGoal(proposedInstructions);
    setProposedInstructions('');
    toast.success('Instructions accepted');
  };

  // Build Agent
  const handleBuildAgent = async () => {
    if (!instructionGoal.trim()) {
      toast.error('Please provide instruction goal');
      return;
    }

    if (selectedDocIds.length === 0) {
      toast.error('Please upload and select at least one document');
      return;
    }

    setIsBuilding(true);
    try {
      const response = await buildAgent({
        instruction_goal: instructionGoal,
        document_ids: selectedDocIds,
      });

      toast.success(`Build started - Job #${response.job_id}`);

      // Start polling
      pollBuildStatus(response.job_id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Build failed');
      setIsBuilding(false);
    }
  };

  const pollBuildStatus = useCallback((jobId: number) => {
    const poll = async () => {
      try {
        const status = await getBuildJobStatus(jobId);
        setBuildJob(status);

        if (status.status === 'completed') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setIsBuilding(false);
          toast.success('Agent build completed!');
          fetchActiveSpec();
        } else if (status.status === 'failed') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setIsBuilding(false);
          toast.error(`Build failed: ${status.error_summary || 'Unknown error'}`);
        }
      } catch (err) {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsBuilding(false);
        toast.error('Failed to check build status');
      }
    };

    // Initial check
    poll();

    // Poll every 2 seconds
    pollIntervalRef.current = setInterval(poll, 2000);
  }, []);

  // Agent Chat
  const handleChatSend = async () => {
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage: AgentChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: chatInput,
      timestamp: new Date(),
    };

    setChatMessages((prev) => [...prev, userMessage]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const response = await sendAgentChatMessage({
        session_id: sessionId,
        message: userMessage.content,
      });

      const assistantMessage: AgentChatMessage = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        route: response.route,
        requires_followup: response.requires_followup,
        followup_field: response.followup_field,
        agent_spec_version: response.agent_spec_version,
      };

      setChatMessages((prev) => [...prev, assistantMessage]);
      setCurrentSpecVersion(response.agent_spec_version);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Chat failed');
    } finally {
      setIsChatLoading(false);
    }
  };

  // Report Mistake
  const handleReportMistake = async (message: AgentChatMessage) => {
    if (!feedbackInput.trim()) {
      toast.error('Please provide feedback');
      return;
    }

    // Find the preceding user message
    const msgIndex = chatMessages.findIndex((m) => m.id === message.id);
    const userQuery = msgIndex > 0 ? chatMessages[msgIndex - 1].content : '';

    try {
      await createAgentMistake({
        user_query: userQuery,
        bot_answer: message.content,
        feedback: feedbackInput,
        route: message.route || null,
        session_id: sessionId,
        runtime: 'part2',
        agent_spec_version: message.agent_spec_version || currentSpecVersion || 1,
      });

      toast.success('Mistake reported');
      setReportingMessageId(null);
      setFeedbackInput('');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to report mistake');
    }
  };

  return (
    <AppShell>
      <div className="flex h-full flex-col">
        {/* Header */}
        <header className="border-b border-surface-container-high bg-surface-container-lowest px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="font-[var(--font-manrope)] text-xl font-bold text-foreground sm:text-2xl">
                Agent Studio
              </h1>
              <p className="mt-1 text-sm text-muted-foreground sm:text-base">
                Build and configure your generated AI agent
              </p>
            </div>
            {activeSpec && (
              <div className="flex items-center gap-2">
                <Badge className="bg-success/10 text-success">
                  <CheckCircle2 className="mr-1 size-3" />
                  v{activeSpec.version} Active
                </Badge>
              </div>
            )}
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex h-full flex-col">
            <div className="border-b px-4 sm:px-6 lg:px-8">
              <TabsList className="h-12 w-full justify-start gap-4 bg-transparent p-0">
                <TabsTrigger
                  value="setup"
                  className="data-[state=active]:bg-transparent data-[state=active]:border-b-primary data-[state=active]:text-primary font-bold data-[state=active]:shadow-none rounded-none border-b-2 border-transparent pb-3"
                >
                  <Cpu className="mr-2 size-4" />
                  Setup
                </TabsTrigger>
                <TabsTrigger
                  value="chat"
                  className="data-[state=active]:bg-transparent data-[state=active]:border-b-primary data-[state=active]:text-primary font-bold data-[state=active]:shadow-none rounded-none border-b-2 border-transparent pb-3"
                >
                  <MessageSquare className="mr-2 size-4" />
                  Chat
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Setup Tab */}
            <TabsContent value="setup" className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 mt-0">
              <div className="mx-auto max-w-5xl grid grid-cols-1 gap-4 md:grid-cols-2">
                {/* Section A: Document Upload */}
                <section className="rounded-2xl bg-surface-container-lowest p-4 sm:p-6">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-surface-container sm:size-12">
                      <Upload className="size-5 text-primary sm:size-6" />
                    </div>
                    <div className="flex-1">
                      <h2 className="text-base font-semibold text-foreground sm:text-lg">
                        Document Upload
                      </h2>
                      <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
                        Upload documents (.txt, .md, .html) to train your agent. Max 5MB per file.
                      </p>

                      <div className="mt-4">
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".txt,.md,.html,.htm"
                          onChange={handleFileSelect}
                          className="hidden"
                        />
                        <Button
                          variant="outline"
                          onClick={() => fileInputRef.current?.click()}
                          disabled={isUploading}
                          className="w-full gap-2 border-dashed border-surface-container-high bg-surface-container hover:bg-surface-container-high sm:w-auto"
                        >
                          {isUploading ? (
                            <>
                              <Spinner className="size-4" />
                              Uploading...
                            </>
                          ) : (
                            <>
                              <Upload className="size-4" />
                              Select File
                            </>
                          )}
                        </Button>
                      </div>

                      {/* Document List */}
                      {documents.length > 0 && (
                        <div className="mt-4 space-y-2">
                          {documents.map((doc) => (
                            <div
                              key={doc.id}
                              className="flex items-center justify-between rounded-xl bg-surface-container p-3"
                            >
                              <div className="flex items-center gap-3">
                                <FileText className="size-4 text-muted-foreground" />
                                <div>
                                  <p className="text-sm font-medium text-foreground">
                                    {doc.original_filename}
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    {(doc.size_bytes / 1024).toFixed(1)} KB · ID: {doc.id}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <Badge
                                  className={cn(
                                    doc.status === 'uploaded' && 'bg-success/10 text-success',
                                    doc.status === 'processing' && 'bg-warning/10 text-warning',
                                    doc.status === 'error' && 'bg-destructive/10 text-destructive'
                                  )}
                                >
                                  {doc.status}
                                </Badge>
                                <Button
                                  variant="ghost"
                                  size="icon-sm"
                                  onClick={() => removeDocument(doc.id)}
                                >
                                  <Trash2 className="size-4 text-muted-foreground hover:text-destructive" />
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </section>

                {/* Section B: Meta Chat */}
                <section className="rounded-2xl bg-surface-container-lowest p-4 sm:p-6 row-span-2">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-dim sm:size-12">
                      <Sparkles className="size-5 text-primary-foreground sm:size-6" />
                    </div>
                    <div className="flex-1">
                      <h2 className="font-[var(--font-manrope)] text-base font-semibold text-foreground sm:text-lg">
                        Meta Chat - Instruction Refinement
                      </h2>
                      <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
                        Chat with the meta-agent to refine your agent&apos;s instructions
                      </p>

                      {/* Current Instructions */}
                      <div className="mt-4">
                        <label className="text-xs font-medium text-muted-foreground">
                          Current Instructions
                        </label>
                        <Textarea
                          value={currentInstructions}
                          onChange={(e) => setCurrentInstructions(e.target.value)}
                          placeholder="Your agent's current instructions..."
                          className="mt-2 min-h-24 resize-none border-none bg-surface-container-low focus:bg-surface-container"
                        />
                      </div>

                      {/* Meta Chat Input */}
                      <div className="mt-4">
                        <label className="text-xs font-medium text-muted-foreground">
                          Ask Meta-Agent for Refinements
                        </label>
                        <div className="mt-2 flex gap-2">
                          <Textarea
                            value={metaChatInput}
                            onChange={(e) => setMetaChatInput(e.target.value)}
                            placeholder="e.g., Make answers shorter and include eligibility caveats..."
                            className="min-h-12 resize-none border-none bg-surface-container-low focus:bg-surface-container"
                          />
                          <Button
                            onClick={handleMetaChat}
                            disabled={!metaChatInput.trim() || isMetaChatLoading}
                            className="shrink-0 gap-2 bg-gradient-to-br from-primary to-primary-dim"
                          >
                            {isMetaChatLoading ? (
                              <Spinner className="size-4" />
                            ) : (
                              <Send className="size-4" />
                            )}
                          </Button>
                        </div>
                      </div>

                      {/* Proposed Instructions */}
                      {proposedInstructions && (
                        <div className="mt-4 rounded-xl bg-primary/5 p-4">
                          <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-primary">Proposed Instructions</p>
                            <Button
                              size="sm"
                              onClick={acceptProposedInstructions}
                              className="gap-1 bg-primary"
                            >
                              <CheckCircle2 className="size-3" />
                              Accept
                            </Button>
                          </div>
                          <p className="mt-2 text-sm text-foreground whitespace-pre-wrap">
                            {proposedInstructions}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </section>

                {/* Section C: Build Agent */}
                <section className="rounded-2xl bg-surface-container-lowest p-4 sm:p-6">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-surface-container sm:size-12">
                      <Play className="size-5 text-primary sm:size-6" />
                    </div>
                    <div className="flex-1">
                      <h2 className="font-[var(--font-manrope)] text-base font-semibold text-foreground sm:text-lg">
                        Build Agent
                      </h2>
                      <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
                        Compile your documents and instructions into a new agent version
                      </p>

                      {/* Instruction Goal */}
                      <div className="mt-4">
                        <label className="text-xs font-medium text-muted-foreground">
                          Instruction Goal
                        </label>
                        <Textarea
                          value={instructionGoal}
                          onChange={(e) => setInstructionGoal(e.target.value)}
                          placeholder="Describe how the agent should behave..."
                          className="mt-2 min-h-20 resize-none border-none bg-surface-container-low focus:bg-surface-container"
                        />
                      </div>

                      {/* Selected Documents */}
                      <div className="mt-4">
                        <label className="text-xs font-medium text-muted-foreground">
                          Selected Documents ({selectedDocIds.length})
                        </label>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {documents.map((doc) => (
                            <Badge
                              key={doc.id}
                              variant={selectedDocIds.includes(doc.id) ? 'default' : 'outline'}
                              className={cn(
                                'cursor-pointer transition-all',
                                selectedDocIds.includes(doc.id)
                                  ? 'bg-primary text-primary-foreground'
                                  : 'hover:bg-surface-container-high'
                              )}
                              onClick={() => {
                                if (selectedDocIds.includes(doc.id)) {
                                  setSelectedDocIds((prev) => prev.filter((id) => id !== doc.id));
                                } else {
                                  setSelectedDocIds((prev) => [...prev, doc.id]);
                                }
                              }}
                            >
                              {doc.original_filename}
                            </Badge>
                          ))}
                          {documents.length === 0 && (
                            <p className="text-xs text-muted-foreground">
                              No documents uploaded yet
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Build Button */}
                      <div className="mt-4">
                        <Button
                          onClick={handleBuildAgent}
                          disabled={isBuilding || !instructionGoal.trim() || selectedDocIds.length === 0}
                          className="w-full gap-2 bg-gradient-to-br from-primary to-primary-dim sm:w-auto"
                        >
                          {isBuilding ? (
                            <>
                              <Spinner className="size-4" />
                              Building...
                            </>
                          ) : (
                            <>
                              <Cpu className="size-4" />
                              Build Agent
                            </>
                          )}
                        </Button>
                      </div>

                      {/* Build Progress */}
                      {buildJob && (
                        <div className="mt-4 rounded-xl bg-surface-container p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium text-foreground">
                                Job #{buildJob.id}
                              </p>
                              <Badge
                                className={cn(
                                  buildJob.status === 'queued' && 'bg-muted text-muted-foreground',
                                  buildJob.status === 'running' && 'bg-warning/10 text-warning',
                                  buildJob.status === 'completed' && 'bg-success/10 text-success',
                                  buildJob.status === 'failed' && 'bg-destructive/10 text-destructive'
                                )}
                              >
                                {buildJob.status === 'running' && <Spinner className="mr-1 size-3" />}
                                {buildJob.status === 'completed' && <CheckCircle2 className="mr-1 size-3" />}
                                {buildJob.status === 'failed' && <XCircle className="mr-1 size-3" />}
                                {buildJob.status}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">
                              v{buildJob.agent_spec_version}
                            </p>
                          </div>

                          {/* Progress Bar */}
                          {buildJob.status === 'running' && (
                            <div className="mt-3">
                              <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Processing documents</span>
                                <span>
                                  {buildJob.processed_docs} / {buildJob.total_docs}
                                </span>
                              </div>
                              <div className="mt-1 h-2 overflow-hidden rounded-full bg-surface-container-high">
                                <div
                                  className="h-full bg-gradient-to-r from-primary to-primary-dim transition-all"
                                  style={{
                                    width: `${(buildJob.processed_docs / buildJob.total_docs) * 100}%`,
                                  }}
                                />
                              </div>
                            </div>
                          )}

                          {buildJob.error_summary && (
                            <p className="mt-2 text-xs text-destructive">{buildJob.error_summary}</p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </section>

                {/* Section D: Active Spec */}
                <section className="rounded-2xl bg-surface-container-lowest p-4 sm:p-6 col-span-full">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-surface-container sm:size-12">
                      <Bot className="size-5 text-primary sm:size-6" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h2 className="font-[var(--font-manrope)] text-base font-semibold text-foreground sm:text-lg">
                          Active Agent Spec
                        </h2>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={fetchActiveSpec}
                          disabled={isLoadingSpec}
                        >
                          <RefreshCw className={cn('size-4', isLoadingSpec && 'animate-spin')} />
                        </Button>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
                        Currently deployed agent configuration
                      </p>

                      {isLoadingSpec ? (
                        <div className="mt-4 flex items-center justify-center py-8">
                          <Spinner className="size-6" />
                        </div>
                      ) : activeSpec ? (
                        <div className="mt-4 rounded-xl bg-surface-container p-4">
                          <div className="flex flex-wrap items-center gap-3">
                            <Badge className="bg-success/10 text-success">
                              <CheckCircle2 className="mr-1 size-3" />
                              Version {activeSpec.version}
                            </Badge>
                            <Badge className="bg-primary/10 text-primary">
                              {activeSpec.status}
                            </Badge>
                          </div>
                          <div className="mt-3 text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="size-3" />
                            Updated: {new Date(activeSpec.updated_at).toLocaleString()}
                          </div>
                          <div className="mt-3 rounded-lg bg-surface-container-low p-3">
                            <p className="text-sm text-foreground whitespace-pre-wrap line-clamp-4">
                              {activeSpec.instruction_text}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-4 flex flex-col items-center justify-center rounded-xl bg-surface-container py-8">
                          <AlertCircle className="size-8 text-muted-foreground" />
                          <p className="mt-2 text-sm text-muted-foreground">
                            No active agent spec
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Build your first agent to get started
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </section>
              </div>
            </TabsContent>

            {/* Chat Tab */}
            <TabsContent value="chat" className="flex-1 flex flex-col overflow-hidden mt-0">
              {!activeSpec ? (
                <div className="flex flex-1 flex-col items-center justify-center p-8">
                  <AlertCircle className="size-12 text-muted-foreground" />
                  <p className="mt-4 text-lg font-medium text-foreground">No Active Agent</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Build an agent in the Setup tab to start chatting
                  </p>
                  <Button
                    onClick={() => setActiveTab('setup')}
                    className="mt-4 gap-2 bg-gradient-to-br from-primary to-primary-dim"
                  >
                    <Cpu className="size-4" />
                    Go to Setup
                  </Button>
                </div>
              ) : (
                <>
                  {/* Chat Messages */}
                  <div
                    ref={chatScrollRef}
                    className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8"
                  >
                    <div className="mx-auto max-w-3xl space-y-6">
                      {chatMessages.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-12">
                          <Bot className="size-12 text-muted-foreground" />
                          <p className="mt-4 text-lg font-medium text-foreground">
                            Chat with Generated Agent v{activeSpec.version}
                          </p>
                          <p className="mt-1 text-sm text-muted-foreground text-center">
                            Ask questions to test your generated agent
                          </p>
                        </div>
                      )}

                      {chatMessages.map((message) => (
                        <div
                          key={message.id}
                          className={cn(
                            'flex gap-3 sm:gap-4',
                            message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                          )}
                        >
                          {/* Avatar */}
                          <div
                            className={cn(
                              'flex size-8 shrink-0 items-center justify-center rounded-xl sm:size-10',
                              message.role === 'user'
                                ? 'bg-gradient-to-br from-primary to-primary-dim'
                                : 'bg-surface-container-highest'
                            )}
                          >
                            {message.role === 'user' ? (
                              <User className="size-4 text-primary-foreground sm:size-5" />
                            ) : (
                              <Bot className="size-4 text-foreground sm:size-5" />
                            )}
                          </div>

                          {/* Message Content */}
                          <div
                            className={cn(
                              'group relative max-w-[85%] space-y-2 sm:max-w-[75%] sm:space-y-3',
                              message.role === 'user' ? 'items-end' : 'items-start'
                            )}
                          >
                            <div
                              className={cn(
                                'rounded-xl px-4 py-3 sm:px-5 sm:py-4',
                                message.role === 'user'
                                  ? 'rounded-br-sm bg-gradient-to-br from-primary to-primary-dim text-primary-foreground'
                                  : 'rounded-bl-sm bg-surface-container-highest text-foreground'
                              )}
                            >
                              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                                {message.content}
                              </p>
                            </div>

                            {/* Spec Version */}
                            {message.agent_spec_version && (
                              <p className="text-xs text-muted-foreground">
                                v{message.agent_spec_version}
                              </p>
                            )}

                            {/* Report Mistake */}
                            {message.role === 'assistant' && (
                              <div className="opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100">
                                {reportingMessageId === message.id ? (
                                  <div className="flex flex-col gap-2 rounded-xl bg-surface-container p-3">
                                    <Textarea
                                      value={feedbackInput}
                                      onChange={(e) => setFeedbackInput(e.target.value)}
                                      placeholder="What's wrong with this response?"
                                      className="min-h-16 resize-none border-none bg-surface-container-low text-sm"
                                    />
                                    <div className="flex gap-2">
                                      <Button
                                        size="sm"
                                        onClick={() => handleReportMistake(message)}
                                        disabled={!feedbackInput.trim()}
                                        className="gap-1 bg-destructive text-destructive-foreground"
                                      >
                                        Submit
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => {
                                          setReportingMessageId(null);
                                          setFeedbackInput('');
                                        }}
                                      >
                                        Cancel
                                      </Button>
                                    </div>
                                  </div>
                                ) : (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-destructive"
                                    onClick={() => setReportingMessageId(message.id)}
                                  >
                                    <AlertCircle className="size-3" />
                                    Report Mistake
                                  </Button>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}

                      {isChatLoading && (
                        <div className="flex gap-3 sm:gap-4">
                          <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-surface-container-highest sm:size-10">
                            <Bot className="size-4 text-foreground sm:size-5" />
                          </div>
                          <div className="rounded-xl rounded-bl-sm bg-surface-container-highest px-4 py-3">
                            <Spinner className="size-5" />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Chat Input */}
                  <div className="border-t border-surface-container-high bg-surface-container-lowest px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
                    <div className="mx-auto max-w-3xl">
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          handleChatSend();
                        }}
                        className="flex items-center h-full gap-2 rounded-2xl bg-surface-container-low p-2 transition-all duration-200 focus-within:bg-surface-container-lowest focus-within:ring-2 focus-within:ring-primary/20 sm:gap-3 sm:p-3"
                      >
                        <textarea
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleChatSend();
                            }
                          }}
                          placeholder="Ask the generated agent..."
                          disabled={isChatLoading}
                          rows={1}
                          className="flex-1 resize-none bg-transparent py-1 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50 sm:py-0"
                        />
                        <Button
                          type="submit"
                          size="icon"
                          disabled={!chatInput.trim() || isChatLoading}
                          className="size-9 shrink-0 rounded-xl bg-gradient-to-br from-primary to-primary-dim hover:from-primary/90 hover:to-primary-dim/90 disabled:opacity-50 sm:size-10"
                        >
                          {isChatLoading ? (
                            <Spinner className="size-4" />
                          ) : (
                            <Send className="size-4" />
                          )}
                        </Button>
                      </form>
                    </div>
                  </div>
                </>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </AppShell>
  );
}
