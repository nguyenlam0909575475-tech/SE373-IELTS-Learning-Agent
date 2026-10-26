"""Configuration settings for SE373 IELTS Learning Agent Backend.

Includes the central switch flag (USE_MOCK_AGENT) to toggle between
Mock Agent (offline / deterministic testing) and Live Agent (real LLM / LangGraph / Committee).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from agent.tools.compute_tool import WORD_PATTERN

# Load .env if present
load_dotenv()

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
EVALS_DIR = ROOT_DIR / "evals"

# ==============================================================================
# Execution Mode: 100% Member 3 Live Agent
# ==============================================================================
# Mock agent has been completely removed.
USE_MOCK_AGENT: bool = False

# Standard regex for word count (harmonized from Member 4 deterministic tool)
WORD_COUNT_REGEX: str = WORD_PATTERN

# API Server settings
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")


def get_mock_mode() -> bool:
    """Return False: mock agent is disabled and removed."""
    return False


def set_mock_mode(enabled: bool) -> None:
    """Mock agent is disabled. This is a no-op."""
    pass
