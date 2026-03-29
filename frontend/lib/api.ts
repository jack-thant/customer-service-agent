import type {
  ChatRequest,
  ChatResponse,
  BotConfig,
  UpdateConfigRequest,
  ReingestResponse,
  Mistake,
  CreateMistakeRequest,
  UpdateMistakeRequest,
  MistakeStatus,
  // Part 2 Agent types
  AgentDocument,
  BuildJobRequest,
  BuildJobResponse,
  BuildJobStatusResponse,
  MetaChatRequest,
  MetaChatResponse,
  AgentSpec,
  ActivateSpecResponse,
  AgentChatRequest,
  AgentChatResponse,
  CreateAgentMistakeRequest,
  AgentSpecResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// Health API
export async function checkHealth(): Promise<{ message: string }> {
  return fetchAPI<{ message: string }>('/');
}

// Chat API
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  return fetchAPI<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Config API
export async function getConfig(): Promise<BotConfig> {
  return fetchAPI<BotConfig>('/config');
}

export async function updateConfig(request: UpdateConfigRequest): Promise<BotConfig> {
  return fetchAPI<BotConfig>('/config', {
    method: 'PUT',
    body: JSON.stringify(request),
  });
}

export async function reingestKnowledgeBase(forceReingest = false): Promise<ReingestResponse> {
  return fetchAPI<ReingestResponse>('/config/reingest', {
    method: 'POST',
    body: JSON.stringify({ force_reingest: forceReingest }),
  });
}

// Mistakes API
export async function getMistakes(status?: MistakeStatus): Promise<Mistake[]> {
  const params = status ? `?status=${status}` : '';
  return fetchAPI<Mistake[]>(`/mistakes${params}`);
}

export async function createMistake(request: CreateMistakeRequest): Promise<Mistake> {
  return fetchAPI<Mistake>('/mistakes', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function updateMistakeStatus(
  mistakeId: number,
  request: UpdateMistakeRequest
): Promise<Mistake> {
  return fetchAPI<Mistake>(`/mistakes/${mistakeId}`, {
    method: 'PATCH',
    body: JSON.stringify(request),
  });
}

// Part 2: Agent API

// Upload Document
export async function uploadAgentDocument(file: File): Promise<AgentDocument> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/agent/docs`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || `Upload Error: ${response.status}`);
  }

  return response.json();
}

// Build Agent
export async function buildAgent(request: BuildJobRequest): Promise<BuildJobResponse> {
  return fetchAPI<BuildJobResponse>('/agent/build', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Get Build Job Status
export async function getBuildJobStatus(jobId: number): Promise<BuildJobStatusResponse> {
  return fetchAPI<BuildJobStatusResponse>(`/agent/build/${jobId}`);
}

// Meta Chat
export async function sendMetaChat(request: MetaChatRequest): Promise<MetaChatResponse> {
  return fetchAPI<MetaChatResponse>('/agent/meta-chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Get Active Spec
export async function getActiveSpec(): Promise<AgentSpec> {
  return fetchAPI<AgentSpec>('/agent/spec/active');
}

// Get All Specs
export async function getAllSpecs(): Promise<AgentSpec[]> {
  return fetchAPI<AgentSpec[]>('/agent/specs');
}

// Activate Spec Version
export async function activateSpecVersion(version: number): Promise<ActivateSpecResponse> {
  return fetchAPI<ActivateSpecResponse>(`/agent/spec/${version}/activate`, {
    method: 'POST',
  });
}

// Agent Chat (Part 2)
export async function sendAgentChatMessage(request: AgentChatRequest): Promise<AgentChatResponse> {
  return fetchAPI<AgentChatResponse>('/agent/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Report Mistake for Part 2
export async function createAgentMistake(request: CreateAgentMistakeRequest): Promise<Mistake> {
  return fetchAPI<Mistake>('/mistakes', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
