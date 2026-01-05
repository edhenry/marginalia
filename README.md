# Marginalia

A collaborative research workflow system that positions Claude as an active research partner. Marginalia handles administrative overhead (paper tracking, queue management, note generation, context maintenance) while surfacing what requires human attention.

## Features

- **Paper Management**: Import papers from arXiv or upload PDFs directly
- **Claude Reviews**: Automatic paper analysis with summaries, key contributions, and relevance scoring
- **Interactive Reading**: PDF viewer with annotations, highlights, and contextual chat
- **Research Context**: Track research questions and let Claude identify patterns across your reading
- **Briefings**: Generate prioritized reading recommendations based on your research agenda
- **Integrations**: Sync with Notion and save literature notes to Obsidian

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The application will be available at `http://localhost:5173`.

## Configuration

Create a `.env` file in the `backend` directory:

```env
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Optional - Notion Integration
NOTION_API_KEY=your-notion-api-key
NOTION_QUEUE_DATABASE_ID=your-database-id

# Optional - Obsidian Integration
OBSIDIAN_VAULT_PATH=/path/to/your/vault
OBSIDIAN_INBOX_FOLDER=inbox
OBSIDIAN_CONCEPTS_FOLDER=concepts

# Optional - Customization
CLAUDE_MODEL=claude-sonnet-4-20250514
DATABASE_URL=sqlite+aiosqlite:///./marginalia.db
```

## Usage

### Adding Papers

1. **From arXiv**: Click "Add Paper" in the Queue, enter an arXiv ID (e.g., `2301.00001`), and the paper will be imported with its PDF
2. **Upload PDF**: Click "Add Paper", switch to "Upload PDF" tab, and upload a PDF with metadata

### Reading Papers

1. Open a paper from the Queue or Dashboard
2. Read the PDF with Claude's review summary in the side panel
3. Select text to highlight, add notes, or ask Claude questions
4. Use the chat tab for deeper discussions about the paper

### Research Questions

1. Go to Research Agenda
2. Add questions that guide your research
3. Claude will consider these when reviewing papers and identifying patterns

### Generating Briefings

Click "Generate Briefing" on the Dashboard to get Claude's recommendations on what to read next based on your queue and research context.

## Architecture

```
marginalia/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/routes/     # API endpoints
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── core/           # Config and database
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── package.json
└── specification.md        # Full system specification
```

## API Endpoints

### Papers
- `GET /api/v1/papers` - List papers
- `POST /api/v1/papers` - Create paper
- `POST /api/v1/papers/upload` - Upload paper with PDF
- `GET /api/v1/papers/queue` - Get prioritized queue
- `GET /api/v1/papers/{id}` - Get paper details
- `GET /api/v1/papers/{id}/pdf` - Get paper PDF
- `POST /api/v1/papers/{id}/annotations` - Create annotation

### Research Context
- `GET /api/v1/context` - Get research context
- `GET /api/v1/context/questions` - List research questions
- `POST /api/v1/context/questions` - Create research question
- `GET /api/v1/context/patterns` - Get identified patterns
- `POST /api/v1/context/analyze` - Trigger pattern analysis
- `POST /api/v1/context/briefing` - Generate briefing

### Chat
- `POST /api/v1/chat/threads` - Create chat thread
- `GET /api/v1/chat/threads/{id}` - Get thread with messages
- `POST /api/v1/chat/threads/{id}/messages` - Send message

### Sync
- `POST /api/v1/sync/arxiv/import` - Import from arXiv
- `POST /api/v1/sync/notion/paper/{id}` - Sync paper to Notion
- `POST /api/v1/sync/obsidian/literature-note/{id}` - Save literature note

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Database Migrations

The database is automatically created on first run. For schema changes, delete `marginalia.db` and restart the server.

## License

MIT
