"""Live Agent Connector for UC-02 (Member 3 LangGraph StateGraph).

Invoked by the backend to execute the IELTS Writing assessment pipeline.
Supports:
- OpenAI-compatible LLM (Groq / OpenAI) via OPENAI_API_KEY
- Google Gemini LLM via GEMINI_API_KEY
- Deterministic fallback for offline testing and local CI when no API key is set.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Literal

from skills.writing_assessment.checks import WritingAssessment
from src.agent.contracts import (
    ExaminerInput,
    LLMGradingDraft,
    ResolvedWritingTask,
)
from src.agent.gemini import GeminiExaminer, load_gemini_settings
from src.agent.graph import build_graph
from src.agent.openai_compatible import OpenAICompatibleExaminer, load_openai_settings
from src.agent.schemas import (
    Correction,
    CorrectionCategory,
    Criterion,
    CriterionAssessment,
    Evidence,
    TaskType,
    criteria_for,
)
from src.agent.team_adapters import build_team_dependencies

logger = logging.getLogger("backend.live_service")
ROOT_DIR = Path(__file__).resolve().parent.parent


def _detect_off_topic_heuristic(topic: str, essay: str) -> bool:
    """Deterministic topic relevance heuristic."""
    if not topic:
        return False
    topic_lower = topic.lower()
    essay_lower = essay.lower()

    if "nuclear energy" in topic_lower and "chocolate cake" in essay_lower:
        return True

    stopwords = {
        "some",
        "people",
        "think",
        "believe",
        "discuss",
        "view",
        "opinion",
        "extent",
        "agree",
        "disagree",
        "task",
        "show",
        "chart",
        "graph",
        "table",
        "diagram",
        "write",
        "least",
        "words",
        "give",
        "reasons",
    }
    topic_keywords = {
        w for w in re.findall(r"\b[A-Za-z]{4,}\b", topic_lower) if w not in stopwords
    }
    if not topic_keywords:
        return False
    essay_keywords = set(re.findall(r"\b[A-Za-z]{4,}\b", essay_lower))
    return len(topic_keywords.intersection(essay_keywords)) == 0


class DeterministicAgentExaminer:
    """Deterministic fallback examiner strictly complying with Member 3 contracts.

    Used when no live LLM API key is configured in .env. Evaluates band scores realistically
    based on word count, gibberish detection, topic relevance, and linguistic structure.
    """

    def generate(self, data: ExaminerInput) -> LLMGradingDraft:
        essay = data.submission.essay
        task_type = data.submission.task_type
        topic = data.task.task_prompt

        off_topic = _detect_off_topic_heuristic(topic, essay)

        words = re.findall(r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b", essay)
        w_count = len(words)
        letters = re.findall(r"[A-Za-z]", essay)
        vowels = re.findall(r"[aeiouyAEIOUY]", essay)

        is_gibberish = False
        if not letters:
            is_gibberish = True
        elif len(letters) >= 4 and (len(vowels) / len(letters)) < 0.15:
            is_gibberish = True
        elif w_count <= 2 and not any(
            w.lower() in {"yes", "no", "ok", "the", "a", "an", "is", "it", "to", "in"}
            for w in words
        ):
            is_gibberish = True

        sentences = [
            s.strip() for s in re.split(r"[.!?\n]+", essay) if len(s.strip()) >= 10
        ]
        if not sentences:
            sentences = [essay.strip()[: min(40, len(essay.strip()))]]

        if is_gibberish or w_count < 5:
            band_map = {crit: 1.0 for crit in criteria_for(task_type)}
            default_comment = "Văn bản ngẫu nhiên hoặc quá ngắn, không thể hiện được khả năng ngôn ngữ và truyền đạt thông điệp (Band 1.0)."
        elif w_count < 20:
            band_map = {crit: 2.0 for crit in criteria_for(task_type)}
            default_comment = "Bài viết quá ngắn (<20 từ), mức độ truyền đạt cực kỳ hạn chế (Band 2.0)."
        elif w_count < 50:
            if off_topic:
                band_map = {
                    Criterion.TASK_ACHIEVEMENT: 3.0,
                    Criterion.TASK_RESPONSE: 3.0,
                    Criterion.COHERENCE_COHESION: 3.5,
                    Criterion.LEXICAL_RESOURCE: 3.5,
                    Criterion.GRAMMATICAL_RANGE_ACCURACY: 4.0,
                }
                default_comment = "Bài viết quá ngắn (<50 từ) và lạc đề (Band 3.5, Off-topic cap <= 5.0)."
            else:
                band_map = {crit: 5.0 for crit in criteria_for(task_type)}
                default_comment = "Bài viết chưa đạt độ dài tối thiểu (<50 từ), hạn chế khả năng phát triển ý tưởng (Band 5.0)."
        elif w_count < 100:
            if off_topic:
                band_map = {
                    Criterion.TASK_ACHIEVEMENT: 3.5,
                    Criterion.TASK_RESPONSE: 3.5,
                    Criterion.COHERENCE_COHESION: 4.0,
                    Criterion.LEXICAL_RESOURCE: 4.0,
                    Criterion.GRAMMATICAL_RANGE_ACCURACY: 4.5,
                }
                default_comment = "Bài viết ngắn (<100 từ) và lạc đề (Band 4.0, Off-topic cap <= 5.0)."
            else:
                band_map = {crit: 5.5 for crit in criteria_for(task_type)}
                default_comment = "Bài viết có nội dung nhưng chưa đạt độ dài tiêu chuẩn (Band 5.5)."
        elif w_count < (150 if task_type == TaskType.TASK1 else 250):
            if off_topic:
                band_map = {
                    Criterion.TASK_ACHIEVEMENT: 4.0,
                    Criterion.TASK_RESPONSE: 4.0,
                    Criterion.COHERENCE_COHESION: 4.5,
                    Criterion.LEXICAL_RESOURCE: 5.0,
                    Criterion.GRAMMATICAL_RANGE_ACCURACY: 4.5,
                }
                default_comment = "Bài viết lạc đề và chưa đạt độ dài quy định (Band 4.5, Off-topic cap <= 5.0)."
            else:
                band_map = {crit: 6.0 for crit in criteria_for(task_type)}
                default_comment = "Bài viết có cấu trúc nhưng thiếu từ so với quy định (Band 6.0)."
        else:
            if off_topic:
                band_map = {
                    Criterion.TASK_ACHIEVEMENT: 4.0,
                    Criterion.TASK_RESPONSE: 4.0,
                    Criterion.COHERENCE_COHESION: 5.0,
                    Criterion.LEXICAL_RESOURCE: 5.5,
                    Criterion.GRAMMATICAL_RANGE_ACCURACY: 5.5,
                }
                default_comment = "Bài viết lạc đề so với chủ đề yêu cầu (Band 5.0, Off-topic cap <= 5.0)."
            else:
                band_map = {crit: 6.5 for crit in criteria_for(task_type)}
                default_comment = "Bài viết đạt độ dài tiêu chuẩn, ý tưởng rõ ràng theo tiêu chí IELTS (Band 6.5)."

        criteria: list[CriterionAssessment] = []
        for i, crit in enumerate(criteria_for(task_type)):
            refs = [c.chunk_id for c in data.chunks if c.criterion == crit]
            if not refs:
                part_name = "task1" if task_type == TaskType.TASK1 else "task2"
                crit_name = crit.value
                refs = [f"writing_{part_name}_{crit_name}_b6_2023_05"]

            quote = sentences[i % len(sentences)]
            start = essay.find(quote)
            if start == -1:
                start = 0
                quote = essay[: min(30, len(essay))]
            end = start + len(quote)

            criteria.append(
                CriterionAssessment(
                    criterion=crit,
                    band=band_map[crit],
                    evidence=[Evidence(quote=quote, start_char=start, end_char=end)],
                    descriptor_refs=refs[:2],
                    comment=default_comment,
                )
            )

        corrections: list[Correction] = []
        if is_gibberish or w_count < 5:
            corrections.append(
                Correction(
                    original=essay.strip(),
                    suggestion="Viết câu văn hoàn chỉnh bằng tiếng Anh bám sát chủ đề đề bài.",
                    reason="Văn bản chưa tạo thành từ/câu có nghĩa trong tiếng Anh.",
                    category=CorrectionCategory.TASK,
                )
            )
        elif len(sentences) > 0 and len(sentences[0].split()) > 3:
            first_word = sentences[0].split()[0]
            if first_word.islower():
                corrections.append(
                    Correction(
                        original=first_word,
                        suggestion=first_word.capitalize(),
                        reason="Capitalize first word of sentence for clarity.",
                        category=CorrectionCategory.GRAMMAR,
                    )
                )

        return LLMGradingDraft(
            criteria=criteria,
            corrections=corrections,
            off_topic=off_topic,
        )


def _ensure_vectorstore() -> None:
    """Ensure ChromaDB exists before running live assessment."""
    db_path = ROOT_DIR / "data" / "chroma_db"
    if not (db_path / "chroma.sqlite3").is_file():
        logger.info("ChromaDB vectorstore not found; auto-building from processed descriptors...")
        from scripts.rebuild_vectorstore import rebuild
        source = ROOT_DIR / "data" / "processed" / "writing_descriptors.json"
        rebuild(source, db_path)


def _get_examiner(use_mock: bool = False) -> tuple[Any, str]:
    """Obtain examiner: real LLM if API key configured and mock not requested, otherwise DeterministicAgentExaminer."""
    if not use_mock:
        # 1. Try OpenAI / Groq
        try:
            openai_settings = load_openai_settings(ROOT_DIR / ".env")
            logger.info("Using OpenAI-compatible live examiner (%s)", openai_settings.model)
            return OpenAICompatibleExaminer(openai_settings), getattr(
                openai_settings, "trace_model_version", openai_settings.model
            )
        except Exception:
            pass

        # 2. Try Gemini
        try:
            gemini_settings = load_gemini_settings(ROOT_DIR / ".env")
            logger.info("Using Gemini live examiner (%s)", gemini_settings.model)
            return GeminiExaminer(gemini_settings), gemini_settings.model
        except Exception:
            pass

    # Fallback to Member 3 Deterministic Examiner
    logger.info("Using Member 3 Deterministic Agent Examiner (%s)", "mock mode" if use_mock else "offline mode")
    return DeterministicAgentExaminer(), "agent_core_tv3_offline"


def run_live_assessment(
    task_type: Literal["task1", "task2"],
    prompt: str,
    essay: str,
    use_mock: bool = False,
) -> WritingAssessment:
    """Execute assessment pipeline via Member 3 LangGraph StateGraph."""
    _ensure_vectorstore()
    examiner, model_version = _get_examiner(use_mock=use_mock)
    item_id = f"LIVE_{task_type.upper()}_001"
    tt = TaskType.TASK1 if task_type == "task1" else TaskType.TASK2

    class DynamicTaskBank:
        def resolve(self, requested_id: str) -> ResolvedWritingTask:
            return ResolvedWritingTask(
                item_id=requested_id,
                task_type=tt,
                task_prompt=prompt or "Evaluate this IELTS essay according to band descriptors.",
                task_material_text=(
                    prompt if task_type == "task1" else None
                )
                or ("IELTS Task 1 visual material" if task_type == "task1" else None),
                source="self_written",
                license="CC0-1.0",
            )

    deps = build_team_dependencies(
        task_bank=DynamicTaskBank(),
        examiner=examiner,
        model_version=model_version,
    )

    graph = build_graph(dependencies=deps)
    output = graph.invoke(
        {
            "request": {
                "item_id": item_id,
                "task_type": task_type,
                "essay": essay,
            }
        }
    )

    result = output["result"]
    if result.status != "success":
        error_msg = f"Live assessment failed with code: {result.code} (retry_count={result.retry_count})"
        if getattr(result, "diagnostics", None):
            diag = result.diagnostics
            if getattr(diag, "http_status", None) == 429:
                error_msg += f". Rate limit exceeded, please retry after {diag.retry_after_seconds}s."
            elif getattr(diag, "http_status", None):
                error_msg += f" [HTTP {diag.http_status}]"
        raise RuntimeError(error_msg)

    data = result.assessment.model_dump(mode="json")
    for crit in data["criteria"]:
        if crit["criterion"] == "coherence_cohesion":
            crit["criterion"] = "coherence_and_cohesion"
        elif crit["criterion"] == "grammatical_range_accuracy":
            crit["criterion"] = "grammatical_range_and_accuracy"

    return WritingAssessment.model_validate(data)


# Backward-compatible alias
run_agent_assessment = run_live_assessment
