import type {
  Paper,
  QueueResponse,
  Annotation,
  ResearchContext,
  ResearchQuestion,
  Pattern,
  UserPreferences,
  ChatThread,
  ChatMessage,
  Briefing,
} from '../types';

const API_BASE = '/api/v1';

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

// Paper API
export const papersApi = {
  list: (params?: { status?: string; tags?: string[] }) =>
    fetchApi<Paper[]>(`/papers${params ? `?${new URLSearchParams(params as Record<string, string>)}` : ''}`),

  get: (id: string) => fetchApi<Paper>(`/papers/${id}`),

  create: (data: Partial<Paper>) =>
    fetchApi<Paper>('/papers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Paper>) =>
    fetchApi<Paper>(`/papers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchApi<{ success: boolean }>(`/papers/${id}`, {
      method: 'DELETE',
    }),

  getQueue: () => fetchApi<QueueResponse>('/papers/queue'),

  reorderQueue: (paperIds: string[]) =>
    fetchApi<{ success: boolean }>('/papers/queue/reorder', {
      method: 'POST',
      body: JSON.stringify(paperIds),
    }),

  getAnnotations: (paperId: string) =>
    fetchApi<Annotation[]>(`/papers/${paperId}/annotations`),

  createAnnotation: (paperId: string, data: Omit<Annotation, 'id' | 'paper_id' | 'created_at'>) =>
    fetchApi<Annotation>(`/papers/${paperId}/annotations`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateAnnotation: (annotationId: string, data: Partial<Annotation>) =>
    fetchApi<Annotation>(`/papers/annotations/${annotationId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteAnnotation: (annotationId: string) =>
    fetchApi<{ success: boolean }>(`/papers/annotations/${annotationId}`, {
      method: 'DELETE',
    }),
};

// Research Context API
export const contextApi = {
  get: () => fetchApi<ResearchContext>('/context'),

  getSummary: () => fetchApi<{ summary: string }>('/context/summary'),

  // Research Questions
  getQuestions: () => fetchApi<ResearchQuestion[]>('/context/questions'),

  createQuestion: (data: { question: string; description?: string }) =>
    fetchApi<ResearchQuestion>('/context/questions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateQuestion: (id: string, data: Partial<ResearchQuestion>) =>
    fetchApi<ResearchQuestion>(`/context/questions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteQuestion: (id: string) =>
    fetchApi<{ success: boolean }>(`/context/questions/${id}`, {
      method: 'DELETE',
    }),

  // Patterns
  getPatterns: () => fetchApi<Pattern[]>('/context/patterns'),

  acknowledgePattern: (id: string) =>
    fetchApi<Pattern>(`/context/patterns/${id}/acknowledge`, {
      method: 'POST',
    }),

  analyzePatterns: () =>
    fetchApi<{ success: boolean; operation_id: string }>('/context/analyze', {
      method: 'POST',
    }),

  // Preferences
  getPreferences: () => fetchApi<UserPreferences>('/context/preferences'),

  updatePreferences: (data: Partial<UserPreferences>) =>
    fetchApi<UserPreferences>('/context/preferences', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Briefing
  generateBriefing: () =>
    fetchApi<Briefing>('/context/briefing', {
      method: 'POST',
    }),
};

// Chat API
export const chatApi = {
  getThread: (id: string) => fetchApi<ChatThread>(`/chat/threads/${id}`),

  listThreads: (params?: { paper_id?: string; question_id?: string }) =>
    fetchApi<ChatThread[]>(`/chat/threads${params ? `?${new URLSearchParams(params as Record<string, string>)}` : ''}`),

  createThread: (data: {
    context_type: string;
    paper_id?: string;
    question_id?: string;
    synthesis_scope?: string[];
  }) =>
    fetchApi<ChatThread>('/chat/threads', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  sendMessage: (threadId: string, content: string) =>
    fetchApi<ChatMessage>(`/chat/threads/${threadId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  getMessages: (threadId: string) =>
    fetchApi<ChatMessage[]>(`/chat/threads/${threadId}/messages`),
};

// Sync API
export const syncApi = {
  syncPaperToNotion: (paperId: string) =>
    fetchApi<{ success: boolean; notion_page_id?: string }>(`/sync/notion/paper/${paperId}`, {
      method: 'POST',
    }),

  pullFromNotion: () =>
    fetchApi<{ success: boolean; synced_count: number }>('/sync/notion/pull', {
      method: 'POST',
    }),

  saveLiteratureNote: (paperId: string) =>
    fetchApi<{ success: boolean; path?: string }>(`/sync/obsidian/literature-note/${paperId}`, {
      method: 'POST',
    }),

  importFromArxiv: (arxivId: string) =>
    fetchApi<{ success: boolean; paper_id: string; title: string }>('/sync/arxiv/import', {
      method: 'POST',
      body: JSON.stringify({ arxiv_id: arxivId }),
    }),
};
