/**
 * Frontend JavaScript for IELTS Learning Agent (UC-02).
 * Handles Home navigation, Writing Test options (Chọn bài mẫu & Tự thiết kế),
 * Sample Tests Window with 3-dot question expansion, real-time word counting,
 * interactive evidence highlighting, timer, and Mock vs Live agent switching.
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- Navigation & View Elements ---
  const homeView = document.getElementById("homeView");
  const writingTestView = document.getElementById("writingTestView");
  const navHomeBtn = document.getElementById("navHomeBtn");
  const navWritingBtn = document.getElementById("navWritingBtn");
  const btnBackToHome = document.getElementById("btnBackToHome");
  const btnStartWriting = document.getElementById("btnStartWriting");
  const btnOpenSampleTestsFromEditor = document.getElementById("btnOpenSampleTestsFromEditor");

  // --- Modal Elements ---
  const writingOptionsModal = document.getElementById("writingOptionsModal");
  const closeWritingOptionsBtn = document.getElementById("closeWritingOptionsBtn");
  const optSelectSampleBtn = document.getElementById("optSelectSampleBtn");
  const optCustomTestBtn = document.getElementById("optCustomTestBtn");

  const sampleTestsModal = document.getElementById("sampleTestsModal");
  const closeSampleTestsBtn = document.getElementById("closeSampleTestsBtn");
  const sampleTestsList = document.getElementById("sampleTestsList");

  // --- Writing Workspace Elements ---
  const tabTask1 = document.getElementById("tabTask1");
  const tabTask2 = document.getElementById("tabTask2");
  const presetSelector = document.getElementById("presetSelector");
  const promptInput = document.getElementById("promptInput");
  const taskMaterialInput = document.getElementById("taskMaterialInput");
  const taskMaterialGroup = document.getElementById("taskMaterialGroup");
  const essayInput = document.getElementById("essayInput");
  const wordCountBadge = document.getElementById("wordCountBadge");
  const wordTargetBadge = document.getElementById("wordTargetBadge");
  const lengthStatusBadge = document.getElementById("lengthStatusBadge");
  const mockModeToggle = document.getElementById("mockModeToggle");
  const modeStatusBadge = document.getElementById("modeStatusBadge");

  const timerDisplay = document.getElementById("timerDisplay");
  const timerToggleBtn = document.getElementById("timerToggleBtn");
  const timerResetBtn = document.getElementById("timerResetBtn");

  const clearBtn = document.getElementById("clearBtn");
  const submitBtn = document.getElementById("submitBtn");
  const submitSpinner = document.getElementById("submitSpinner");
  const submitText = document.getElementById("submitText");

  const emptyResultState = document.getElementById("emptyResultState");
  const assessmentResults = document.getElementById("assessmentResults");
  const overallBandValue = document.getElementById("overallBandValue");
  const durationValue = document.getElementById("durationValue");
  const resWordCount = document.getElementById("resWordCount");
  const resExecMode = document.getElementById("resExecMode");
  const disclaimerText = document.getElementById("disclaimerText");
  const flagsContainer = document.getElementById("flagsContainer");
  const highlightedEssayContent = document.getElementById("highlightedEssayContent");
  const criteriaGrid = document.getElementById("criteriaGrid");
  const correctionsList = document.getElementById("correctionsList");

  // --- State Variables ---
  let currentTask = "task1";
  let targetWords = 150;
  let presetsData = {};
  let sampleTestsData = [];
  let currentAssessment = null;
  let timerInterval = null;
  let timeLeftSeconds = 40 * 60; // 40 minutes default
  let timerRunning = false;
  let currentView = "home"; // "home" or "writing"

  // Harmonized regex for word count (matches backend & harness)
  const WORD_REGEX = /\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b/g;

  // Fallback Sample Tests Data
  const DEFAULT_SAMPLE_TESTS = [
    {
      id: "cambridge_19_test1",
      name: "Cambridge IELTS 19 - Test 1 Academic",
      source: "Cambridge University Press & Assessment (2024)",
      description: "Đề thi thử chính thức mới nhất năm 2024 từ bộ sách Cambridge IELTS 19.",
      questions: [
        {
          id: "c19_t1_q1",
          task_type: "task1",
          title: "Task 1: Rented Accommodation in Europe (2011–2021)",
          prompt: "The chart below shows the percentage of households in four European countries living in rented accommodation between 2011 and 2021. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: ""
        },
        {
          id: "c19_t1_q2",
          task_type: "task2",
          title: "Task 2: Compulsory Community Service in High School",
          prompt: "Some people believe that unpaid community service should be a compulsory part of high school programmes (for example working for a charity, improving the neighborhood or teaching sports to younger children). To what extent do you agree or disagree?",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: ""
        }
      ]
    },
    {
      id: "cambridge_18_test2",
      name: "Cambridge IELTS 18 - Test 2 Academic",
      source: "Cambridge University Press & Assessment (2023)",
      description: "Đề thi chuẩn hóa học thuật từ bộ đề Cambridge IELTS 18.",
      questions: [
        {
          id: "c18_t2_q1",
          task_type: "task1",
          title: "Task 1: Monthly Temperature & Rainfall in 3 Major Cities",
          prompt: "The graph below shows the average monthly temperature and total rainfall in three major cities throughout 2020. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: ""
        },
        {
          id: "c18_t2_q2",
          task_type: "task2",
          title: "Task 2: Impact of Technology on Modern Life Complexity",
          prompt: "Some people believe that technology has made modern life more complicated rather than simpler. To what extent do you agree or disagree with this statement?",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: ""
        }
      ]
    },
    {
      id: "cambridge_17_test1",
      name: "Cambridge IELTS 17 - Test 1 Academic (Kèm bài mẫu)",
      source: "Cambridge University Press & Assessment (2022)",
      description: "Đề thi kèm bài làm mẫu chuẩn Band 6.5 và Band 7.0 để thử nghiệm hệ thống chấm điểm.",
      questions: [
        {
          id: "c17_t1_q1",
          task_type: "task1",
          title: "Task 1: Renewable Energy Production (Standard Band 6.5)",
          prompt: "The chart below shows the percentage of electricity generated from renewable sources in four countries between 2010 and 2020. Summarise the information by selecting and reporting the main features.",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: "The bar chart illustrates the proportion of electricity produced from renewable energy sources in four different countries from 2010 to 2020. Overall, it is evident that all four nations experienced an upward trend in renewable power generation over the ten-year period. In 2010, Country A was the leader, accounting for approximately 30% of total electricity production. By 2020, this figure surged dramatically to reach nearly 55%. Country B followed a similar trajectory, rising steadily from 20% to 38%. In contrast, Country C and Country D registered comparatively modest growth throughout the observed timeframe. Country C started at 10% in 2010 and climbed incrementally to finish at 22% in 2020. Finally, Country D remained the lowest throughout, increasing from a mere 5% to 15%. In summary, while renewable electricity output expanded significantly across all four examined countries, Country A maintained the most commanding share throughout the entire decade, demonstrating the most substantial commitment to green energy transition.",
          sample_band: "6.5"
        },
        {
          id: "c17_t1_q2",
          task_type: "task2",
          title: "Task 2: Remote Working Merits (Standard Band 7.0)",
          prompt: "Some people believe that working from home brings more benefits to employees and employers than working in an office. To what extent do you agree or disagree?",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: "In recent years, remote working has emerged as a prominent arrangement across numerous modern industries. I firmly agree that telecommuting provides far greater advantages to both workers and organizations compared to traditional office-based routines.\n\nFirst and foremost, employees experience profound improvements in productivity and work-life balance when working from home. By eliminating exhausting daily commutes, individuals conserve valuable hours each day, which can subsequently be channeled into focused intellectual tasks or healthy personal activities. Moreover, workers operate within a personalized and comfortable domestic environment, significantly minimizing ambient office distractions and stress levels.\n\nFrom the corporate standpoint, businesses can substantially reduce operating expenses through remote work models. Employers are no longer burdened by exorbitant rental costs for commercial office premises, utility bills, and workplace maintenance. Furthermore, companies can recruit exceptional talent globally regardless of geographical constraints, thereby fostering innovation and maintaining a highly competitive advantage in global markets.\n\nIn conclusion, telecommuting delivers indispensable benefits for work flexibility and fiscal efficiency. Both employees and corporate entities should actively embrace flexible remote working policies in the digital age.",
          sample_band: "7.0"
        }
      ]
    },
    {
      id: "british_council_2024",
      name: "British Council Official Practice Test 2024",
      source: "British Council IELTS Preparation Materials",
      description: "Đề thi thử chính thức chuẩn quốc tế từ Hội đồng Anh (British Council).",
      questions: [
        {
          id: "bc_2024_q1",
          task_type: "task1",
          title: "Task 1: Public Park Redevelopment Plan (1920 vs Today)",
          prompt: "The plans below show a public park when it first opened in 1920 and the same park today. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: ""
        },
        {
          id: "bc_2024_q2",
          task_type: "task2",
          title: "Task 2: Causes & Effects of Fast Food Consumption",
          prompt: "In many countries, an increasing number of people are buying and consuming fast food. What are the causes of this trend, and what effects does it have on society and individuals?",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: ""
        }
      ]
    },
    {
      id: "idp_mock_2024",
      name: "IDP IELTS Mock Examination 2024",
      source: "IDP Education Official Assessment Practice",
      description: "Đề thi thử định dạng khảo thí từ trung tâm khảo thí IDP Education.",
      questions: [
        {
          id: "idp_2024_q1",
          task_type: "task1",
          title: "Task 1: Water Consumption Across 3 Sectors in 2020",
          prompt: "The table below gives information about water consumption in three sectors (agriculture, industry, domestic) in four countries in 2020. Summarise the information by selecting and reporting the main features.",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: ""
        },
        {
          id: "idp_2024_q2",
          task_type: "task2",
          title: "Task 2: Practical Skills vs Theoretical Knowledge in Universities",
          prompt: "Some people think that universities should prioritize practical skills over theoretical knowledge to increase graduates' employability. Discuss both views and give your opinion.",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: ""
        }
      ]
    }
  ];

  // --- Initialization ---
  fetchServerConfig();
  fetchSamplePresets();
  fetchSampleTests();
  setupEventListeners();

  // Show Home view by default
  switchView("home");

  // --- View Switching Functions ---

  function switchView(viewName) {
    currentView = viewName;
    if (viewName === "home") {
      homeView.classList.remove("hidden");
      writingTestView.classList.add("hidden");
      navHomeBtn.classList.add("active");
      navWritingBtn.classList.remove("active");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      homeView.classList.add("hidden");
      writingTestView.classList.remove("hidden");
      navHomeBtn.classList.remove("active");
      navWritingBtn.classList.add("active");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  // --- Modal Functions ---

  function openWritingOptionsModal() {
    writingOptionsModal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }

  function closeWritingOptionsModal() {
    writingOptionsModal.classList.add("hidden");
    document.body.style.overflow = "";
  }

  function openSampleTestsModal() {
    closeWritingOptionsModal();
    sampleTestsModal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
    renderSampleTestsList();
  }

  function closeSampleTestsModal() {
    sampleTestsModal.classList.add("hidden");
    document.body.style.overflow = "";
  }

  // --- Sample Tests Rendering & 3-Dot Interaction ---

  async function fetchSampleTests() {
    try {
      const res = await fetch("/api/sample-tests");
      if (res.ok) {
        sampleTestsData = await res.json();
      } else {
        sampleTestsData = DEFAULT_SAMPLE_TESTS;
      }
    } catch (e) {
      console.warn("Could not fetch /api/sample-tests, using default mock tests.", e);
      sampleTestsData = DEFAULT_SAMPLE_TESTS;
    }
  }

  function renderSampleTestsList() {
    sampleTestsList.innerHTML = "";
    const list = (sampleTestsData && sampleTestsData.length > 0) ? sampleTestsData : DEFAULT_SAMPLE_TESTS;

    list.forEach((test, testIdx) => {
      const card = document.createElement("div");
      card.className = "sample-test-card";
      card.id = `testCard-${test.id || testIdx}`;

      // Card Header: Tên bài mẫu, Nguồn bài thi, and Expand Indicator
      const header = document.createElement("div");
      header.className = "sample-test-header";
      header.setAttribute("role", "button");
      header.setAttribute("tabindex", "0");
      header.setAttribute("title", "Nhấn vào đây để xem danh sách câu hỏi");
      header.innerHTML = `
        <div class="sample-test-info">
          <div class="sample-test-name-row">
            <span class="test-icon">📄</span>
            <h4 class="sample-test-name">${escapeHtml(test.name)}</h4>
          </div>
          <div class="sample-test-source-row">
            <span class="source-tag">🏛 Nguồn bài thi:</span>
            <span class="sample-test-source">${escapeHtml(test.source)}</span>
          </div>
        </div>
        <div class="sample-test-action-area">
          <span class="expand-badge">
            <span class="expand-chevron">▼</span>
          </span>
        </div>
      `;

      // Collapsible Questions Drawer (Hiển thị khi ấn vào đề đó)
      const drawer = document.createElement("div");
      drawer.className = "sample-questions-drawer hidden";
      drawer.id = `drawer-${testIdx}`;

      let questionsHtml = `
        <div class="drawer-header">
          <span class="drawer-title">📋 Danh Sách Câu Hỏi Của Bài Thi:</span>
          <span class="drawer-sub">Chọn một câu hỏi để nạp vào bài thi Writing</span>
        </div>
        <div class="questions-list">
      `;

      (test.questions || []).forEach((q, qIdx) => {
        const isTask1 = q.task_type === "task1";
        const taskLabel = isTask1 ? "Writing Task 1" : "Writing Task 2";
        const taskBadgeClass = isTask1 ? "badge-task1" : "badge-task2";
        const wordReq = isTask1 ? "Min 150 từ" : "Min 250 từ";
        const timeReq = q.suggested_time || (isTask1 ? "20 phút" : "40 phút");

        questionsHtml += `
          <div class="question-item-card">
            <div class="question-item-header">
              <span class="task-badge ${taskBadgeClass}">${taskLabel}</span>
              <span class="question-meta-info">⏱ ${timeReq} • 📝 ${wordReq}</span>
            </div>
            <h5 class="question-item-title">${escapeHtml(q.title || `Câu hỏi ${qIdx + 1}`)}</h5>
            <p class="question-prompt-text">${escapeHtml(q.prompt)}</p>
            <div class="question-actions">
              <button type="button" class="btn-sm btn-primary btn-select-question" data-test-idx="${testIdx}" data-q-idx="${qIdx}">
                ✍️ Chọn câu này &amp; Bắt đầu làm bài
              </button>
              ${q.sample_essay ? `
                <button type="button" class="btn-sm btn-outline btn-load-sample-essay" data-test-idx="${testIdx}" data-q-idx="${qIdx}">
                  ⚡ Nạp bài mẫu chuẩn (Band ${escapeHtml(q.sample_band || "7.0")})
                </button>
              ` : ""}
            </div>
          </div>
        `;
      });

      questionsHtml += `</div>`;
      drawer.innerHTML = questionsHtml;

      // Event listener: Nhấn vào đề đó thì toggle hiển thị danh sách câu hỏi
      function toggleDrawer() {
        const isHidden = drawer.classList.contains("hidden");
        // Close other open drawers for clean accordion UX
        document.querySelectorAll(".sample-questions-drawer").forEach(d => {
          if (d !== drawer) d.classList.add("hidden");
        });
        document.querySelectorAll(".sample-test-card").forEach(c => {
          if (c !== card) c.classList.remove("expanded");
        });

        if (isHidden) {
          drawer.classList.remove("hidden");
          card.classList.add("expanded");
        } else {
          drawer.classList.add("hidden");
          card.classList.remove("expanded");
        }
      }

      header.addEventListener("click", toggleDrawer);
      header.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggleDrawer();
        }
      });

      card.appendChild(header);
      card.appendChild(drawer);
      sampleTestsList.appendChild(card);
    });

    // Attach event listeners to question selection buttons
    sampleTestsList.querySelectorAll(".btn-select-question").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const testIdx = parseInt(btn.dataset.testIdx, 10);
        const qIdx = parseInt(btn.dataset.qIdx, 10);
        loadSelectedQuestion(testIdx, qIdx, false);
      });
    });

    sampleTestsList.querySelectorAll(".btn-load-sample-essay").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const testIdx = parseInt(btn.dataset.testIdx, 10);
        const qIdx = parseInt(btn.dataset.qIdx, 10);
        loadSelectedQuestion(testIdx, qIdx, true);
      });
    });
  }

  function loadSelectedQuestion(testIdx, qIdx, loadSampleEssay = false) {
    const list = (sampleTestsData && sampleTestsData.length > 0) ? sampleTestsData : DEFAULT_SAMPLE_TESTS;
    const test = list[testIdx];
    if (!test || !test.questions || !test.questions[qIdx]) return;

    const question = test.questions[qIdx];

    // Set task type (Task 1 or Task 2)
    setTask(question.task_type);

    // Set prompt
    promptInput.value = question.prompt;
    taskMaterialInput.value = question.task_material_text || "";

    // Set or clear essay
    if (loadSampleEssay && question.sample_essay) {
      essayInput.value = question.sample_essay;
    } else {
      essayInput.value = "";
    }

    // Reset preset selector
    presetSelector.value = "";

    // Update word count
    updateWordCountDisplay();

    // Reset results if any
    resetAssessmentDisplay();

    // Close modal
    closeSampleTestsModal();

    // Switch to Writing view
    switchView("writing");

    // Focus editor
    essayInput.focus();
  }

  // --- Writing Workspace Functions ---

  function countWords(text) {
    if (!text || !text.trim()) return 0;
    const matches = text.match(WORD_REGEX);
    return matches ? matches.length : 0;
  }

  function updateWordCountDisplay() {
    const text = essayInput.value;
    const count = countWords(text);
    wordCountBadge.textContent = count;
    wordTargetBadge.textContent = `/ ${targetWords} từ`;

    if (count < targetWords && count > 0) {
      lengthStatusBadge.classList.remove("hidden");
      lengthStatusBadge.textContent = `Thiếu ${targetWords - count} từ`;
    } else {
      lengthStatusBadge.classList.add("hidden");
    }
  }

  async function fetchServerConfig() {
    try {
      const res = await fetch("/api/config");
      if (res.ok) {
        const config = await res.json();
        mockModeToggle.checked = config.mock_mode;
        updateModeBadge(config.mock_mode);
      }
    } catch (e) {
      console.warn("Could not fetch server config, using local defaults.", e);
    }
  }

  function updateModeBadge(isMock) {
    if (isMock) {
      modeStatusBadge.className = "badge badge-mock";
      modeStatusBadge.textContent = "⚡ Mock Agent";
    } else {
      modeStatusBadge.className = "badge badge-live";
      modeStatusBadge.textContent = "🤖 Live Agent";
    }
  }

  async function fetchSamplePresets() {
    try {
      const res = await fetch("/api/sample-prompts");
      if (res.ok) {
        const list = await res.json();
        presetsData = {};
        list.forEach((item) => {
          presetsData[item.id] = item;
        });
      }
    } catch (e) {
      console.warn("Could not load presets from server.", e);
    }
  }

  function setTask(taskType) {
    currentTask = taskType;
    taskMaterialGroup.classList.toggle("hidden", taskType !== "task1");
    if (taskType === "task1") {
      tabTask1.classList.add("active");
      tabTask2.classList.remove("active");
      targetWords = 150;
    } else {
      tabTask2.classList.add("active");
      tabTask1.classList.remove("active");
      targetWords = 250;
    }
    updateWordCountDisplay();
  }

  function loadPreset(presetId) {
    const preset = presetsData[presetId];
    if (!preset) return;

    setTask(preset.task_type);
    promptInput.value = preset.prompt;
    taskMaterialInput.value = preset.task_material_text || "";
    essayInput.value = preset.sample_essay;
    updateWordCountDisplay();
  }

  function resetAssessmentDisplay() {
    emptyResultState.classList.remove("hidden");
    assessmentResults.classList.add("hidden");
  }

  // Timer controls
  function updateTimerDisplay() {
    const mins = Math.floor(timeLeftSeconds / 60);
    const secs = timeLeftSeconds % 60;
    timerDisplay.textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  function toggleTimer() {
    if (timerRunning) {
      clearInterval(timerInterval);
      timerRunning = false;
      timerToggleBtn.textContent = "Tiếp tục";
    } else {
      timerRunning = true;
      timerToggleBtn.textContent = "Tạm dừng";
      timerInterval = setInterval(() => {
        if (timeLeftSeconds > 0) {
          timeLeftSeconds--;
          updateTimerDisplay();
        } else {
          clearInterval(timerInterval);
          timerRunning = false;
          timerToggleBtn.textContent = "Hết giờ!";
          alert("Hết 40 phút làm bài IELTS Writing!");
        }
      }, 1000);
    }
  }

  function resetTimer() {
    clearInterval(timerInterval);
    timerRunning = false;
    timeLeftSeconds = 40 * 60;
    timerToggleBtn.textContent = "Bắt đầu";
    updateTimerDisplay();
  }

  // --- Essay Submission & Assessment Rendering ---

  async function submitEssay() {
    const essayText = essayInput.value;
    if (!essayText.trim()) {
      alert("Vui lòng nhập bài viết trước khi nộp!");
      essayInput.focus();
      return;
    }

    submitBtn.disabled = true;
    submitSpinner.classList.remove("hidden");
    submitText.textContent = "Đang thẩm định & Chấm bài...";

    const payload = {
      task_type: currentTask,
      prompt: promptInput.value.trim(),
      essay: essayText,
      task_material_text: currentTask === "task1" ? taskMaterialInput.value.trim() || null : null,
      mock: mockModeToggle.checked,
    };

    try {
      const res = await fetch("/api/assess-writing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const detail = errorData.detail;
        const messages = {
          RETRIEVAL_INVALID: "Dữ liệu tiêu chí chấm chưa sẵn sàng.",
          DEPENDENCY_UNAVAILABLE: "Dữ liệu hoặc công cụ chấm chưa sẵn sàng.",
          LLM_CONFIGURATION_ERROR: "Dịch vụ chấm chưa được cấu hình đầy đủ.",
          LLM_RATE_LIMITED: "Dịch vụ đang quá tải. Vui lòng thử lại sau.",
          LLM_TIMEOUT: "Dịch vụ chấm phản hồi chậm. Vui lòng thử lại.",
          ASSESSMENT_VALIDATION_FAILED: "Chưa tạo được kết quả qua kiểm tra. Vui lòng thử lại.",
        };
        throw new Error(typeof detail === "string" ? detail :
          messages[detail?.code] || "Không thể chấm bài lúc này. Vui lòng thử lại.");
      }

      const data = await res.json();
      currentAssessment = data.assessment;

      renderResults(data, essayText);
    } catch (err) {
      alert(`Lỗi khi chấm bài: ${err.message}`);
      console.error(err);
    } finally {
      submitBtn.disabled = false;
      submitSpinner.classList.add("hidden");
      submitText.textContent = "🚀 Nộp bài & Chấm điểm ngay";
    }
  }

  function renderResults(apiResponse, rawEssay) {
    const a = apiResponse.assessment;
    emptyResultState.classList.add("hidden");
    assessmentResults.classList.remove("hidden");

    // Score Header
    overallBandValue.textContent = a.overall_band.toFixed(1);
    durationValue.textContent = `${apiResponse.duration_ms} ms`;
    resWordCount.textContent = a.word_count;
    resExecMode.textContent = apiResponse.execution_mode.toUpperCase();
    disclaimerText.textContent = a.disclaimer;

    // Flags
    flagsContainer.innerHTML = "";
    if (a.flags && a.flags.length > 0) {
      flagsContainer.classList.remove("hidden");
      a.flags.forEach((flag) => {
        const pill = document.createElement("span");
        pill.className = "badge badge-flag";
        let label = flag;
        if (flag === "under_length") label = "⚠️ Chưa đủ độ dài quy định";
        if (flag === "off_topic") label = "🚨 Lạc đề hoàn toàn (Cap <= 5.0)";
        if (flag === "possible_plagiarism") label = "⚠️ Nghi vấn đạo văn / Canned text";
        if (flag === "injection_detected") label = "🛡 Phát hiện Prompt Injection";
        pill.textContent = label;
        flagsContainer.appendChild(pill);
      });
    } else {
      flagsContainer.classList.add("hidden");
    }

    // Render Highlighted Essay
    renderInteractiveEssay(rawEssay, a.criteria);

    // Render 4 Criteria Cards
    renderCriteriaCards(a.criteria);

    // Render Actionable Corrections
    renderCorrections(a.corrections);

    // Scroll smoothly to results
    document.getElementById("resultsSection").scrollIntoView({ behavior: "smooth" });
  }

  function renderInteractiveEssay(essayText, criteria) {
    // Backend offsets count Unicode code points; JS slice counts UTF-16 units.
    const offsets = [0];
    for (const character of essayText) {
      offsets.push(offsets[offsets.length - 1] + character.length);
    }
    // Gather all evidence spans across criteria
    const spans = [];
    criteria.forEach((crit, critIdx) => {
      if (crit.evidence && Array.isArray(crit.evidence)) {
        crit.evidence.forEach((ev, evIdx) => {
          if (ev.quote && Number.isInteger(ev.start_char) && Number.isInteger(ev.end_char) &&
              ev.start_char >= 0 && ev.end_char > ev.start_char && ev.end_char < offsets.length &&
              essayText.slice(offsets[ev.start_char], offsets[ev.end_char]) === ev.quote) {
            spans.push({
              quote: ev.quote,
              start: offsets[ev.start_char],
              end: offsets[ev.end_char],
              criterion: crit.criterion,
              comment: crit.comment,
              critIdx: critIdx,
              id: `quote-${critIdx}-${evIdx}`,
            });
          }
        });
      }
    });

    // Split at all boundaries so overlapping evidence remains clickable for
    // every criterion without duplicating or dropping any essay characters.
    const boundaries = [...new Set([0, essayText.length,
      ...spans.flatMap((span) => [span.start, span.end])])].sort((a, b) => a - b);
    let html = "";
    for (let index = 0; index < boundaries.length - 1; index++) {
      const start = boundaries[index];
      const end = boundaries[index + 1];
      const active = spans.filter((span) => span.start <= start && span.end >= end);
      const text = escapeHtml(essayText.slice(start, end));
      if (active.length) {
        const ids = active.map((span) => span.id).join(" ");
        const title = active.map((span) => `${span.criterion}: ${span.comment}`).join(" | ");
        html += `<mark class="quote-highlight" data-quote-ids="${ids}" title="${escapeHtml(title)}">${text}</mark>`;
      } else {
        html += text;
      }
    }

    highlightedEssayContent.innerHTML = html;

    // Attach click events on marks
    document.querySelectorAll(".quote-highlight").forEach((el) => {
      el.addEventListener("click", () => {
        highlightQuote(el.dataset.quoteIds.split(" ")[0]);
      });
    });
  }

  function highlightQuote(quoteId) {
    document.querySelectorAll(".quote-highlight").forEach((el) => {
      el.classList.remove("active-glow");
    });
    const targets = document.querySelectorAll(`[data-quote-ids~="${quoteId}"]`);
    targets.forEach((target) => target.classList.add("active-glow"));
    if (targets.length) {
      targets[0].scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function renderCriteriaCards(criteria) {
    criteriaGrid.innerHTML = "";
    const criterionDisplayNames = {
      task_achievement: "Task Achievement (Task 1)",
      task_response: "Task Response (Task 2)",
      coherence_and_cohesion: "Coherence & Cohesion",
      coherence_cohesion: "Coherence & Cohesion",
      lexical_resource: "Lexical Resource",
      grammatical_range_and_accuracy: "Grammatical Range & Accuracy",
      grammatical_range_accuracy: "Grammatical Range & Accuracy",
    };

    criteria.forEach((crit, idx) => {
      const card = document.createElement("div");
      card.className = "criterion-card";
      card.dataset.crit = crit.criterion;

      const title = criterionDisplayNames[crit.criterion] || crit.criterion;
      const refsHtml = (crit.descriptor_refs || [])
        .map((r) => `<span class="ref-pill">#${escapeHtml(r)}</span>`)
        .join(" ");

      card.innerHTML = `
        <div class="crit-header">
          <span class="crit-title">${title}</span>
          <span class="crit-band">Band ${crit.band.toFixed(1)}</span>
        </div>
        <p class="crit-comment">${escapeHtml(crit.comment)}</p>
        <div class="crit-refs">${refsHtml}</div>
        <button class="btn-view-evidence" data-crit-idx="${idx}">
          🔍 Xem dẫn chứng trên bài viết (${crit.evidence ? crit.evidence.length : 0})
        </button>
      `;

      card.querySelector(".btn-view-evidence").addEventListener("click", (e) => {
        e.stopPropagation();
        highlightQuote(`quote-${idx}-0`);
        document.querySelectorAll(".criterion-card").forEach((c) => c.classList.remove("selected-card"));
        card.classList.add("selected-card");
      });

      card.addEventListener("click", () => {
        highlightQuote(`quote-${idx}-0`);
        document.querySelectorAll(".criterion-card").forEach((c) => c.classList.remove("selected-card"));
        card.classList.add("selected-card");
      });

      criteriaGrid.appendChild(card);
    });
  }

  function renderCorrections(corrections) {
    correctionsList.innerHTML = "";
    if (!corrections || corrections.length === 0) {
      correctionsList.innerHTML = `<p class="empty-state" style="padding: 10px;">Không có lỗi ngữ pháp hoặc từ vựng đáng kể.</p>`;
      return;
    }

    corrections.forEach((item) => {
      const row = document.createElement("div");
      row.className = "correction-card";
      row.innerHTML = `
        <div class="corr-header">
          <span class="corr-tag">${escapeHtml(item.category)}</span>
        </div>
        <div class="corr-diff">
          <span class="corr-orig">"${escapeHtml(item.original)}"</span>
          <span class="corr-arrow">➔</span>
          <span class="corr-sugg">"${escapeHtml(item.suggestion)}"</span>
        </div>
        <div class="corr-reason">💡 <strong>Giải thích:</strong> ${escapeHtml(item.reason)}</div>
      `;
      correctionsList.appendChild(row);
    });
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // --- Event Listeners Setup ---

  function setupEventListeners() {
    // Navigation bar buttons
    navHomeBtn.addEventListener("click", () => switchView("home"));
    navWritingBtn.addEventListener("click", () => switchView("writing"));
    btnBackToHome.addEventListener("click", () => switchView("home"));

    btnStartWriting.addEventListener("click", (e) => {
      e.stopPropagation();
      openWritingOptionsModal();
    });

    // Option 1: "Chọn bài mẫu" -> opens Sample Tests modal
    optSelectSampleBtn.addEventListener("click", () => {
      openSampleTestsModal();
    });

    // Option 2: "Tự thiết kế" -> opens Writing workspace for custom design
    optCustomTestBtn.addEventListener("click", () => {
      closeWritingOptionsModal();
      promptInput.value = "";
      taskMaterialInput.value = "";
      essayInput.value = "";
      presetSelector.value = "";
      updateWordCountDisplay();
      resetAssessmentDisplay();
      switchView("writing");
      promptInput.focus();
    });

    // Close Options Modal
    closeWritingOptionsBtn.addEventListener("click", closeWritingOptionsModal);

    // Open Sample Tests Modal from Writing Workspace
    btnOpenSampleTestsFromEditor.addEventListener("click", openSampleTestsModal);

    // Close Sample Tests Modal (dấu x ở góc trên bên phải để đóng)
    closeSampleTestsBtn.addEventListener("click", closeSampleTestsModal);

    // Close modals on clicking overlay backdrop
    writingOptionsModal.addEventListener("click", (e) => {
      if (e.target === writingOptionsModal) {
        closeWritingOptionsModal();
      }
    });

    sampleTestsModal.addEventListener("click", (e) => {
      if (e.target === sampleTestsModal) {
        closeSampleTestsModal();
      }
    });

    // Close modals on Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeWritingOptionsModal();
        closeSampleTestsModal();
      }
    });

    // Task tabs switching
    tabTask1.addEventListener("click", () => setTask("task1"));
    tabTask2.addEventListener("click", () => setTask("task2"));

    // Real-time word count
    essayInput.addEventListener("input", updateWordCountDisplay);

    // Preset dropdown in editor
    presetSelector.addEventListener("change", (e) => {
      if (e.target.value) {
        loadPreset(e.target.value);
      }
    });

    // Mode Toggle switch
    mockModeToggle.addEventListener("change", async (e) => {
      const isMock = e.target.checked;
      updateModeBadge(isMock);
      try {
        await fetch("/api/config/toggle-mock", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled: isMock }),
        });
      } catch (err) {
        console.warn("Could not sync mock mode with server:", err);
      }
    });

    // Timer buttons
    timerToggleBtn.addEventListener("click", toggleTimer);
    timerResetBtn.addEventListener("click", resetTimer);

    // Clear button
    clearBtn.addEventListener("click", () => {
      if (confirm("Bạn có chắc muốn xóa toàn bộ nội dung bài viết?")) {
        essayInput.value = "";
        updateWordCountDisplay();
      }
    });

    // Submit button
    submitBtn.addEventListener("click", submitEssay);
  }
});
