// Paper types
export type PaperStatus =
  | 'new'
  | 'processing'
  | 'claude_reviewed'
  | 'reading'
  | 'read'
  | 'synthesized'
  | 'archived';

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  venue: string | null;
  year: number | null;
  abstract: string | null;
  pdf_url: string;
  source_url: string | null;
  source_id: string | null;
  added_at: string;
  status: PaperStatus;
  priority: number;
  relevance_score: number | null;
  relevance_reason: string | null;
  tags: string[];
  claude_review: ClaudeReview | null;
  notion_page_id: string | null;
  annotation_count: number;
}

export interface ClaudeReview {
  summary: string;
  key_contributions: string[];
  methodology: string | null;
  relevance_analysis: string;
  connections: PaperConnection[];
  suggested_tags: string[];
  discussion_questions: string[];
  reviewed_at: string;
}

export interface PaperConnection {
  target_paper_id: string | null;
  target_title: string;
  connection_type: 'cites' | 'cited_by' | 'similar' | 'foundational' | 'contrasts';
  explanation: string;
}

export interface Annotation {
  id: string;
  paper_id: string;
  author: 'user' | 'claude';
  type: 'highlight' | 'note' | 'question';
  page_number: number;
  selected_text: string | null;
  content: string;
  thread_id: string | null;
  created_at: string;
  position: AnnotationPosition | null;
}

export interface AnnotationPosition {
  page_index: number;
  rects: Array<{ x: number; y: number; width: number; height: number }>;
}

export interface QueueResponse {
  papers: Paper[];
  total_count: number;
  new_count: number;
  claude_reviewed_count: number;
  reading_count: number;
}

// Research Context types
export interface ResearchQuestion {
  id: string;
  question: string;
  description: string | null;
  status: 'active' | 'paused' | 'resolved';
  related_paper_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface Pattern {
  id: string;
  description: string;
  paper_ids: string[];
  identified_at: string;
  acknowledged: boolean;
}

export interface UserPreferences {
  weight_relevance: number;
  weight_recency: number;
  weight_foundational: number;
  weight_social: number;
  push_enabled: boolean;
  email_enabled: boolean;
  email_digest: 'none' | 'daily' | 'weekly';
  briefing_schedule: string | null;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  quiet_hours_timezone: string | null;
}

export interface ResearchContext {
  id: string;
  user_id: string;
  research_questions: ResearchQuestion[];
  patterns: Pattern[];
  preferences: UserPreferences | null;
  created_at: string;
  updated_at: string;
}

// Chat types
export interface ChatMessage {
  id: string;
  thread_id: string;
  role: 'user' | 'assistant';
  content: string;
  annotation_references: string[] | null;
  created_at: string;
}

export interface ChatThread {
  id: string;
  context_type: 'paper' | 'research_question' | 'synthesis' | 'general';
  paper_id: string | null;
  question_id: string | null;
  synthesis_scope: string[] | null;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

// Briefing type
export interface Briefing {
  briefing: string;
  generated_at: string;
  paper_count: number;
}
