"""Background task worker for async operations."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Coroutine

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.async_operation import AsyncOperation, OperationStatus, OperationType

logger = logging.getLogger(__name__)


class TaskWorker:
    """Background task worker that processes async operations."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self._handlers: dict[OperationType, Callable] = {}

    def register_handler(
        self,
        operation_type: OperationType,
        handler: Callable[[AsyncSession, dict], Coroutine[Any, Any, dict]],
    ):
        """Register a handler for an operation type."""
        self._handlers[operation_type] = handler

    async def start(self):
        """Start the background worker."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Task worker started")

    async def stop(self):
        """Stop the background worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Task worker stopped")

    async def _run_loop(self):
        """Main worker loop."""
        while self._running:
            try:
                await self._process_pending_operations()
            except Exception as e:
                logger.error(f"Error in task worker: {e}")

            # Wait before checking for more tasks
            await asyncio.sleep(2)

    async def _process_pending_operations(self):
        """Process all pending operations."""
        async with async_session_maker() as session:
            # Get pending operations
            result = await session.execute(
                select(AsyncOperation)
                .where(AsyncOperation.status == OperationStatus.QUEUED)
                .order_by(AsyncOperation.created_at)
                .limit(5)
            )
            operations = list(result.scalars().all())

            for operation in operations:
                await self._process_operation(session, operation)

    async def _process_operation(self, session: AsyncSession, operation: AsyncOperation):
        """Process a single operation."""
        handler = self._handlers.get(operation.type)
        if not handler:
            logger.warning(f"No handler for operation type: {operation.type}")
            return

        try:
            # Update status to running
            operation.status = OperationStatus.RUNNING
            operation.started_at = datetime.utcnow()
            await session.commit()

            # Execute the handler
            logger.info(f"Processing operation {operation.id} ({operation.type.value})")
            result = await handler(session, operation.input_data)

            # Update with success
            operation.status = OperationStatus.COMPLETED
            operation.output_data = result
            operation.completed_at = datetime.utcnow()
            await session.commit()

            logger.info(f"Operation {operation.id} completed successfully")

        except Exception as e:
            logger.error(f"Operation {operation.id} failed: {e}")

            # Update with failure
            operation.status = OperationStatus.FAILED
            operation.error_message = str(e)[:1000]
            operation.completed_at = datetime.utcnow()
            await session.commit()


# Global worker instance
task_worker = TaskWorker()


async def setup_task_handlers():
    """Set up handlers for all operation types."""
    from app.services.claude_service import ClaudeService
    from app.services.research_context_service import ResearchContextService

    async def handle_paper_review(session: AsyncSession, input_data: dict) -> dict:
        """Handle paper review operation."""
        claude_service = ClaudeService(session)
        paper_id = input_data.get("paper_id")
        user_id = input_data.get("user_id", "default_user")

        if not paper_id:
            raise ValueError("paper_id is required")

        return await claude_service.execute_paper_review(paper_id, user_id)

    async def handle_pattern_analysis(session: AsyncSession, input_data: dict) -> dict:
        """Handle pattern analysis operation."""
        from app.models.paper import Paper, PaperStatus
        from anthropic import AsyncAnthropic
        from app.core.config import settings
        import json

        user_id = input_data.get("user_id", "default_user")

        # Get reading history
        context_service = ResearchContextService(session)
        reading_events = await context_service.get_reading_history(user_id, limit=30)

        if len(reading_events) < 3:
            return {"patterns": [], "message": "Not enough reading history for pattern analysis"}

        # Get papers from reading history
        paper_ids = list(set(e.paper_id for e in reading_events))
        result = await session.execute(
            select(Paper).where(Paper.id.in_(paper_ids))
        )
        papers = list(result.scalars().all())

        if len(papers) < 3:
            return {"patterns": [], "message": "Not enough papers for pattern analysis"}

        # Get research context
        context_summary = await context_service.get_context_summary(user_id)

        # Build prompt for Claude
        paper_summaries = []
        for p in papers:
            summary = f"- {p.title}"
            if p.claude_review:
                summary += f"\n  Summary: {p.claude_review.get('summary', '')[:300]}"
                if p.claude_review.get('key_contributions'):
                    summary += f"\n  Key points: {', '.join(p.claude_review.get('key_contributions', [])[:3])}"
            paper_summaries.append(summary)

        prompt = f"""Analyze the following papers from a researcher's reading history and identify any emerging patterns, themes, or connections.

## Research Context
{context_summary}

## Recent Papers Read
{chr(10).join(paper_summaries)}

## Your Task
Identify 1-3 meaningful patterns across these papers. For each pattern, provide:
1. A clear description of the pattern or theme
2. Which papers relate to this pattern

Respond in JSON format:
{{
    "patterns": [
        {{
            "description": "Description of the pattern",
            "paper_titles": ["Paper 1 title", "Paper 2 title"]
        }}
    ]
}}

Focus on substantive intellectual connections, not superficial similarities."""

        # Call Claude API
        if not settings.anthropic_api_key:
            return {"patterns": [], "message": "Claude API not configured"}

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = response.content[0].text
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(response_text[start:end])
                patterns_data = data.get("patterns", [])

                # Create patterns in database
                created_patterns = []
                for pattern_info in patterns_data[:3]:  # Limit to 3 patterns
                    # Find paper IDs from titles
                    pattern_paper_ids = []
                    for title in pattern_info.get("paper_titles", []):
                        for p in papers:
                            if title.lower() in p.title.lower():
                                pattern_paper_ids.append(p.id)
                                break

                    pattern = await context_service.create_pattern(
                        user_id=user_id,
                        description=pattern_info.get("description", ""),
                        paper_ids=pattern_paper_ids,
                    )
                    created_patterns.append({
                        "id": pattern.id,
                        "description": pattern.description,
                    })

                return {
                    "patterns": created_patterns,
                    "message": f"Identified {len(created_patterns)} patterns",
                }
        except json.JSONDecodeError:
            pass

        return {"patterns": [], "message": "Could not parse pattern analysis"}

    async def handle_briefing_generation(session: AsyncSession, input_data: dict) -> dict:
        """Handle briefing generation operation."""
        claude_service = ClaudeService(session)
        user_id = input_data.get("user_id", "default_user")

        return await claude_service.generate_briefing(user_id)

    async def handle_synthesis_draft(session: AsyncSession, input_data: dict) -> dict:
        """Handle synthesis draft generation."""
        # Placeholder for synthesis draft generation
        return {"draft": "", "message": "Synthesis draft generation not yet implemented"}

    # Register handlers
    task_worker.register_handler(OperationType.PAPER_REVIEW, handle_paper_review)
    task_worker.register_handler(OperationType.PATTERN_ANALYSIS, handle_pattern_analysis)
    task_worker.register_handler(OperationType.BRIEFING_GENERATION, handle_briefing_generation)
    task_worker.register_handler(OperationType.SYNTHESIS_DRAFT, handle_synthesis_draft)
