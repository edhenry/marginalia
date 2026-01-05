# Research Collaboration System Specification

**Version**: 0.1 (Draft)  
**Author**: Ed + Claude  
**Last Updated**: January 2026

---

## 1. Overview

### 1.1 Vision

A collaborative research workflow system that positions Claude as an active research partner rather than a passive tool. The system handles administrative overhead (paper tracking, queue management, note generation, context maintenance) while surfacing what requires human attention. The human focuses on reading, thinking, and deciding; Claude handles logistics and provides substantive intellectual collaboration.

### 1.2 Core Principles

1. **Claude as proactive collaborator**: Claude reviews papers asynchronously, identifies connections, surfaces insights, and maintains research context without being asked.

2. **Mobile-first reading**: iPad and phone are primary reading environments. The system must support comfortable long-form reading and annotation on these devices.

3. **Leverage existing tools**: Notion, Obsidian, and paper management tools are integrated rather than replaced. The system is a collaboration layer, not a monolithic replacement.

4. **Inbox-based handoffs**: Claude writes to designated inboxes (Obsidian, Notion). The human reviews, edits, and promotes content—maintaining sovereignty over their knowledge systems.

5. **Context accumulates**: The system maintains a persistent understanding of the user's research agenda, reading history, and emerging ideas. Each interaction is informed by this context.

---

## 2. User Stories

### 2.1 Paper Ingestion

> "I found a paper on Twitter. I save it to my reading list. By the time I'm ready to read it, Claude has already reviewed it, assessed its relevance to my current work, identified connections to papers I've read, and prepared discussion questions."

### 2.2 Mobile Reading Session

> "I have 30 minutes on the train. I open the app, see my prioritized queue with Claude's relevance notes. I pick a paper, read on my iPad, highlight key passages. When I highlight something confusing, I tap 'Ask Claude' and get an explanation in context. My highlights and our discussion are preserved."

### 2.3 Collaborative Synthesis

> "After reading a paper, I see Claude's draft literature note in my Obsidian inbox. It captures the key contributions and suggests connections to my existing notes. I edit it, add my own thoughts, and file it in my vault. The connections Claude suggested become actual links in my knowledge graph."

### 2.4 Proactive Discovery

> "Claude notices that three papers I've read this week all cite a foundational paper I haven't read. It adds that paper to my queue with a note explaining why it's suddenly relevant."

### 2.5 Research Briefing

> "Monday morning, I get a briefing: 'You have 5 papers in queue. Based on your GNN expressiveness research question, I'd prioritize Paper X—it directly addresses the WL hierarchy limitation you noted last week. Paper Y can probably wait; it's tangentially related. Also, I noticed a pattern across your recent reading—want me to draft a synthesis note?'"

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                         Client Applications                         │
│                                                                     │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐  │
│   │   Web App       │   │   iOS/iPad      │   │   Notifications │  │
│   │   (React PWA)   │   │   (PWA)         │   │   (Push/Email)  │  │
│   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘  │
│            │                     │                     │           │
└────────────┼─────────────────────┼─────────────────────┼───────────┘
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          API Gateway                                │
│                   (Auth, Rate Limiting, Routing)                    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
         ┌───────────────┬─────────┴─────────┬───────────────┐
         ▼               ▼                   ▼               ▼
