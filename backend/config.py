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
# SWITCH FLAG: Mock vs. Live Agent
# ==============================================================================
# Set USE_MOCK_AGENT=true to run in fast, offline, deterministic mock mode.
# Set USE_MOCK_AGENT=false to run in live agent mode (calls real LLM / LangGraph pipeline).
USE_MOCK_AGENT: bool = os.getenv("USE_MOCK_AGENT", "true").lower() in ("true", "1", "yes")

# Standard regex for word count (harmonized from Member 4 deterministic tool)
WORD_COUNT_REGEX: str = WORD_PATTERN

# API Server settings
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")


def get_mock_mode() -> bool:
    """Return the current global mock mode state."""
    return USE_MOCK_AGENT


def set_mock_mode(enabled: bool) -> None:
    """Dynamically toggle the global mock mode at runtime."""
    global USE_MOCK_AGENT
    USE_MOCK_AGENT = enabled
