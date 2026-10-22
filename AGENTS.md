# AGENTS & HARNESS SPECIFICATION

This document outlines the Multi-Agent architecture, specialized Agent roles, and the Harness verification layer for the **SE373 IELTS Learning Agent** system.

---

## 1. Multi-Agent Ecosystem Overview

The system is designed around specialized single-purpose agents coordinated through deterministic workflows (LangGraph):

| Agent Name | Owned Use Case | Primary Responsibility | Input Context |
| :--- | :--- | :--- | :--- |
| **Examiner A** | UC-02, UC-07 | First independent evaluator for Writing Task 1/2. | Delimited student essay, RAG descriptors, linguistic metrics. |
| **Examiner B** | UC-02, UC-07 | Second independent evaluator for Writing Task 1/2. | Isolated input identical to Examiner A (never receives Examiner A's output). |
| **Moderator Agent** | UC-07 | Reconciles discrepancies when divergence exceeds threshold. | Both examiners' assessments, cited quotes, and essay context. |
| **Practice Generator** | UC-04 | Generates Reading passages & Listening scripts with 2-layer validator. | CEFR level target, topic bank, question types. |
| **Study Plan & Memory Agent**| UC-05 | Tracks learner weakness memory and dynamically updates study roadmap. | Learner attempt history, skill gap profiles. |
| **Progress & HITL Agent** | UC-10 | Generates weekly progress report and submits for Teacher approval. | Aggregated learner metrics, teacher feedback queue. |

---

## 2. Harness Verification Layer (Defense-in-Depth)

The intelligence of the system relies on the **Harness layer** rather than raw LLM generation:

```
[Raw Student Input]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ 1. Security & Sanitization                             │
│    - Encapsulate in `<student_essay>` delimiters       │
│    - Detect prompt injection / instruction override    │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 2. Deterministic Tools                                 │
│    - count_words (exact word count)                    │
│    - check_plagiarism (against sample corpus)          │
│    - retrieve_descriptors (RAG chunk retrieval)        │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 3. LLM Structured Assessment                           │
│    - Criterion scoring with verbatim quote citations   │
│    - RAG descriptor references                         │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 4. Deterministic Skill Checks (checks.py)              │
│    - Validate schema (Pydantic v2)                     │
│    - Code-calculated overall band (IELTS rounding)     │
│    - 100% Verbatim quote & [start_char:end_char] match │
│    - Verify descriptor_refs belong to retrieved chunks │
│    - Penalty enforcement (under_length, off_topic)     │
│    - Mandatory AI estimation disclaimer                │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
            [Validated Assessment / Self-Correction Retry]
```

---

## 3. Committee Workflow & Divergence Protocol (UC-07)

1. **Independent Evaluation:** Examiner A and Examiner B grade the essay simultaneously with isolated context.
2. **Divergence Calculation:**
   $$\Delta_{\text{overall}} = |\text{Overall}_A - \text{Overall}_B|$$
   $$\Delta_{\text{crit}} = \max_{c \in \text{Criteria}} |\text{Band}_A(c) - \text{Band}_B(c)|$$
3. **Trigger Criteria:**
   - Moderator is invoked **if and only if**:
     - $\Delta_{\text{overall}} > 0.5$, OR
     - $\Delta_{\text{crit}} \ge 1.0$, OR
     - Disagreement on `off_topic` status.
4. **Moderator Invariants:**
   - Final band must fall within $[\min(A, B), \max(A, B)]$ unless an explicit `out_of_bounds_justification` is provided.
   - Must cite at least one verbatim evidence quote originating from Examiner A or B.
   - Any unresolved conflict regarding `off_topic` automatically flags `needs_teacher_review = True`.

---

## 4. Security & Compliance Guidelines

- **Anti-Prompt Injection:** Any attempt by student input to dictate scores or change examiner personas triggers the `"injection_detected"` flag and is ignored.
- **AI Estimation Disclaimer:** All outputs explicitly state:
  > *"Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức."*
- **No Direct LLM Math:** Numerical metrics (word count, overall band rounding) must be computed in deterministic code, never generated freehand by LLMs.
