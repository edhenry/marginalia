"""Service layer for Claude AI integration."""

import uuid
from datetime import datetime
from typing import Any

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.async_operation import AsyncOperation, OperationStatus, OperationType
from app.models.chat import ChatMessage, ChatThread
from app.models.paper import Paper, PaperStatus
from app.services.research_context_service import ResearchContextService


class ClaudeService:
    """Service for Claude AI operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self.model = settings.claude_model

    async def queue_paper_review(self, paper_id: str, user_id: str) -> AsyncOperation:
        """Queue a paper for Claude review."""
        operation = AsyncOperation(
            id=str(uuid.uuid4()),
            type=OperationType.PAPER_REVIEW,
            input_data={"paper_id": paper_id, "user_id": user_id},
        )
        self.session.add(operation)

        # Update paper status
        result = await self.session.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()
        if paper:
            paper.status = PaperStatus.PROCESSING

        await self.session.flush()
        return operation

    async def execute_paper_review(self, paper_id: str, user_id: str) -> dict[str, Any]:
        """Execute a paper review (called by background worker)."""
        if not self.client:
            return {"error": "Claude API not configured"}

        # Get paper
        result = await self.session.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        # Get research context
        context_service = ResearchContextService(self.session)
        context_summary = await context_service.get_context_summary(user_id)

        # Build prompt
        prompt = self._build_review_prompt(paper, context_summary)

        # Call Claude API
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response and structure review
        review = self._parse_review_response(response.content[0].text)

        # Update paper with review
        paper.claude_review = review
        paper.status = PaperStatus.CLAUDE_REVIEWED
        paper.relevance_score = review.get("relevance_score", 0.5)
        paper.relevance_reason = review.get("relevance_analysis", "")

        await self.session.flush()
        return review

    async def chat(
        self,
        thread_id: str,
        message: str,
        user_id: str,
    ) -> ChatMessage:
        """Send a message in a chat thread and get Claude's response."""
        # Get thread
        result = await self.session.execute(
            select(ChatThread).where(ChatThread.id == thread_id)
        )
        thread = result.scalar_one_or_none()
        if not thread:
            raise ValueError("Thread not found")

        # Save user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            role="user",
            content=message,
        )
        self.session.add(user_message)

        # Build context for Claude
        context = await self._build_chat_context(thread, user_id)

        # Get conversation history
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at)
        )
        history = list(result.scalars().all())

        # Build messages for API
        messages = []
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})

        # Call Claude API
        if self.client:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=context,
                messages=messages,
            )
            assistant_content = response.content[0].text
        else:
            assistant_content = "[Claude API not configured] This is a placeholder response."

        # Save assistant message
        assistant_message = ChatMessage(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            role="assistant",
            content=assistant_content,
        )
        self.session.add(assistant_message)
        await self.session.flush()

        return assistant_message

    async def create_thread(
        self,
        context_type: str,
        paper_id: str | None = None,
        question_id: str | None = None,
        synthesis_scope: list[str] | None = None,
    ) -> ChatThread:
        """Create a new chat thread."""
        thread = ChatThread(
            id=str(uuid.uuid4()),
            context_type=context_type,
            paper_id=paper_id,
            question_id=question_id,
            synthesis_scope=synthesis_scope,
        )
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def get_thread(self, thread_id: str) -> ChatThread | None:
        """Get a chat thread with messages."""
        result = await self.session.execute(
            select(ChatThread).where(ChatThread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def queue_pattern_analysis(self, user_id: str) -> AsyncOperation:
        """Queue a pattern analysis operation."""
        operation = AsyncOperation(
            id=str(uuid.uuid4()),
            type=OperationType.PATTERN_ANALYSIS,
            input_data={"user_id": user_id},
        )
        self.session.add(operation)
        await self.session.flush()
        return operation

    async def queue_briefing_generation(self, user_id: str) -> AsyncOperation:
        """Queue a briefing generation operation."""
        operation = AsyncOperation(
            id=str(uuid.uuid4()),
            type=OperationType.BRIEFING_GENERATION,
            input_data={"user_id": user_id},
        )
        self.session.add(operation)
        await self.session.flush()
        return operation

    async def generate_briefing(self, user_id: str) -> dict[str, Any]:
        """Generate a research briefing."""
        if not self.client:
            return {"error": "Claude API not configured"}

        # Get context and papers
        context_service = ResearchContextService(self.session)
        context_summary = await context_service.get_context_summary(user_id)

        # Get queue papers
        result = await self.session.execute(
            select(Paper)
            .where(Paper.status.in_([PaperStatus.NEW, PaperStatus.CLAUDE_REVIEWED, PaperStatus.READING]))
            .order_by(Paper.priority.desc())
            .limit(10)
        )
        papers = list(result.scalars().all())

        # Build prompt
        prompt = self._build_briefing_prompt(papers, context_summary)

        # Call Claude
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "briefing": response.content[0].text,
            "generated_at": datetime.utcnow().isoformat(),
            "paper_count": len(papers),
        }

    def _build_review_prompt(self, paper: Paper, context_summary: str) -> str:
        """Build the prompt for paper review."""
        return f"""You are reviewing an academic paper for a researcher. Your goal is to:
1. Summarize the key contributions
2. Assess relevance to the researcher's active work
3. Identify connections to papers they've already read
4. Generate discussion questions

## Researcher Context
{context_summary}

## Paper to Review
Title: {paper.title}
Authors: {', '.join(paper.authors)}
Year: {paper.year or 'Unknown'}
Venue: {paper.venue or 'Unknown'}
Abstract: {paper.abstract or 'Not available'}

## Your Task
Provide a structured review in JSON format with these fields:
- "summary": 2-3 paragraph summary of what the paper does and what's novel
- "key_contributions": array of bullet points with main takeaways
- "methodology": brief description of the approach
- "relevance_analysis": how this connects to the researcher's active questions
- "relevance_score": number 0-1 indicating relevance to their research
- "connections": array of related topics/papers
- "suggested_tags": array of topic tags
- "discussion_questions": 2-3 questions to seed collaborative discussion

Be specific and substantive. Reference specific sections, results, or claims where possible."""

    def _parse_review_response(self, response_text: str) -> dict[str, Any]:
        """Parse Claude's review response into structured format."""
        import json

        # Try to parse as JSON
        try:
            # Find JSON in the response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

        # Fallback: return raw text as summary
        return {
            "summary": response_text,
            "key_contributions": [],
            "methodology": None,
            "relevance_analysis": "",
            "relevance_score": 0.5,
            "connections": [],
            "suggested_tags": [],
            "discussion_questions": [],
            "reviewed_at": datetime.utcnow().isoformat(),
        }

    async def _build_chat_context(self, thread: ChatThread, user_id: str) -> str:
        """Build system context for chat."""
        context_parts = [
            "You are collaborating with a researcher on their work.",
            "Be substantive, specific, and helpful.",
        ]

        # Add paper context if applicable
        if thread.paper_id:
            result = await self.session.execute(
                select(Paper).where(Paper.id == thread.paper_id)
            )
            paper = result.scalar_one_or_none()
            if paper:
                context_parts.append(f"\nYou are discussing the paper: {paper.title}")
                if paper.claude_review:
                    context_parts.append(f"\nYour earlier review summary: {paper.claude_review.get('summary', '')}")

        # Add research context
        context_service = ResearchContextService(self.session)
        research_context = await context_service.get_context_summary(user_id)
        context_parts.append(f"\n\nResearcher Context:\n{research_context}")

        return "\n".join(context_parts)

    def _build_briefing_prompt(self, papers: list[Paper], context_summary: str) -> str:
        """Build the prompt for briefing generation."""
        paper_list = "\n".join([
            f"- {p.title} (Priority: {p.priority}, Status: {p.status.value})"
            + (f"\n  Review: {p.claude_review.get('summary', '')[:200]}..." if p.claude_review else "")
            for p in papers
        ])

        return f"""Generate a research briefing for the user based on:

## Current Queue
{paper_list}

## Research Context
{context_summary}

## Your Briefing Should Include:
1. **Priority Recommendation**: Which 1-2 papers should they read first, and why?
2. **Queue Assessment**: Any papers that can be deprioritized or archived?
3. **Pattern Observations**: Anything emerging from their reading list?
4. **Synthesis Opportunities**: Any clusters of papers that warrant a synthesis note?

Keep it concise and actionable. They should be able to read this in 2 minutes."""
