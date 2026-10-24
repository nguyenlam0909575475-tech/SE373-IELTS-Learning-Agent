"""Live Agent Connector for UC-02.

Invoked when USE_MOCK_AGENT is False. Integrates with the LangGraph StateGraph,
the Dual-Examiner Committee, or the LangSmith tracing harness.
"""

from __future__ import annotations

import logging
from typing import Literal

from skills.writing_assessment.checks import WritingAssessment

logger = logging.getLogger("backend.live_service")


def run_live_assessment(
    task_type: Literal["task1", "task2"],
    prompt: str,
    essay: str,
) -> WritingAssessment:
    """Execute live assessment pipeline via agent core / committee.

    Raises:
        NotImplementedError: If the live LLM agent loop is not yet connected.
        RuntimeError: If LLM API keys or dependencies are missing.
    """
    try:
        # Check if agent.core.loop or agent.core.committee has live implementation
        from agent.core import committee

        if hasattr(committee, "run_committee_assessment"):
            logger.info("Attempting to run committee assessment...")
            # Note: requires examiner_a_fn and examiner_b_fn implementations
            raise NotImplementedError(
                "Live LLM Examiner agents (Examiner A & B) are pending LLM API keys and model initialization. "
                "Switch to Mock Mode (USE_MOCK_AGENT=true or click the Mock switch on UI) to test the complete application."
            )
        else:
            raise NotImplementedError("Live agent loop is not yet fully initialized.")

    except ImportError as err:
        raise NotImplementedError(
            f"Live agent dependencies could not be imported: {err}. "
            "Ensure packages in requirements.txt are installed."
        ) from err
