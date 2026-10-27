"""FastAPI Application for SE373 IELTS Learning Agent (UC-02).

Provides:
1. REST API for essay assessment with real-time word counting and evidence citations.
2. Central switch toggle (Mock Agent vs. Live Agent) controllable via:
   - Environment variable (USE_MOCK_AGENT)
   - Runtime toggle endpoint (/api/config/toggle-mock)
   - Per-request override (mock: true/false in payload)
3. Serving static Frontend Single-Page Application (SPA) at root URL.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.tools.compute_tool import count_words
from backend.config import FRONTEND_DIR, ROOT_DIR, WORD_COUNT_REGEX
from backend.live_service import LiveAssessmentError, run_agent_assessment
from skills.writing_assessment.checks import WritingAssessment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")
LATEST_RESULT_PATH = ROOT_DIR / "latest_assessment_result.json"

app = FastAPI(
    title="IELTS Learning Agent API",
    description="Automated IELTS Writing Assessment System (UC-02) for SE373",
    version="0.1.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    """Ensure static assets and SPA pages are not cached during local development."""
    response = await call_next(request)
    if (
        request.url.path.startswith("/static")
        or request.url.path in ("/", "/style.css", "/app.js")
        or request.url.path.endswith(".html")
    ):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ==============================================================================
# Pydantic Schemas for API
# ==============================================================================
class AssessmentRequest(BaseModel):
    task_type: Literal["task1", "task2"] = Field(
        ..., description="IELTS Writing task type: 'task1' or 'task2'"
    )
    prompt: str = Field(
        default="", description="The IELTS prompt / question topic"
    )
    essay: str = Field(
        ..., min_length=1, description="Student's raw essay text"
    )
    task_material_text: str | None = None
    source_url: str | None = Field(default=None, pattern=r"^https://[^\s]+$")
    mock: bool | None = Field(
        default=None,
        description="Deprecated: Mock mode is permanently disabled. Evaluations strictly use Member 3 Live Agent.",
    )


class AssessmentResponse(BaseModel):
    success: bool
    execution_mode: str = "agent"
    duration_ms: float
    word_count: int
    assessment: WritingAssessment
    message: str | None = None


class ToggleMockRequest(BaseModel):
    enabled: bool


class WordCountRequest(BaseModel):
    text: str


# ==============================================================================
# API Endpoints
# ==============================================================================
@app.get("/api/health")
def health_check() -> dict[str, Any]:
    """Health check endpoint displaying server status and active agent mode."""
    return {
        "status": "healthy",
        "service": "IELTS Learning Agent Backend",
        "agent_mode": "live_agent_core_tv3",
        "mock_mode": False,
        "version": "0.1.0",
    }


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    """Retrieve runtime configuration for Live Agent."""
    return {
        "agent_mode": "live_agent_core_tv3",
        "mock_mode": False,
        "word_count_regex": WORD_COUNT_REGEX,
        "supported_tasks": ["task1", "task2"],
    }


@app.post("/api/config/toggle-mock")
def toggle_mock(payload: ToggleMockRequest) -> dict[str, Any]:
    """Mock mode is disabled; system strictly runs on Member 3 Live Agent."""
    return {
        "mock_mode": False,
        "message": "Mock mode is permanently disabled. System runs on Member 3 Live Agent.",
    }


@app.post("/api/count-words")
def api_count_words(payload: WordCountRequest) -> dict[str, Any]:
    """Calculate word count using the official harmonized regex."""
    count = count_words(payload.text)
    return {
        "word_count": count,
        "is_under_task1": count < 150,
        "is_under_task2": count < 250,
    }



@app.get("/api/sample-prompts")
def get_sample_prompts() -> list[dict[str, Any]]:
    """Return curated authentic sample IELTS prompts from official exam sources."""
    return [
        {
            "id": "task1_standard",
            "task_type": "task1",
            "title": "Task 1: Trips Made by Children to School (IELTS.org Official)",
            "prompt": (
                "The chart below shows the number of trips made by children in one country in 1990 and 2010 "
                "to travel to and from school using different modes of transport. Summarise the information by selecting "
                "and reporting the main features, and make comparisons where relevant. Write at least 150 words."
            ),
            "sample_essay": "",
        },
        {
            "id": "task2_standard",
            "task_type": "task2",
            "title": "Task 2: Future Health Standard (IELTS.org Official)",
            "prompt": (
                "The average standard of people's health is likely to be lower in the future than it is now. "
                "To what extent do you agree or disagree with this statement? Give reasons for your answer "
                "and include any relevant examples from your own knowledge or experience. Write at least 250 words."
            ),
            "sample_essay": "",
        },
        {
            "id": "task1_energy_consumption",
            "task_type": "task1",
            "title": "Task 1: USA Energy Consumption 1980–2030 (Cambridge IELTS)",
            "prompt": (
                "The graph below gives information from a report about consumption of energy in the USA since 1980 "
                "with projections until 2030. Summarise the information by selecting and reporting the main features, "
                "and make comparisons where relevant. Write at least 150 words."
            ),
            "sample_essay": "",
        },
        {
            "id": "task2_university_education",
            "task_type": "task2",
            "title": "Task 2: Free University Education Funding (Cambridge IELTS)",
            "prompt": (
                "Some people feel that the government should pay the costs of running universities so that "
                "a university education is free for all students. To what extent do you agree or disagree with this opinion? "
                "Give reasons for your answer and include any relevant examples from your own knowledge or experience. "
                "Write at least 250 words."
            ),
            "sample_essay": "",
        },
        {
            "id": "task1_ethanol_production",
            "task_type": "task1",
            "title": "Task 1: Biofuel Ethanol Production Process (British Council / IDP)",
            "prompt": (
                "The diagram below shows how a biofuel called ethanol is produced. "
                "Summarise the information by selecting and reporting the main features, and make comparisons where relevant. "
                "Write at least 150 words."
            ),
            "sample_essay": "",
        },
    ]


def build_sample_tests() -> list[dict[str, Any]]:
    """Build authentic IELTS practice exam sets for student testing on Computer-Delivered UI."""
    return [
        {
            "id": "ielts_practice_test_01",
            "name": "Bộ đề thi IELTS Academic 01 (Phương tiện đi học & Sức khỏe tương lai)",
            "source": "IELTS.org Official Academic Sample",
            "description": "Đề thi thực hành chính thức gồm Writing Task 1 (Biểu đồ cột) và Writing Task 2 (Nghị luận xã hội).",
            "questions": [
                {
                    "id": "practice_01_task1",
                    "task_type": "task1",
                    "title": "Task 1: Trips Made by Children to School (1990 & 2010)",
                    "prompt": (
                        "The chart below shows the number of trips made by children in one country in 1990 and 2010 "
                        "to travel to and from school using different modes of transport. Summarise the information by selecting "
                        "and reporting the main features, and make comparisons where relevant. Write at least 150 words.\n\n"
                        "Chart key: solid black bars = 1990; hatched bars = 2010. The chart covers children aged 5-12. "
                        "The vertical axis shows the total number of trips per year, in millions."
                    ),
                    "min_words": 150,
                    "suggested_time": "20 phút",
                    "sample_essay": (
                        "The chart gives you information on how children travelled to and from school in the years 1990 and 2010. "
                        "The modes of transport were by car, walking, cycling, walking and by bus and by bus only.\n\n"
                        "A striking feature in this chart is that the number of children who travelled by car has increased from 1990 to 2010. "
                        "In 1990 the most number of trips per year by children were by walking. However in 2010 it reduced to up to 6 million trips per year. "
                        "The total number of trips to school by cycling and walking and bus were approximately 6 million in 1990. "
                        "However the number of trips to school by cycling reduced to 2 million and the number of trips to school by walking and bus "
                        "reduced to about 3 million in 2010. There isn’t a significant change to the number of trips to school by bus. "
                        "In 1990 it was about 7 million and in 2010 it came down to approximately 5 million.\n\n"
                        "In 1990 the amount of children who travelled to and from school by car was significantly lower than the children who travelled by walking. "
                        "In contrast in 2010 the number of children who travelled to school by car increased and the number of children walking to school has decreased."
                    ),
                    "sample_band": "6.5",
                },
                {
                    "id": "practice_01_task2",
                    "task_type": "task2",
                    "title": "Task 2: Future Health Standard",
                    "prompt": (
                        "The average standard of people's health is likely to be lower in the future than it is now. "
                        "To what extent do you agree or disagree with this statement? Give reasons for your answer "
                        "and include any relevant examples from your own knowledge or experience. Write at least 250 words."
                    ),
                    "min_words": 250,
                    "suggested_time": "40 phút",
                    "sample_essay": (
                        "Some people believe that the average standard of people's health is likely to be lower in the future than it is now. "
                        "In my opinion, I disagree with this point of view.\n\n"
                        "First of all, medical science and technology are developing rapidly. Physicians and researchers can now cure and treat "
                        "numerous illnesses that were previously incurable. Furthermore, continuous breakthroughs in preventative medicine, genetic "
                        "therapies, and advanced surgical interventions are significantly enhancing life expectancy and physical vitality across populations.\n\n"
                        "Secondly, contemporary societies exhibit heightened awareness regarding personal wellbeing, nutrition, and exercise. "
                        "Widespread access to health information empowers citizens to adopt balanced diets, curb harmful habits such as smoking, "
                        "and engage in active lifestyles. Governments also invest substantially in public healthcare infrastructure and recreational facilities.\n\n"
                        "In conclusion, despite contemporary challenges related to sedentary lifestyles and processed foods, ongoing medical advancements "
                        "and informed lifestyle choices will ensure higher health standards in the future."
                    ),
                    "sample_band": "7.0",
                },
            ],
        },
        {
            "id": "ielts_practice_test_02",
            "name": "Bộ đề thi IELTS Academic 02 (Tiêu thụ năng lượng & Giáo dục đại học)",
            "source": "Cambridge IELTS Official Practice",
            "description": "Đề thi thực hành chuẩn Cambridge gồm Writing Task 1 (Biểu đồ đường) và Writing Task 2 (Thảo luận quan điểm giáo dục).",
            "questions": [
                {
                    "id": "practice_02_task1",
                    "task_type": "task1",
                    "title": "Task 1: Energy Consumption in the USA (1980–2030)",
                    "prompt": (
                        "The graph below gives information from a report about consumption of energy in the USA since 1980 with projections until 2030. "
                        "Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words."
                    ),
                    "min_words": 150,
                    "suggested_time": "20 phút",
                    "sample_essay": (
                        "The line graph illustrates energy consumption trends in the United States across six different fuel sources from 1980, with future projections up to 2030.\n\n"
                        "Overall, fossil fuels have historically dominated and are expected to continue leading overall consumption throughout the period. Petrol and oil consistently represent the largest share, starting at 35 quadrillion units in 1980 and projected to rise steadily to nearly 50 quadrillion by 2030.\n\n"
                        "Natural gas and coal experienced similar consumption levels in 1980 at approximately 20 quadrillion units each. However, while coal shows a gradual upward trajectory reaching about 31 quadrillion units, natural gas fluctuates before stabilizing around 25 quadrillion.\n\n"
                        "In contrast, cleaner energy sources—nuclear, solar/wind, and hydropower—remain comparatively minor contributors, each remaining below 10 quadrillion units over the entire projected timeframe."
                    ),
                    "sample_band": "7.5",
                },
                {
                    "id": "practice_02_task2",
                    "task_type": "task2",
                    "title": "Task 2: Free University Education Funding",
                    "prompt": (
                        "Some people feel that the government should pay the costs of running universities so that a university education "
                        "is free for all students. To what extent do you agree or disagree with this opinion? Give reasons for your answer "
                        "and include any relevant examples from your own knowledge or experience. Write at least 250 words."
                    ),
                    "min_words": 250,
                    "suggested_time": "40 phút",
                    "sample_essay": (
                        "Access to tertiary education remains a vital catalyst for socio-economic mobility. While some contend that public treasuries "
                        "should fully subsidize university tuition for every citizen, I believe that a cost-sharing model is both more economically viable "
                        "and socially equitable.\n\n"
                        "On the one hand, abolishing university tuition removes financial obstacles for gifted students from underprivileged backgrounds. "
                        "When academic admission is purely meritocratic rather than constrained by wealth, society maximizes intellectual capital and accelerates innovation.\n\n"
                        "On the other hand, funding universal tertiary education places an immense fiscal burden on taxpayers, which can lead to diminished "
                        "educational quality and underfunded facilities. Since university graduates typically command significantly higher lifetime earnings, "
                        "it is reasonable that recipients contribute partially toward their credentials through income-contingent loans.\n\n"
                        "In conclusion, while governments should guarantee comprehensive scholarships for disadvantaged students, full public subsidization "
                        "for all students is neither sustainable nor necessary."
                    ),
                    "sample_band": "7.5",
                },
            ],
        },
        {
            "id": "ielts_practice_test_03",
            "name": "Bộ đề thi IELTS Academic 03 (Sản xuất Ethanol & Đô thị hóa)",
            "source": "British Council & IDP Sample Tests",
            "description": "Đề thi thực hành chính thức gồm Writing Task 1 (Sơ đồ quy trình sản xuất) và Writing Task 2 (Đô thị và phát triển vùng).",
            "questions": [
                {
                    "id": "practice_03_task1",
                    "task_type": "task1",
                    "title": "Task 1: Biofuel Ethanol Production Process",
                    "prompt": (
                        "The diagram below shows how a biofuel called ethanol is produced. "
                        "Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words."
                    ),
                    "min_words": 150,
                    "suggested_time": "20 phút",
                    "sample_essay": (
                        "The flowchart illustrates the sequential industrial stages involved in manufacturing ethanol biofuel.\n\n"
                        "Overall, ethanol production is a circular biochemical process comprising plant cultivation, mechanical processing, chemical fermentation, and final product distribution.\n\n"
                        "Initially, crops absorb sunlight and atmospheric carbon dioxide during growth. Once mature, plants are harvested and mechanically shredded into fine cellulose fibers. The pre-processed material then undergoes chemical pretreatment to release essential sugars.\n\n"
                        "Subsequently, microbes and enzymes are introduced to ferment the sugars into ethanol liquid. Following purification, the refined fuel is transported to filling stations for commercial vehicular use, ultimately releasing carbon dioxide that is re-absorbed by newly planted vegetation."
                    ),
                    "sample_band": "7.0",
                },
                {
                    "id": "practice_03_task2",
                    "task_type": "task2",
                    "title": "Task 2: Urban Congestion & Regional Development",
                    "prompt": (
                        "People living in big cities face several problems. What are these problems? "
                        "Should governments encourage city residents to move to regional towns? Give reasons for your answer "
                        "and include any relevant examples from your own knowledge or experience. Write at least 250 words."
                    ),
                    "min_words": 250,
                    "suggested_time": "40 phút",
                    "sample_essay": (
                        "Rapid urbanization across the globe has exacerbated numerous difficulties for metropolis inhabitants, notably severe traffic congestion, exorbitant housing costs, and escalating air pollution.\n\n"
                        "Traffic gridlock consumes precious productive hours and induces psychological stress, while inflated real estate pricing forces younger demographics into precarious living situations. To alleviate these acute pressures, governmental initiatives aimed at decentralization and regional relocation represent a pragmatic and strategic remedy.\n\n"
                        "By offering corporate tax incentives and improving intercity transport infrastructure, authorities can motivate businesses and families to relocate to regional towns. This not only decompresses congested metropolises but also invigorates regional economic development and spreads prosperity equitably.\n\n"
                        "In conclusion, addressing urban distress requires proactive state intervention to stimulate balanced regional migration and sustainable infrastructure development."
                    ),
                    "sample_band": "7.5",
                },
            ],
        },
    ]


SAMPLE_TESTS: list[dict[str, Any]] = build_sample_tests()


@app.get("/api/sample-tests")
def get_sample_tests() -> list[dict[str, Any]]:
    """Return structured sample IELTS tests with name, source, and questions list."""
    return build_sample_tests()


def load_benchmark_tasks() -> dict[str, list[dict[str, Any]]]:
    """Load individual Task 1 and Task 2 prompts from evals/benchmark_test/benchmark.json and 5_basic_cases.json."""
    bm_file = ROOT_DIR / "evals" / "benchmark_test" / "benchmark.json"
    basic_file = ROOT_DIR / "evals" / "data" / "5_basic_cases.json"

    t1_list: list[dict[str, Any]] = []
    t2_list: list[dict[str, Any]] = []

    if bm_file.is_file():
        try:
            bm_data = json.loads(bm_file.read_text(encoding="utf-8"))
            for item in bm_data:
                tt = item.get("task_type")
                cid = item.get("case_id", "")
                q_text = item.get("exam_question", "").strip()
                mat = item.get("material")
                mat_url = f"/materials/{Path(mat).name}" if mat else None
                first_line = q_text.splitlines()[0] if q_text else "Prompt"

                if tt == "task1":
                    t1_list.append({
                        "id": cid,
                        "task_type": "task1",
                        "title": f"Task 1: {first_line[:65]}...",
                        "prompt": q_text,
                        "material": mat_url,
                        "source": item.get("source", "IELTS Juice / Benchmark Test"),
                        "suggested_time": "20 phút",
                        "min_words": 150,
                        "sample_essay": item.get("essay", ""),
                        "sample_band": str(item.get("scores", {}).get("overall_band", "")),
                    })
                elif tt == "task2":
                    t2_list.append({
                        "id": cid,
                        "task_type": "task2",
                        "title": f"Task 2: {first_line[:65]}...",
                        "prompt": q_text,
                        "material": None,
                        "source": item.get("source", "IELTS Online Tests / Benchmark Test"),
                        "suggested_time": "40 phút",
                        "min_words": 250,
                        "sample_essay": item.get("essay", ""),
                        "sample_band": str(item.get("scores", {}).get("overall_band", "")),
                    })
        except Exception as exc:
            logger.warning("Could not load benchmark.json: %s", exc)

    if basic_file.is_file():
        try:
            basic_data = json.loads(basic_file.read_text(encoding="utf-8"))
            for item in basic_data:
                bid = item.get("id", "")
                if bid in ("case_04_off_topic_advanced", "case_05_grammar_errors"):
                    tag = "Case 04: Lạc đề" if "04" in bid else "Case 05: Lỗi ngữ pháp"
                    q_text = item.get("exam_question", "").strip()
                    first_line = q_text.splitlines()[0] if q_text else "Prompt"
                    t2_list.append({
                        "id": bid,
                        "task_type": "task2",
                        "title": f"Task 2 [{tag}]: {first_line[:55]}...",
                        "prompt": q_text,
                        "material": None,
                        "source": f"IELTS.org Official ({tag})",
                        "suggested_time": "40 phút",
                        "min_words": 250,
                        "sample_essay": item.get("essay", ""),
                        "sample_band": "",
                    })
        except Exception as exc:
            logger.warning("Could not load 5_basic_cases.json: %s", exc)

    return {"task1": t1_list, "task2": t2_list}


BENCHMARK_TASKS: dict[str, list[dict[str, Any]]] = load_benchmark_tasks()


@app.get("/api/benchmark-tasks")
def get_benchmark_tasks() -> dict[str, list[dict[str, Any]]]:
    """Return individual Task 1 and Task 2 prompts from benchmark_test and basic cases."""
    return load_benchmark_tasks()


@app.post("/api/assess-writing", response_model=AssessmentResponse)
def assess_writing(payload: AssessmentRequest) -> AssessmentResponse:
    """Evaluate a student's Writing Task 1 or Task 2 essay using Member 3's LangGraph Agent."""
    start_time = time.perf_counter()
    if not payload.essay.strip() or not payload.prompt.strip():
        raise HTTPException(status_code=422, detail="Vui lòng nhập đề bài và nội dung bài viết.")
    if payload.task_type == "task1" and not (payload.task_material_text and payload.task_material_text.strip()):
        raise HTTPException(status_code=422, detail="Task 1 cần đầy đủ số liệu và chú giải biểu đồ.")
    w_count = count_words(payload.essay)
    logger.info("Evaluating essay with Member 3 Live Agent Core (word count=%d)...", w_count)

    try:
        assessment = run_agent_assessment(
            task_type=payload.task_type,
            prompt=payload.prompt,
            essay=payload.essay,
            task_material_text=payload.task_material_text,
            source_url=payload.source_url,
        )
    except LiveAssessmentError as exc:
        status_code = {
            "INVALID_TASK": 422, "INVALID_INPUT": 422,
            "LLM_RATE_LIMITED": 429, "LLM_TIMEOUT": 504,
            "RETRIEVAL_INVALID": 503, "DEPENDENCY_UNAVAILABLE": 503,
            "LLM_CONFIGURATION_ERROR": 503,
        }.get(exc.code.value, 502)
        raise HTTPException(status_code=status_code, detail={
            "code": exc.code.value, "retry_count": exc.retry_count,
            "errors": exc.errors, "diagnostics": exc.diagnostics,
        }) from None
    except Exception as exc:
        logger.error("Agent assessment failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể chấm bài lúc này.",
        ) from exc

    duration = (time.perf_counter() - start_time) * 1000.0

    resp = AssessmentResponse(
        success=True,
        execution_mode="agent",
        duration_ms=round(duration, 4),
        word_count=w_count,
        assessment=assessment,
        message="Evaluation completed successfully using Member 3 Live Agent Core.",
    )

    # Automatically save the latest evaluation result to disk
    try:
        latest_path = LATEST_RESULT_PATH
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(resp.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
        logger.info("Saved latest assessment result to %s", latest_path)
    except Exception as save_err:
        logger.warning("Could not persist latest_assessment_result.json: %s", save_err)

    return resp


@app.get("/api/latest-assessment")
def get_latest_assessment() -> dict[str, Any]:
    """Return the most recent assessment JSON output."""
    latest_path = LATEST_RESULT_PATH
    if latest_path.is_file():
        try:
            with open(latest_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as read_err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not read latest assessment result: {read_err}",
            ) from read_err
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Chưa có kết quả bài nộp nào được ghi nhận. Vui lòng nộp bài để tạo kết quả.",
    )


# ==============================================================================
# Mount Frontend Static Files & SPA Root & Materials
# ==============================================================================
MATERIALS_DIR = ROOT_DIR / "evals" / "materials"
if MATERIALS_DIR.is_dir():
    app.mount("/materials", StaticFiles(directory=str(MATERIALS_DIR)), name="materials")

if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.api_route("/", methods=["GET", "HEAD"])
    def serve_frontend_index() -> FileResponse:
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return FileResponse(FRONTEND_DIR / ".gitkeep")

    @app.api_route("/style.css", methods=["GET", "HEAD"])
    def serve_frontend_style() -> FileResponse:
        style_file = FRONTEND_DIR / "style.css"
        if style_file.exists():
            return FileResponse(style_file)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="style.css not found")

    @app.api_route("/app.js", methods=["GET", "HEAD"])
    def serve_frontend_script() -> FileResponse:
        js_file = FRONTEND_DIR / "app.js"
        if js_file.exists():
            return FileResponse(js_file)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="app.js not found")
