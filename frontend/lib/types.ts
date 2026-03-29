// Chat types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  route?: string;
  requires_followup?: boolean;
  followup_field?: string | null;
}

export interface Source {
  title: string | null;
  url: string | null;
  snippet: string | null;
}

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface ChatResponse {
  answer: string;
  route: string;
  sources: Source[];
  requires_followup: boolean;
  followup_field: string | null;
}

// Config types
export interface BotConfig {
  kb_url: string;
  additional_guidelines: string;
  updated_at: string;
}

export interface UpdateConfigRequest {
  kb_url: string;
  additional_guidelines: string;
}

export interface ReingestResponse {
  message: string;
  kb_url: string;
  force_reingest: boolean;
  articles_ingested: number;
}

// Mistake types
export type MistakeStatus = 'open' | 'patched' | 'fixed' | 'archived';

export interface Mistake {
  id: number;
  user_query: string;
  bot_answer: string;
  feedback: string;
  route: string | null;
  session_id: string | null;
  status: MistakeStatus;
  root_cause: string | null;
  suggested_fix: string | null;
  applied_fix: string | null;
  rerun_answer: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateMistakeRequest {
  user_query: string;
  bot_answer: string;
  feedback: string;
  route?: string | null;
  session_id?: string | null;
}

export interface UpdateMistakeRequest {
  status: MistakeStatus;
}

// Part 2: Agent Types

// Document Upload
export interface AgentDocument {
  id: number;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  checksum: string;
  status: 'uploaded' | 'processing' | 'ready' | 'error';
  created_at: string;
}

// Build Job
export type BuildJobStatus = 'queued' | 'running' | 'completed' | 'failed';

export interface BuildJobRequest {
  instruction_goal: string;
  document_ids: number[];
}

export interface BuildJobResponse {
  job_id: number;
  agent_spec_version: number;
  status: BuildJobStatus;
}

export interface BuildJobStatusResponse {
  id: number;
  agent_spec_version: number;
  status: BuildJobStatus;
  total_docs: number;
  processed_docs: number;
  error_summary: string | null;
  created_at: string;
  updated_at: string;
}

// Meta Chat
export interface MetaChatRequest {
  message: string;
  current_instructions: string;
}

export interface MetaChatResponse {
  proposed_instructions: string;
}

// Agent Spec
export interface AgentSpec {
  version: number;
  instruction_text: string;
  status: 'ready' | 'building' | 'error';
  active: boolean;
  updated_at: string;
}

export interface ActivateSpecResponse {
  version: number;
  active: boolean;
}

// Agent Chat (Part 2)
export interface AgentChatRequest {
  session_id: string;
  message: string;
}

export interface AgentChatSource {
  title: string;
  url: string;
  snippet: string;
}

export interface AgentChatResponse {
  answer: string;
  route: string;
  sources: AgentChatSource[];
  requires_followup: boolean;
  followup_field: string | null;
  agent_spec_version: number;
}

// Agent Chat Message (extends base ChatMessage)
export interface AgentChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: AgentChatSource[];
  route?: string;
  requires_followup?: boolean;
  followup_field?: string | null;
  agent_spec_version?: number;
}

// Part 2 Mistake Report
export interface CreateAgentMistakeRequest {
  user_query: string;
  bot_answer: string;
  feedback: string;
  route?: string | null;
  session_id?: string | null;
  runtime: 'part2';
  agent_spec_version: number;
}

export interface AgentSpecResponse {
  version: number;
  instruction_text: string;
  status: string;
  active: boolean;
  updated_at: string;
}