┌─────────────┐  ┌─────────────┐     ┌─────────────┐  ┌─────────────┐
│   Paper     │  │  Research   │     │   Claude    │  │    Sync     │
│   Service   │  │  Context    │     │   Service   │  │   Service   │
│             │  │   Service   │     │             │  │             │
│ • Storage   │  │ • Agenda    │     │ • MCP Host  │  │ • Notion    │
│ • Metadata  │  │ • History   │     │ • Async Ops │  │ • Obsidian  │
│ • Annotate  │  │ • Prefs     │     │ • Chat      │  │ • alphaxiv  │
│ • Queue     │  │ • Patterns  │     │ • Briefings │  │             │
└─────────────┘  └─────────────┘     └─────────────┘  └─────────────┘
         │               │                   │               │
         └───────────────┴─────────┬─────────┴───────────────┘
                                   ▼
                    ┌──────────────────────────┐
                    │       Data Layer         │
                    │                          │
                    │  ┌────────┐ ┌─────────┐  │
                    │  │ SQLite │ │  Blob   │  │
                    │  │  (or   │ │ Storage │  │
                    │  │ Postgres│ │ (PDFs)  │  │
                    │  └────────┘ └─────────┘  │
                    │                          │
                    └──────────────────────────┘
```

### 3.2 Component Descriptions

#### 3.2.1 Web Application (React PWA)

**Purpose**: Primary user interface for all platforms.

**Key Capabilities**:
- Responsive design optimized for desktop, tablet, and phone
- PDF viewing with annotation layer
- Real-time collaboration chat
- Queue management and prioritization views
- Offline support for reading cached papers

**Technology**: React, TypeScript, Tailwind CSS, PDF.js (or PSPDFKit for better mobile annotation), Service Workers for offline.

#### 3.2.2 Paper Service

**Purpose**: Manages papers, PDFs, annotations, and reading queue.

**Data Model**:
```typescript
interface Paper {
  id: string;
  title: string;
  authors: string[];
  venue?: string;
  year?: number;
  abstract?: string;
  pdfUrl: string;           // Internal blob storage URL
  sourceUrl?: string;       // Original URL (arXiv, alphaxiv, etc.)
  sourceId?: string;        // External ID (arXiv ID, DOI)
  addedAt: DateTime;
  status: PaperStatus;
  priority: number;         // Claude-suggested, user-adjustable
  relevanceScore?: number;  // 0-1, Claude-assessed
  relevanceReason?: string; // Why Claude thinks it's relevant
  tags: string[];
  claudeReview?: ClaudeReview;
  notionPageId?: string;    // Link to Notion queue entry
}

enum PaperStatus {
  NEW = "new",                      // Just added, not yet processed
  PROCESSING = "processing",        // Claude is reviewing
  CLAUDE_REVIEWED = "claude_reviewed",  // Ready for human
  READING = "reading",              // Human is actively reading
  READ = "read",                    // Human finished reading
  SYNTHESIZED = "synthesized",      // Literature note complete
  ARCHIVED = "archived"             // No longer active
}

interface ClaudeReview {
  summary: string;                  // 2-3 paragraph summary
  keyContributions: string[];       // Bullet points
  methodology?: string;             // Brief methodology description
  relevanceAnalysis: string;        // Why this matters to user's research
  connections: PaperConnection[];   // Links to other papers
  suggestedTags: string[];
  discussionQuestions: string[];    // Seeded questions for collaboration
  reviewedAt: DateTime;
}

interface PaperConnection {
  targetPaperId?: string;           // If paper is in system
  targetTitle: string;              // For display
  connectionType: "cites" | "cited_by" | "similar" | "foundational" | "contrasts";
  explanation: string;
}

interface Annotation {
  id: string;
  paperId: string;
  author: "user" | "claude";
  type: "highlight" | "note" | "question";
  pageNumber: number;
  position: AnnotationPosition;     // PDF coordinates
  selectedText?: string;
  content: string;                  // Note or question text
  threadId?: string;                // Link to discussion thread
  createdAt: DateTime;
}

interface AnnotationPosition {
  rects: Array<{x: number, y: number, width: number, height: number}>;
  pageIndex: number;
}
```

**API Endpoints**:
```
POST   /papers                    # Add new paper (URL or PDF upload)
GET    /papers                    # List papers (with filters)
GET    /papers/:id                # Get paper details
PATCH  /papers/:id                # Update paper (status, priority, etc.)
DELETE /papers/:id                # Archive/delete paper

GET    /papers/:id/pdf            # Get PDF content
GET    /papers/:id/annotations    # Get all annotations
POST   /papers/:id/annotations    # Create annotation
PATCH  /annotations/:id           # Update annotation
DELETE /annotations/:id           # Delete annotation

GET    /queue                     # Get prioritized reading queue
POST   /queue/reorder             # Manual reorder
```

#### 3.2.3 Research Context Service

**Purpose**: Maintains persistent understanding of user's research agenda, patterns, and preferences.

**Data Model**:
```typescript
interface ResearchContext {
  userId: string;
  
  // Explicit research agenda
  researchQuestions: ResearchQuestion[];
  
  // Reading history and patterns
  readingHistory: ReadingEvent[];
  
  // Emerging patterns (Claude-identified)
  identifiedPatterns: Pattern[];
  
  // User preferences
  preferences: UserPreferences;
}

interface ResearchQuestion {
  id: string;
  question: string;
  description?: string;
  status: "active" | "paused" | "resolved";
  relatedPaperIds: string[];
  createdAt: DateTime;
  updatedAt: DateTime;
}

interface ReadingEvent {
  paperId: string;
  action: "started" | "annotated" | "discussed" | "completed" | "synthesized";
  timestamp: DateTime;
  metadata?: Record<string, any>;
}

interface Pattern {
  id: string;
  description: string;
  paperIds: string[];
  identifiedAt: DateTime;
  acknowledged: boolean;    // User has seen this
}

interface UserPreferences {
  prioritizationWeights: {
    relevanceToActiveQuestions: number;   // 0-1
    recency: number;
    foundationalImportance: number;
    socialSignal: number;
  };
  notificationPreferences: NotificationPrefs;
  briefingSchedule?: string;  // Cron expression
}
```

**API Endpoints**:
```
GET    /context                        # Get full research context
PATCH  /context                        # Update context

GET    /context/questions              # List research questions
POST   /context/questions              # Add research question
PATCH  /context/questions/:id          # Update question
DELETE /context/questions/:id          # Remove question

GET    /context/patterns               # Get identified patterns
POST   /context/patterns/:id/acknowledge  # Mark pattern as seen

POST   /context/analyze                # Trigger pattern analysis
```

#### 3.2.4 Claude Service

**Purpose**: Interface to Claude API with context management and MCP integration.

**MCP Servers Exposed**:

```typescript
// Papers MCP Server
interface PapersMCP {
  // Tools
  "papers/search": (query: string) => Paper[];
  "papers/get": (id: string) => Paper;
  "papers/get_pdf_content": (id: string, pageRange?: [number, number]) => string;
  "papers/get_annotations": (id: string) => Annotation[];
  "papers/add_annotation": (paperId: string, annotation: Omit<Annotation, "id">) => Annotation;
  
  // Resources
  "papers://queue": Paper[];           // Current reading queue
  "papers://recent": Paper[];          // Recently read
}

// Research Context MCP Server
interface ContextMCP {
  // Tools
  "context/get_questions": () => ResearchQuestion[];
  "context/get_patterns": () => Pattern[];
  "context/record_insight": (insight: string, relatedPaperIds: string[]) => void;
  
  // Resources
  "context://agenda": ResearchContext;  // Full research context
  "context://summary": string;          // Condensed context for prompts
}

// Notes MCP Server (Obsidian integration)
interface NotesMCP {
  // Tools
  "notes/create_draft": (title: string, content: string, folder?: string) => void;
  "notes/search": (query: string) => NoteReference[];
  "notes/get": (path: string) => string;
  
  // Resources
  "notes://concepts": NoteReference[];  // Existing concept notes
  "notes://recent": NoteReference[];    // Recently modified notes
}

// Notion MCP Server
interface NotionMCP {
  // Tools
  "notion/query_database": (databaseId: string, filter?: object) => NotionPage[];
  "notion/create_page": (databaseId: string, properties: object) => NotionPage;
  "notion/update_page": (pageId: string, properties: object) => NotionPage;
}
```

**Async Operations**:

```typescript
interface AsyncOperation {
  id: string;
  type: "paper_review" | "pattern_analysis" | "briefing_generation" | "synthesis_draft";
  status: "queued" | "running" | "completed" | "failed";
  input: Record<string, any>;
  output?: Record<string, any>;
  createdAt: DateTime;
  completedAt?: DateTime;
}

// Paper Review Pipeline
async function reviewPaper(paperId: string): Promise<ClaudeReview> {
  // 1. Fetch paper and PDF content
  // 2. Fetch research context
  // 3. Fetch related papers from library
  // 4. Call Claude API with structured prompt
  // 5. Parse and store review
  // 6. Update paper status
  // 7. Trigger notifications if high relevance
}

// Pattern Analysis Pipeline  
async function analyzePatterns(): Promise<Pattern[]> {
  // 1. Fetch recent reading history
  // 2. Fetch paper reviews and annotations
  // 3. Call Claude to identify emerging patterns
  // 4. Store new patterns
  // 5. Notify user of significant discoveries
}
```

**Chat Interface**:

The chat interface maintains conversation threads tied to specific contexts (paper, research question, synthesis task).

```typescript
interface ChatThread {
  id: string;
  context: ChatContext;
  messages: ChatMessage[];
  createdAt: DateTime;
  updatedAt: DateTime;
}

interface ChatContext {
  type: "paper" | "research_question" | "synthesis" | "general";
  paperId?: string;
  questionId?: string;
  synthesisScope?: string[];  // Paper IDs being synthesized
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  annotations?: AnnotationReference[];  // Links to paper annotations
  createdAt: DateTime;
}
```

#### 3.2.5 Sync Service

**Purpose**: Bidirectional sync with external systems.

**Notion Sync**:
```typescript
interface NotionSyncConfig {
  queueDatabaseId: string;        // Reading queue database
  researchAgendaDatabaseId: string;  // Research questions database
  syncInterval: number;           // Minutes between syncs
}

// Sync operations
async function syncPaperToNotion(paper: Paper): Promise<void>;
async function syncNotionToQueue(): Promise<void>;  // Pull manual changes
```

**Obsidian Sync**:
```typescript
interface ObsidianSyncConfig {
  vaultPath: string;              // Path to Obsidian vault (git repo)
  inboxFolder: string;            // Where Claude writes drafts (e.g., "inbox/")
  conceptsFolder: string;         // Where to look for concept notes
  gitRemote?: string;             // For sync across devices
}

// Sync operations
async function writeDraftNote(title: string, content: string): Promise<void>;
async function indexConceptNotes(): Promise<NoteReference[]>;
async function pullVaultChanges(): Promise<void>;
async function pushVaultChanges(): Promise<void>;
```

**alphaxiv Integration**:
```typescript
interface AlphaxivConfig {
  watchedTopics: string[];        // Topics to monitor
  watchedAuthors: string[];       // Authors to follow
  pollInterval: number;           // Hours between checks
}

// Operations
async function checkForNewPapers(): Promise<Paper[]>;
async function importPaper(arxivId: string): Promise<Paper>;
async function fetchDiscussion(arxivId: string): Promise<Discussion>;
```

---

## 4. User Interface Design

### 4.1 Information Architecture

```
├── Dashboard (Home)
│   ├── Today's Briefing
│   ├── Quick Actions
│   └── Recent Activity
│
├── Reading Queue
│   ├── Priority View (default)
│   ├── By Status
│   ├── By Research Question
│   └── All Papers
│
├── Paper View
│   ├── PDF Reader
│   ├── Annotations Panel
│   ├── Collaboration Panel
│   └── Notes Panel
│
├── Research Agenda
│   ├── Active Questions
│   ├── Patterns & Insights
│   └── Synthesis Documents
│
├── Notes (Obsidian Bridge)
│   ├── Inbox (Claude drafts)
│   ├── Recent Notes
│   └── Search
│
└── Settings
    ├── Integrations
    ├── Notification Preferences
    └── Research Context
```

### 4.2 Key Screens

#### 4.2.1 Dashboard / Briefing View

**Purpose**: Daily starting point. What needs attention?

**Components**:
- **Briefing Card**: Claude's assessment of what to focus on today
- **Priority Queue Preview**: Top 3-5 papers with relevance indicators
- **Pending Items**: Things waiting for user action (draft notes to review, patterns to acknowledge)
- **Recent Activity**: What happened since last visit

**Mobile Adaptation**: Full-screen briefing card, swipeable queue preview.

#### 4.2.2 Paper Reading View

**Purpose**: Primary reading and collaboration environment.

**Desktop Layout**:
```
┌────────────────────────────────────────────────────────────────────┐
│  ◀ Queue    Paper Title                           [Status ▼] [⋮]  │
├───────────────────────────────────────┬────────────────────────────┤
│                                       │  [Collab] [Annot] [Notes]  │
│                                       ├────────────────────────────┤
│                                       │                            │
│                                       │   Claude's Pre-Review      │
│           PDF Viewer                  │   ───────────────────      │
│                                       │   Summary text...          │
│    ┌─────────────────────────┐        │                            │
│    │                         │        │   Questions for You:       │
│    │   [Highlighted text]    │        │   • Question 1?            │
│    │                         │        │   • Question 2?            │
│    │                         │        ├────────────────────────────┤
│    │                         │        │   Discussion Thread        │
│    └─────────────────────────┘        │                            │
│                                       │   Claude: I noticed...     │
│    Page 3 of 12    [◀] [▶]            │   You: That connects to... │
│                                       │   Claude: Yes, and...      │
│                                       │                            │
│                                       ├────────────────────────────┤
│                                       │   [Type a message...]  [➤] │
└───────────────────────────────────────┴────────────────────────────┘
```

**Tablet Layout** (iPad primary use case):
```
┌────────────────────────────────────────────────────────────────────┐
│  ◀   Paper Title                                  [Claude 💬] [⋮]  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│                                                                    │
│                        PDF Viewer                                  │
│                    (Full Width for Reading)                        │
│                                                                    │
│    ┌─────────────────────────────────────────────────────────┐     │
│    │                                                         │     │
│    │          [User selects text]                            │     │
│    │                                                         │     │
│    │          ┌─────────────────────────────┐                │     │
│    │          │ Highlight | Note | Ask Claude│               │     │
│    │          └─────────────────────────────┘                │     │
│    │                                                         │     │
│    └─────────────────────────────────────────────────────────┘     │
│                                                                    │
│    Page 3 of 12                                         [◀] [▶]   │
├────────────────────────────────────────────────────────────────────┤
│  [Annotations: 5]        [Claude's Review]        [Discussion: 3]  │
└────────────────────────────────────────────────────────────────────┘

─── When "Claude 💬" tapped, slide-over panel appears: ───

┌────────────────────────────────────────────────────────────────────┐
│                                          ┌────────────────────────┐│
│                                          │  Discussion      [✕]  ││
│         PDF Viewer                       ├────────────────────────┤│
│        (Compressed)                      │                        ││
│                                          │  Claude: About the     ││
│                                          │  positional encoding...││
│                                          │                        ││
│                                          │  You: How does this    ││
│                                          │  relate to WL?         ││
│                                          │                        ││
│                                          │  Claude: Great question││
│                                          │  The connection is...  ││
│                                          │                        ││
│                                          ├────────────────────────┤│
│                                          │ [Message...]      [➤] ││
│                                          └────────────────────────┘│
└────────────────────────────────────────────────────────────────────┘
```

**Phone Layout**:
- Full-screen PDF with floating action button for Claude
- Bottom sheet for quick actions on text selection
- Swipe to access collaboration panel
- Annotation indicators on page margins

**Key Interactions**:

1. **Text Selection → Action Menu**
   - Highlight (color options)
   - Add Note
   - Ask Claude (opens chat with selected text as context)
   
2. **Tap Existing Annotation**
   - View note/discussion
   - Edit
   - Delete
   - Jump to related discussion

3. **Claude Chat Panel**
   - Shows pre-review summary at top (collapsible)
   - Threaded discussion below
   - Context-aware: Claude sees the paper, your annotations, research context

#### 4.2.3 Reading Queue View

**Purpose**: Manage what to read and when.

**Components**:
- **Filter/Sort Bar**: By status, relevance, date added, research question
- **Paper Cards**: Title, authors, Claude's relevance assessment, status badge
- **Drag-to-Reorder**: Manual priority adjustment
- **Bulk Actions**: Archive, change status, assign to research question

**Paper Card Design**:
```
┌────────────────────────────────────────────────────────────────┐
│  [High ↑]  [claude-reviewed]                                   │
│                                                                │
│  Graph Neural Networks with Learnable Structural...            │
│  Dwivedi et al. · ICLR 2022                                   │
│                                                                │
│  Claude: "Directly relevant to your expressiveness work.       │
│  Proposes separating structural and positional encodings..."   │
│                                                                │
│  [Read] [Archive] [⋮]                                          │
└────────────────────────────────────────────────────────────────┘
```

#### 4.2.4 Research Agenda View

**Purpose**: Manage research questions and see emerging patterns.

**Components**:
- **Research Questions**: Active questions with linked papers
- **Patterns**: Claude-identified patterns across reading
- **Synthesis Suggestions**: "These 4 papers might warrant a synthesis note"

#### 4.2.5 Notes Bridge View

**Purpose**: Interface to Obsidian content without replacing Obsidian.

**Components**:
- **Inbox**: Draft notes from Claude awaiting review
- **Recent Notes**: Recently modified notes in vault
- **Search**: Search vault contents
- **Preview**: Read-only preview of notes (edit in Obsidian)

---

## 5. Notification System

### 5.1 Notification Types

| Event | Channel | Urgency |
|-------|---------|---------|
| High-relevance paper added | Push | High |
| Paper review complete | Push | Low |
| Pattern identified | Push | Medium |
| Briefing ready | Push (scheduled) | Low |
| Synthesis suggestion | In-app only | Low |
| Draft note ready | In-app only | Low |

### 5.2 Notification Content

**High-Relevance Paper**:
```
🔬 New paper highly relevant to "GNN Expressiveness"

"Weisfeiler and Leman Go Neural" directly addresses 
the WL hierarchy limitations you noted. Added to top 
of your queue.

[View Paper] [Dismiss]
```

**Pattern Identified**:
```
💡 Pattern spotted across recent reading

3 papers this week all propose attention mechanisms 
for graph pooling. Might be worth a synthesis note?

[See Papers] [Dismiss]
```

**Weekly Briefing**:
```
📚 Your research briefing is ready

5 papers reviewed, 2 high-priority. I have a synthesis 
suggestion for your positional encoding reading.

[Open Briefing]
```

### 5.3 Delivery Configuration

```typescript
interface NotificationPrefs {
  pushEnabled: boolean;
  emailEnabled: boolean;
  emailDigest: "none" | "daily" | "weekly";
  
  // Per-type overrides
  highRelevancePaper: { push: boolean; email: boolean };
  patternIdentified: { push: boolean; email: boolean };
  briefingReady: { push: boolean; email: boolean };
  
  // Quiet hours
  quietHours?: { start: string; end: string; timezone: string };
}
```

---

## 6. Claude Integration Details

### 6.1 Paper Review Prompt Structure

```markdown
You are reviewing an academic paper for a researcher. Your goal is to:
1. Summarize the key contributions
2. Assess relevance to the researcher's active work
3. Identify connections to papers they've already read
4. Generate discussion questions

## Researcher Context
{research_context_summary}

## Active Research Questions
{research_questions}

## Papers in Library (potentially related)
{related_papers_summaries}

## Paper to Review
Title: {title}
Authors: {authors}
Abstract: {abstract}

{pdf_content}

## Your Task
Provide a structured review with:
1. **Summary** (2-3 paragraphs): What does this paper do? What's novel?
2. **Key Contributions** (bullet points): The main takeaways
3. **Relevance Analysis**: How does this connect to the researcher's active questions?
4. **Connections**: Which papers in their library does this relate to, and how?
5. **Discussion Questions**: 2-3 questions to seed collaborative discussion

Be specific and substantive. Reference specific sections, results, or claims.
```

### 6.2 Contextual Chat System Prompt

```markdown
You are collaborating with a researcher on a paper they're reading. You have access to:
- The full paper content
- Your pre-review of the paper
- The researcher's annotations and highlights
- Their research context and active questions
- Your prior discussion about this paper

When they highlight text and ask a question:
- Answer in the context of the specific passage
- Connect to their broader research when relevant
- Reference your pre-review observations if applicable
- Be substantive and specific, not generic

When they want to discuss the paper generally:
- Build on your pre-review
- Ask clarifying questions about their interpretation
- Suggest connections they might not have seen
- Help them articulate their own takeaways
```

### 6.3 Briefing Generation

```markdown
Generate a research briefing for the user based on:

## Current Queue
{queue_papers_with_reviews}

## Recent Reading Activity
{reading_events_last_week}

## Active Research Questions
{research_questions}

## Identified Patterns
{patterns}

## Your Briefing Should Include:
1. **Priority Recommendation**: Which 1-2 papers should they read first, and why?
2. **Queue Assessment**: Any papers that can be deprioritized or archived?
3. **Pattern Observations**: Anything emerging from their recent reading?
4. **Synthesis Opportunities**: Any clusters of papers that warrant a synthesis note?

Keep it concise and actionable. They should be able to read this in 2 minutes.
```

---

## 7. Data Flow Diagrams

### 7.1 Paper Addition Flow

```
User adds paper (URL/PDF)
         │
         ▼
┌─────────────────────┐
│   Paper Service     │
│   - Extract metadata│
│   - Store PDF       │
│   - Create record   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Sync Service      │
│   - Create Notion   │
│     queue entry     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Claude Service    │
│   - Queue review    │
│     operation       │
└─────────┬───────────┘
          │
          ▼ (async)
┌─────────────────────┐
│   Paper Review      │
│   - Fetch context   │
│   - Call Claude API │
│   - Store review    │
│   - Assess priority │
└─────────┬───────────┘
          │
          ├──────────────────────────┐
          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│   Update Notion     │    │   Check Relevance   │
│   with review       │    │   - If high: notify │
└─────────────────────┘    └─────────────────────┘
```

### 7.2 Reading Session Flow

```
User opens paper
         │
         ▼
┌─────────────────────┐
│   Load Paper View   │
│   - PDF content     │
│   - Existing annots │
│   - Claude review   │
│   - Chat history    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Reading/Annotate  │◄────────────────────────┐
│   - Highlight text  │                         │
│   - Add notes       │                         │
└─────────┬───────────┘                         │
          │                                     │
          ▼                                     │
┌─────────────────────┐                         │
│  "Ask Claude"       │                         │
│  (on selection)     │                         │
└─────────┬───────────┘                         │
          │                                     │
          ▼                                     │
┌─────────────────────┐                         │
│   Claude Service    │                         │
│   - Context: paper, │                         │
│     selection,      │                         │
│     annotations,    │                         │
│     research ctx    │                         │
│   - Generate resp   │                         │
└─────────┬───────────┘                         │
          │                                     │
          ▼                                     │
┌─────────────────────┐                         │
│   Display Response  │                         │
│   - Add to thread   │                         │
│   - Link to annot   │─────────────────────────┘
└─────────────────────┘

         │
         ▼ (on session end)
┌─────────────────────┐
│   Update Status     │
│   - Mark as "read"  │
│   - Sync to Notion  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Generate Draft    │
│   Literature Note   │
│   - Write to        │
│     Obsidian inbox  │
└─────────────────────┘
```

---

## 8. Technical Implementation

### 8.1 Technology Stack

**Frontend**:
- React 18+ with TypeScript
- Tailwind CSS for styling
- PDF.js or PSPDFKit for PDF rendering
- Service Workers for offline support
- IndexedDB for local caching

**Backend**:
- Python (FastAPI) or Node.js (Express/Fastify)
- SQLite for MVP, Postgres for scale
- S3-compatible blob storage for PDFs (MinIO for self-hosted)
- Redis for job queue (or simpler in-process queue for MVP)

**Claude Integration**:
- Anthropic API (direct)
- MCP SDK for tool servers

**External Integrations**:
- Notion API
- Git (for Obsidian vault sync)
- alphaxiv API / arXiv API
- Web push (Firebase Cloud Messaging or self-hosted)

### 8.2 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Homelab                                 │
│                                                                 │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │   Traefik   │     │  App Server │     │  Database   │      │
│   │   (proxy)   │────▶│  (API +     │────▶│  (SQLite/   │      │
│   │             │     │   static)   │     │   Postgres) │      │
│   └──────┬──────┘     └─────────────┘     └─────────────┘      │
│          │                   │                                  │
│          │            ┌──────┴──────┐                          │
│          │            ▼             ▼                          │
│          │     ┌───────────┐ ┌───────────┐                     │
│          │     │   MinIO   │ │  Obsidian │                     │
│          │     │   (PDFs)  │ │   Vault   │                     │
│          │     └───────────┘ └───────────┘                     │
│          │                                                      │
└──────────┼──────────────────────────────────────────────────────┘
           │
           │ Cloudflare Tunnel
           │
           ▼
┌─────────────────────┐
│     Internet        │
│   (Mobile access)   │
└─────────────────────┘

External Services:
- Anthropic API (Claude)
- Notion API
- alphaxiv / arXiv
- Push notification service
```

### 8.3 MVP Scope

**Phase 1: Core Reading Loop** (2-3 weeks)
- [ ] Paper ingestion (URL/upload)
- [ ] PDF viewer with basic annotation
- [ ] Claude paper review (async)
- [ ] Simple chat interface
- [ ] Basic queue view
- [ ] Notion sync (queue database)

**Phase 2: Collaboration Features** (2 weeks)
- [ ] Contextual "Ask Claude" on text selection
- [ ] Discussion threads linked to annotations
- [ ] Obsidian draft note generation
- [ ] Mobile-optimized reading view

**Phase 3: Intelligence Layer** (2 weeks)
- [ ] Research context management
- [ ] Priority scoring
- [ ] Pattern detection
- [ ] Briefing generation
- [ ] Push notifications

**Phase 4: Polish** (1-2 weeks)
- [ ] Offline support
- [ ] Performance optimization
- [ ] UI refinements based on usage

---

## 9. Open Questions & Future Considerations

### 9.1 Unresolved Design Questions

1. **Paper deduplication**: How to handle the same paper from different sources (arXiv vs conference version)?

2. **Collaboration expansion**: Could this support multiple researchers? Shared annotations, discussions?

3. **Export/portability**: How to export everything if user wants to leave the system?

4. **Citation integration**: Should we generate BibTeX and integrate with writing tools?

### 9.2 Future Features (Post-MVP)

- Voice notes on annotations (useful for mobile)
- Integration with reference managers beyond Paperpile
- Automated literature search based on research questions
- Writing assistant for synthesis documents
- Integration with arxiv-sanity, Semantic Scholar recommendations
- Collaborative filtering: "Researchers with similar interests read..."

### 9.3 Known Risks

1. **PDF annotation complexity**: High-quality PDF annotation on mobile is hard. May need to use a commercial library (PSPDFKit, PDF.js is limited).

2. **Context window limits**: Papers + annotations + research context can exceed context limits. Need smart truncation/retrieval.

3. **API costs**: Heavy Claude API usage. Need to be smart about what triggers Claude calls.

4. **Sync conflicts**: Notion/Obsidian sync can have conflicts. Need clear conflict resolution.

---

## 10. Success Metrics

### 10.1 Adoption Metrics
- Papers added per week
- Reading sessions per week
- Annotations created per paper
- Chat messages per reading session

### 10.2 Value Metrics
- Time from paper added → read (should decrease)
- Synthesis notes created (should increase)
- Research questions progressed (subjective, periodic check-in)

### 10.3 Quality Metrics
- Relevance score accuracy (user feedback on Claude's assessments)
- Notification usefulness (% acted on vs dismissed)
- Draft note quality (% accepted vs heavily edited)

---

## Appendix A: API Reference

*To be completed during implementation*

## Appendix B: Database Schema

*To be completed during implementation*

## Appendix C: MCP Server Specifications

*To be completed during implementation*
