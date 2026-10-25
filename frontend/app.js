/**
 * Computer-Delivered IELTS Writing Test Application (SE373 UC-02).
 * Simulates the official computer-based IELTS testing experience with:
 * - Real-time countdown timer in header next to IELTS Learning Agent
 * - Split-screen resizable columns with draggable <-> divider
 * - Dynamic instructions banner for Part 1 (20m, 150w) and Part 2 (40m, 250w)
 * - Realtime word counter "Words: 0"
 * - Bottom progress bar with checkmark ticks and green completion status
 * - Bottom-right directional navigation arrows
 * - Review screen showing both Part 1 and Part 2 questions and essays
 * - Confirmation with "Không" (checking time expiration) and "Đồng ý" (Agent assessment)
 * - Rich assessment results view with verbatim quote highlighting & 4 criteria breakdown
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements: Navigation & Layout Views ---
  const homeView = document.getElementById("homeView");
  const writingTestView = document.getElementById("writingTestView");
  const reviewScreenView = document.getElementById("reviewScreenView");
  const resultsView = document.getElementById("resultsView");

  const navHomeBtn = document.getElementById("navHomeBtn");
  const navWritingBtn = document.getElementById("navWritingBtn");
  const btnStartWriting = document.getElementById("btnStartWriting");
  const btnHeaderSubmitExam = document.getElementById("btnHeaderSubmitExam");
  const examTimerBox = document.getElementById("examTimerBox");
  const examTimerDisplay = document.getElementById("examTimerDisplay");


  // Split-screen & Editor Elements
  const cdSplitContainer = document.getElementById("cdSplitContainer");
  const cdLeftPane = document.getElementById("cdLeftPane");
  const cdResizer = document.getElementById("cdResizer");

  const cdInstructionText = document.getElementById("cdInstructionText");

  const cdCurrentPartTitle = document.getElementById("cdCurrentPartTitle");
  const cdPromptTextFormatted = document.getElementById("cdPromptTextFormatted");

  const essayInput = document.getElementById("essayInput");
  const cdWordCountDisplay = document.getElementById("cdWordCountDisplay");

  // Progress Bar & Navigation Arrows
  const progressStepPart1 = document.getElementById("progressStepPart1");
  const progressStepPart2 = document.getElementById("progressStepPart2");
  const btnArrowPrev = document.getElementById("btnArrowPrev");
  const btnArrowNext = document.getElementById("btnArrowNext");

  // Review Screen Elements
  const reviewPart1WcBadge = document.getElementById("reviewPart1WcBadge");
  const reviewPart1PromptText = document.getElementById("reviewPart1PromptText");
  const reviewPart1EssayText = document.getElementById("reviewPart1EssayText");

  const reviewPart2WcBadge = document.getElementById("reviewPart2WcBadge");
  const reviewPart2PromptText = document.getElementById("reviewPart2PromptText");
  const reviewPart2EssayText = document.getElementById("reviewPart2EssayText");

  const timeExpiredNotice = document.getElementById("timeExpiredNotice");
  const btnReviewReject = document.getElementById("btnReviewReject");
  const btnReviewConfirm = document.getElementById("btnReviewConfirm");
  const submitReviewSpinner = document.getElementById("submitReviewSpinner");
  const submitReviewText = document.getElementById("submitReviewText");

  // Results View Elements
  const btnBackToExamFromResults = document.getElementById("btnBackToExamFromResults");
  const btnHomeFromResults = document.getElementById("btnHomeFromResults");
  const tabResultPart1 = document.getElementById("tabResultPart1");
  const tabResultPart2 = document.getElementById("tabResultPart2");
  const scorePartCaption = document.getElementById("scorePartCaption");
  const overallBandValue = document.getElementById("overallBandValue");
  const durationValue = document.getElementById("durationValue");
  const resWordCount = document.getElementById("resWordCount");
  const resExecMode = document.getElementById("resExecMode");
  const disclaimerText = document.getElementById("disclaimerText");
  const flagsContainer = document.getElementById("flagsContainer");
  const highlightedEssayContent = document.getElementById("highlightedEssayContent");
  const criteriaGrid = document.getElementById("criteriaGrid");
  const correctionsList = document.getElementById("correctionsList");
  const emptyResultState = document.getElementById("emptyResultState");
  const assessmentResults = document.getElementById("assessmentResults");

  // Modals Elements
  const writingOptionsModal = document.getElementById("writingOptionsModal");
  const closeWritingOptionsBtn = document.getElementById("closeWritingOptionsBtn");
  const optSelectSampleBtn = document.getElementById("optSelectSampleBtn");
  const optCustomTestBtn = document.getElementById("optCustomTestBtn");

  const sampleTestsModal = document.getElementById("sampleTestsModal");
  const closeSampleTestsBtn = document.getElementById("closeSampleTestsBtn");
  const sampleTestsList = document.getElementById("sampleTestsList");

  // Harmonized regex for word count (matches backend & harness)
  const WORD_REGEX = /\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b/g;

  // --- Fallback Sample Tests Data (100% Người 1 từ evals/data/5_basic_cases.json) ---
  const DEFAULT_SAMPLE_TESTS = [
    {
      id: "member1_standard_set",
      name: "Bộ đề mẫu 01: Chuẩn Band 6.5 – 7.0 (Năng lượng tái tạo & Làm việc từ xa)",
      source: "Bộ dữ liệu Người 1 (evals/data/5_basic_cases.json • Case 01 & Case 02)",
      description: "Bộ đề kiểm thử tiêu chuẩn gồm bài làm mẫu Task 1 (Band 6.5) và Task 2 (Band 7.0).",
      questions: [
        {
          id: "case_01_task1_standard",
          task_type: "task1",
          title: "Task 1: Renewable Energy Production (2010–2020)",
          prompt: "The chart below shows the percentage of electricity generated from renewable sources in four countries between 2010 and 2020. Summarise the information by selecting and reporting the main features.",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: "The bar chart illustrates the proportion of electricity produced from renewable energy sources in four different countries from 2010 to 2020. Overall, it is evident that all four nations experienced an upward trend in renewable power generation over the ten-year period. In 2010, Country A was the leader, accounting for approximately 30% of total electricity production. By 2020, this figure surged dramatically to reach nearly 55%. Country B followed a similar trajectory, rising steadily from 20% to 38%. In contrast, Country C and Country D registered comparatively modest growth throughout the observed timeframe. Country C started at 10% in 2010 and climbed incrementally to finish at 22% in 2020. Finally, Country D remained the lowest throughout, increasing from a mere 5% to 15%. In summary, while renewable electricity output expanded significantly across all four examined countries, Country A maintained the most commanding share throughout the entire decade, demonstrating the most substantial commitment to green energy transition.",
          sample_band: "6.5"
        },
        {
          id: "case_02_task2_standard",
          task_type: "task2",
          title: "Task 2: Remote Working Merits (Employees vs Employers)",
          prompt: "Some people believe that working from home brings more benefits to employees and employers than working in an office. To what extent do you agree or disagree?",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: "In recent years, remote working has emerged as a prominent arrangement across numerous modern industries. I firmly agree that telecommuting provides far greater advantages to both workers and organizations compared to traditional office-based routines.\n\nFirst and foremost, employees experience profound improvements in productivity and work-life balance when working from home. By eliminating exhausting daily commutes, individuals conserve valuable hours each day, which can subsequently be channeled into focused intellectual tasks or healthy personal activities. Moreover, workers operate within a personalized and comfortable domestic environment, significantly minimizing ambient office distractions and stress levels.\n\nFrom the corporate standpoint, businesses can substantially reduce operating expenses through remote work models. Employers are no longer burdened by exorbitant rental costs for commercial office premises, utility bills, and workplace maintenance. Furthermore, companies can recruit exceptional talent globally regardless of geographical constraints, thereby fostering innovation and maintaining a highly competitive advantage in global markets.\n\nIn conclusion, telecommuting delivers indispensable benefits for work flexibility and fiscal efficiency. Both employees and corporate entities should actively embrace flexible remote working policies in the digital age.",
          sample_band: "7.0"
        }
      ]
    },
    {
      id: "member1_underlength_set",
      name: "Bộ đề mẫu 02: Kiểm thử độ dài ngắn (<150 từ & <250 từ)",
      source: "Bộ dữ liệu Người 1 (evals/data/5_basic_cases.json • Case 03a & Case 03b)",
      description: "Bộ đề kiểm thử chế tài trừ điểm bài viết chưa đạt độ dài tối thiểu (Task 1 < 150 từ, Task 2 < 250 từ).",
      questions: [
        {
          id: "case_03a_task1_under_length",
          task_type: "task1",
          title: "Task 1: Water Consumption in 3 Sectors in 2015 (<150 từ)",
          prompt: "The table compares water use in three different sectors in 2015.",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: "The table compares water use in three sectors in 2015. Agriculture consumed 65%, industry consumed 20%, and domestic households consumed 15%. In summary, agricultural activities dominated global water consumption throughout the entire recorded period.",
          sample_band: "5.0"
        },
        {
          id: "case_03b_task2_under_length",
          task_type: "task2",
          title: "Task 2: Free University Education for All Students (<250 từ)",
          prompt: "Some people believe that university education should be free for all students. Discuss.",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: "Free university education is very good for students. When university is free, poor people can study and get good jobs in the future. However, governments need a lot of money to pay for schools, teachers, and libraries. In conclusion, I think tertiary education should be supported by the state.",
          sample_band: "5.0"
        }
      ]
    },
    {
      id: "member1_edge_cases_set",
      name: "Bộ đề mẫu 03: Kiểm thử Lạc đề & Lỗi ngữ pháp cơ bản",
      source: "Bộ dữ liệu Người 1 (evals/data/5_basic_cases.json • Case 04 & Case 05)",
      description: "Bộ đề kiểm thử phát hiện lỗi lạc đề (Off-topic Cap <= 5.0) và phân tích lỗi ngữ pháp.",
      questions: [
        {
          id: "case_04_off_topic_advanced_vocab",
          task_type: "task2",
          title: "Task 2: Nuclear Energy Safety Risks (Kiểm thử Lạc đề)",
          prompt: "Nuclear energy provides a clean source of electricity, but its safety risks are significant. Discuss both views and give your opinion.",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: "Baking a rich chocolate cake requires high-quality ingredients, particularly Dutch-processed cocoa powder and unsalted butter. First, preheat the oven to 175 degrees Celsius and grease two round cake pans thoroughly with flour. In a large bowl, whisk together the dry ingredients including granulated sugar, baking powder, and a pinch of fine salt. Next, gently incorporate fresh eggs, whole milk, and vanilla extract until the batter achieves a smooth, glossy consistency. Carefully pour the batter into the prepared pans and bake for approximately thirty minutes. After allowing the sponges to cool completely on a wire rack, apply decadent chocolate ganache between the layers. This dessert is universally cherished for celebratory gatherings and family celebrations.",
          sample_band: "4.5"
        },
        {
          id: "case_05_basic_grammar_errors",
          task_type: "task2",
          title: "Task 2: Advantages & Disadvantages of Social Media (Lỗi ngữ pháp)",
          prompt: "Do advantages of social media outweigh disadvantages?",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: "Nowadays many people uses social network every day. It have many advantage because people can chat with friends easily. However, some people spends too much times on phone and forget to do homework. In addition, there is many fake news on internet which make people confuse. If government do not control this problem, it will become more worse in the future. In conclusion, social media is useful but we must use it carefully.",
          sample_band: "5.5"
        }
      ]
    }
  ];

  // --- Central Exam Application State ---
  const examState = {
    activePart: "task1", // "task1" (Part 1) or "task2" (Part 2)
    currentView: "home", // "home", "writing", "review", "results"
    timeLeftSeconds: 60 * 60, // 60 minutes countdown default
    timerRunning: false,
    timerInterval: null,
    sampleTestsData: [],
    task1: {
      title: "Writing Task 1",
      prompt: DEFAULT_SAMPLE_TESTS[0].questions[0].prompt,
      essay: "",
      wordCount: 0,
      targetWords: 150,
      completed: false,
    },
    task2: {
      title: "Writing Task 2",
      prompt: DEFAULT_SAMPLE_TESTS[0].questions[1].prompt,
      essay: "",
      wordCount: 0,
      targetWords: 250,
      completed: false,
    },
    results: {
      task1: null,
      task2: null,
    },
    activeResultTab: "task1",
  };

  // --- Initialization ---
  fetchServerConfig();
  fetchSampleTests();
  setupEventListeners();
  setupResizer();
  switchView("home");

  // --- Functions ---

  function countWords(text) {
    if (!text || !text.trim()) return 0;
    const matches = text.match(WORD_REGEX);
    return matches ? matches.length : 0;
  }

  function formatParagraphs(text) {
    if (!text) return "";
    const paras = text.split(/\n\s*\n|\n/);
    return paras
      .map(p => p.trim())
      .filter(p => p.length > 0)
      .map(p => `<p>${escapeHtml(p)}</p>`)
      .join("");
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

  // --- View Switching ---

  function switchView(viewName) {
    examState.currentView = viewName;

    // Hide all main containers
    homeView.classList.add("hidden");
    writingTestView.classList.add("hidden");
    reviewScreenView.classList.add("hidden");
    resultsView.classList.add("hidden");

    // Header buttons state
    navHomeBtn.classList.remove("active");
    navWritingBtn.classList.remove("active");

    if (viewName === "writing") {
      document.body.classList.add("cd-test-active");
      writingTestView.classList.remove("hidden");
      navWritingBtn.classList.add("active");
      btnHeaderSubmitExam.classList.remove("hidden");
      examTimerBox.classList.remove("hidden");
      startExamTimer();
      renderCurrentPart();
    } else {
      document.body.classList.remove("cd-test-active");
      if (viewName === "home") {
        homeView.classList.remove("hidden");
        navHomeBtn.classList.add("active");
        btnHeaderSubmitExam.classList.add("hidden");
        examTimerBox.classList.add("hidden");
        pauseExamTimer();
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else if (viewName === "review") {
        reviewScreenView.classList.remove("hidden");
        navWritingBtn.classList.add("active");
        btnHeaderSubmitExam.classList.remove("hidden");
        examTimerBox.classList.remove("hidden");
        renderReviewScreen();
      } else if (viewName === "results") {
        resultsView.classList.remove("hidden");
        btnHeaderSubmitExam.classList.add("hidden");
        examTimerBox.classList.add("hidden");
        pauseExamTimer();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  }

  // --- Timer Controls ---

  function updateTimerDisplay() {
    const mins = Math.floor(examState.timeLeftSeconds / 60);
    const secs = examState.timeLeftSeconds % 60;
    examTimerDisplay.textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;

    if (examState.timeLeftSeconds <= 300) {
      examTimerBox.style.borderColor = "#ef4444";
      examTimerDisplay.style.color = "#ef4444";
    } else {
      examTimerBox.style.borderColor = "#38bdf8";
      examTimerDisplay.style.color = "#38bdf8";
    }
  }

  function startExamTimer() {
    if (examState.timerRunning) return;
    examState.timerRunning = true;
    updateTimerDisplay();

    examState.timerInterval = setInterval(() => {
      if (examState.timeLeftSeconds > 0) {
        examState.timeLeftSeconds--;
        updateTimerDisplay();
      } else {
        clearInterval(examState.timerInterval);
        examState.timerRunning = false;
        examState.timeLeftSeconds = 0;
        updateTimerDisplay();
        alert("⚠️ Đã hết 60 phút làm bài thi IELTS Writing!");
      }
    }, 1000);
  }

  function pauseExamTimer() {
    if (examState.timerInterval) {
      clearInterval(examState.timerInterval);
    }
    examState.timerRunning = false;
  }

  // --- Computer-Delivered IELTS Workspace Logic ---

  function renderCurrentPart() {
    const isPart1 = examState.activePart === "task1";
    const partData = isPart1 ? examState.task1 : examState.task2;

    // 1. Top Banner: Hộp màu xám nhạt với nội dung hướng dẫn
    if (isPart1) {
      cdInstructionText.textContent = "Part 1 - You should spend about 20 minutes on this task. Write at least 150 words.";
      cdCurrentPartTitle.textContent = "Writing Task 1";
    } else {
      cdInstructionText.textContent = "Part 2 - You should spend about 40 minutes on this task. Write at least 250 words.";
      cdCurrentPartTitle.textContent = "Writing Task 2";
    }

    // 2. Cột trái: Hiển thị đề bài luận văn bản, phân cấp đoạn văn mạch lạc
    cdPromptTextFormatted.innerHTML = formatParagraphs(partData.prompt);
    cdPromptView.classList.remove("hidden");

    // 3. Cột phải: Khung nhập liệu và bộ đếm từ
    essayInput.value = partData.essay;
    const currentWc = countWords(partData.essay);
    partData.wordCount = currentWc;
    cdWordCountDisplay.textContent = currentWc;

    // 4. Thanh tiến trình dưới đáy
    updateProgressBottomBar();

    // 5. Hai biểu tượng mũi tên góc dưới bên phải
    if (isPart1) {
      btnArrowPrev.disabled = true;
      btnArrowPrev.classList.remove("active");
      btnArrowPrev.classList.add("disabled");

      btnArrowNext.disabled = false;
      btnArrowNext.classList.add("active");
      btnArrowNext.classList.remove("disabled");
    } else {
      btnArrowPrev.disabled = false;
      btnArrowPrev.classList.add("active");
      btnArrowPrev.classList.remove("disabled");

      btnArrowNext.disabled = true;
      btnArrowNext.classList.remove("active");
      btnArrowNext.classList.add("disabled");
    }
  }

  function saveCurrentPartText() {
    const currentText = essayInput.value;
    const currentWc = countWords(currentText);

    if (examState.activePart === "task1") {
      examState.task1.essay = currentText;
      examState.task1.wordCount = currentWc;
      if (currentWc > 0) {
        examState.task1.completed = true;
      }
    } else {
      examState.task2.essay = currentText;
      examState.task2.wordCount = currentWc;
      if (currentWc > 0) {
        examState.task2.completed = true;
      }
    }
  }

  function switchPart(targetPart) {
    if (examState.activePart === targetPart) return;

    // Save current active part first
    saveCurrentPartText();

    // Mark previous part completed if user is moving from Part 1 to Part 2
    if (examState.activePart === "task1" && targetPart === "task2") {
      examState.task1.completed = true;
    }

    examState.activePart = targetPart;
    renderCurrentPart();
    essayInput.focus();
  }

  function updateProgressBottomBar() {
    // Part 1 status
    if (examState.task1.completed) {
      progressStepPart1.classList.add("completed");
    } else {
      progressStepPart1.classList.remove("completed");
    }

    // Part 2 status
    if (examState.task2.completed) {
      progressStepPart2.classList.add("completed");
    } else {
      progressStepPart2.classList.remove("completed");
    }

    // Active status
    if (examState.activePart === "task1") {
      progressStepPart1.classList.add("active");
      progressStepPart2.classList.remove("active");
    } else {
      progressStepPart2.classList.add("active");
      progressStepPart1.classList.remove("active");
    }
  }

  // Real-time word counter
  function handleEssayInput() {
    const text = essayInput.value;
    const count = countWords(text);
    cdWordCountDisplay.textContent = count;

    if (examState.activePart === "task1") {
      examState.task1.essay = text;
      examState.task1.wordCount = count;
      if (count > 0) {
        examState.task1.completed = true;
        updateProgressBottomBar();
      }
    } else {
      examState.task2.essay = text;
      examState.task2.wordCount = count;
      if (count > 0) {
        examState.task2.completed = true;
        updateProgressBottomBar();
      }
    }
  }

  // --- Resizable Split-Screen (<-> Draggable Divider) ---

  function setupResizer() {
    let isDragging = false;

    cdResizer.addEventListener("mousedown", (e) => {
      isDragging = true;
      cdResizer.classList.add("active-drag");
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    });

    document.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      const containerRect = cdSplitContainer.getBoundingClientRect();
      const newWidth = e.clientX - containerRect.left;
      const minW = 280;
      const maxW = containerRect.width - 280;

      if (newWidth >= minW && newWidth <= maxW) {
        cdLeftPane.style.width = `${newWidth}px`;
      }
    });

    document.addEventListener("mouseup", () => {
      if (isDragging) {
        isDragging = false;
        cdResizer.classList.remove("active-drag");
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }
    });

    // Touch support for mobile/tablets
    cdResizer.addEventListener("touchstart", (e) => {
      isDragging = true;
      cdResizer.classList.add("active-drag");
    });

    document.addEventListener("touchmove", (e) => {
      if (!isDragging || !e.touches[0]) return;
      const containerRect = cdSplitContainer.getBoundingClientRect();
      const newWidth = e.touches[0].clientX - containerRect.left;
      const minW = 220;
      const maxW = containerRect.width - 220;

      if (newWidth >= minW && newWidth <= maxW) {
        cdLeftPane.style.width = `${newWidth}px`;
      }
    });

    document.addEventListener("touchend", () => {
      isDragging = false;
      cdResizer.classList.remove("active-drag");
    });
  }

  // --- Review Screen Logic ---

  function renderReviewScreen() {
    saveCurrentPartText();
    timeExpiredNotice.classList.add("hidden");

    // Part 1 Review Content
    reviewPart1WcBadge.textContent = `Words: ${examState.task1.wordCount}`;
    reviewPart1PromptText.textContent = examState.task1.prompt || "(Chưa có đề bài)";
    reviewPart1EssayText.textContent = examState.task1.essay || "(Học viên chưa nhập bài làm Part 1)";

    // Part 2 Review Content
    reviewPart2WcBadge.textContent = `Words: ${examState.task2.wordCount}`;
    reviewPart2PromptText.textContent = examState.task2.prompt || "(Chưa có đề bài)";
    reviewPart2EssayText.textContent = examState.task2.essay || "(Học viên chưa nhập bài làm Part 2)";
  }

  function handleReviewReject() {
    // Kiểm tra nếu hết thời gian thì hiển thị thông báo "Đã hết thời gian làm bài"
    if (examState.timeLeftSeconds <= 0) {
      timeExpiredNotice.classList.remove("hidden");
      alert("⚠️ Đã hết thời gian làm bài! Bạn không thể quay lại chỉnh sửa.");
      return;
    }

    // Nếu còn thời gian, quay lại lúc làm bài
    switchView("writing");
  }

  async function handleReviewConfirm() {
    // 1. Thêm tick và chuyển thanh tiến trình Part 2 sang màu xanh lá
    examState.task2.completed = true;
    updateProgressBottomBar();

    // 2. Dừng đồng hồ làm bài
    pauseExamTimer();

    // 3. Kiểm tra xem có bài làm nào để chấm không
    const hasPart1 = Boolean(examState.task1.essay.trim());
    const hasPart2 = Boolean(examState.task2.essay.trim());

    if (!hasPart1 && !hasPart2) {
      alert("Vui lòng nhập bài làm cho ít nhất Part 1 hoặc Part 2 trước khi nộp!");
      switchView("writing");
      return;
    }

    // Hiển thị trạng thái đang chấm
    submitReviewSpinner.classList.remove("hidden");
    submitReviewText.textContent = "Đang thẩm định & Chấm bài...";
    btnReviewConfirm.disabled = true;

    try {
      // Đưa Agent chấm bài
      if (hasPart2) {
        examState.results.task2 = await requestAssessment("task2", examState.task2.prompt, examState.task2.essay);
      }
      if (hasPart1) {
        examState.results.task1 = await requestAssessment("task1", examState.task1.prompt, examState.task1.essay);
      }

      // Mặc định hiển thị tab kết quả của bài viết có nội dung (ưu tiên Part 2)
      examState.activeResultTab = hasPart2 ? "task2" : "task1";

      // Chuyển sang màn hình kết quả phân tích
      switchView("results");
      renderAssessmentResults();
    } catch (err) {
      alert(`Lỗi khi Agent thẩm định bài: ${err.message}`);
      console.error(err);
    } finally {
      submitReviewSpinner.classList.add("hidden");
      submitReviewText.textContent = "Đồng ý";
      btnReviewConfirm.disabled = false;
    }
  }

  async function requestAssessment(taskType, prompt, essay) {
    const payload = {
      task_type: taskType,
      prompt: prompt.trim(),
      essay: essay.trim(),
    };

    const res = await fetch("/api/assess-writing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error (${res.status})`);
    }

    return await res.json();
  }

  // --- Assessment Results Rendering (Giao diện chấm bài cũ) ---

  function renderAssessmentResults() {
    const currentRes = examState.results[examState.activeResultTab];
    if (!currentRes || !currentRes.assessment) {
      emptyResultState.classList.remove("hidden");
      assessmentResults.classList.add("hidden");
      return;
    }

    emptyResultState.classList.add("hidden");
    assessmentResults.classList.remove("hidden");

    const a = currentRes.assessment;
    const isPart1 = examState.activeResultTab === "task1";

    // Tab buttons state
    if (isPart1) {
      tabResultPart1.classList.add("active");
      tabResultPart2.classList.remove("active");
      scorePartCaption.textContent = "Điểm ước lượng Part 1";
    } else {
      tabResultPart2.classList.add("active");
      tabResultPart1.classList.remove("active");
      scorePartCaption.textContent = "Điểm ước lượng Part 2";
    }

    // Score Header
    overallBandValue.textContent = a.overall_band.toFixed(1);
    durationValue.textContent = `${currentRes.duration_ms} ms`;
    resWordCount.textContent = a.word_count;
    resExecMode.textContent = currentRes.execution_mode.toUpperCase();
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
    const rawEssay = isPart1 ? examState.task1.essay : examState.task2.essay;
    renderInteractiveEssay(rawEssay, a.criteria);

    // Render 4 Criteria Cards
    renderCriteriaCards(a.criteria);

    // Render Actionable Corrections
    renderCorrections(a.corrections);
  }

  function renderInteractiveEssay(essayText, criteria) {
    const spans = [];
    criteria.forEach((crit, critIdx) => {
      if (crit.evidence && Array.isArray(crit.evidence)) {
        crit.evidence.forEach((ev, evIdx) => {
          if (ev.quote && typeof ev.start_char === "number" && typeof ev.end_char === "number") {
            spans.push({
              quote: ev.quote,
              start: ev.start_char,
              end: ev.end_char,
              criterion: crit.criterion,
              comment: crit.comment,
              critIdx: critIdx,
              id: `quote-${critIdx}-${evIdx}`,
            });
          }
        });
      }
    });

    spans.sort((a, b) => a.start - b.start);

    let html = "";
    let lastIndex = 0;

    spans.forEach((sp) => {
      if (sp.start > lastIndex) {
        html += escapeHtml(essayText.slice(lastIndex, sp.start));
      }
      if (sp.start >= lastIndex && sp.end <= essayText.length) {
        const sliceText = essayText.slice(sp.start, sp.end);
        html += `<mark class="quote-highlight" id="${sp.id}" data-crit="${sp.criterion}" title="Tiêu chí: ${sp.criterion} - Nhận xét: ${sp.comment}">${escapeHtml(sliceText)}</mark>`;
        lastIndex = sp.end;
      }
    });

    if (lastIndex < essayText.length) {
      html += escapeHtml(essayText.slice(lastIndex));
    }

    highlightedEssayContent.innerHTML = html;

    document.querySelectorAll(".quote-highlight").forEach((el) => {
      el.addEventListener("click", () => {
        highlightQuote(el.id);
      });
    });
  }

  function highlightQuote(quoteId) {
    document.querySelectorAll(".quote-highlight").forEach((el) => {
      el.classList.remove("active-glow");
    });
    const target = document.getElementById(quoteId);
    if (target) {
      target.classList.add("active-glow");
      target.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function renderCriteriaCards(criteria) {
    criteriaGrid.innerHTML = "";
    const criterionDisplayNames = {
      task_achievement: "Task Achievement (Task 1)",
      task_response: "Task Response (Task 2)",
      coherence_and_cohesion: "Coherence & Cohesion",
      lexical_resource: "Lexical Resource",
      grammatical_range_and_accuracy: "Grammatical Range & Accuracy",
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

  // --- Modals & Sample Tests (Người 1) ---

  async function fetchServerConfig() {
    try {
      await fetch("/api/config");
    } catch (e) {
      console.warn("Could not fetch server config, using local defaults.", e);
    }
  }

  async function fetchSampleTests() {
    try {
      const res = await fetch("/api/sample-tests");
      if (res.ok) {
        examState.sampleTestsData = await res.json();
      } else {
        examState.sampleTestsData = DEFAULT_SAMPLE_TESTS;
      }
    } catch (e) {
      console.warn("Could not fetch /api/sample-tests, using local default tests.", e);
      examState.sampleTestsData = DEFAULT_SAMPLE_TESTS;
    }
  }

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

  function renderSampleTestsList() {
    sampleTestsList.innerHTML = "";
    const list = examState.sampleTestsData.length > 0 ? examState.sampleTestsData : DEFAULT_SAMPLE_TESTS;

    list.forEach((test, testIdx) => {
      const card = document.createElement("div");
      card.className = "sample-test-card";
      card.id = `testCard-${test.id || testIdx}`;

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

      const drawer = document.createElement("div");
      drawer.className = "sample-questions-drawer hidden";
      drawer.id = `drawer-${testIdx}`;

      // Lấy 2 câu hỏi Task 1 và Task 2 của bộ đề
      let q1 = (test.questions || []).find(q => q.task_type === "task1");
      let q2 = (test.questions || []).find(q => q.task_type === "task2" && q !== q1);

      if (!q1 && !q2 && test.questions && test.questions.length > 0) {
        q1 = test.questions[0];
        if (test.questions.length > 1) q2 = test.questions[1];
      } else if (!q1 && q2) {
        q1 = (test.questions || []).find(q => q !== q2);
      } else if (q1 && !q2) {
        q2 = (test.questions || []).find(q => q !== q1);
      }

      // Giá trị mặc định nếu thiếu
      if (!q1) {
        q1 = {
          task_type: "task1",
          title: "Writing Task 1",
          prompt: DEFAULT_SAMPLE_TESTS[0].questions[0].prompt,
          suggested_time: "20 phút",
          min_words: 150
        };
      }
      if (!q2) {
        q2 = {
          task_type: "task2",
          title: "Writing Task 2",
          prompt: DEFAULT_SAMPLE_TESTS[0].questions[1].prompt,
          suggested_time: "40 phút",
          min_words: 250
        };
      }

      const timeReq1 = q1.suggested_time || "20 phút";
      const wordReq1 = q1.min_words ? `Min ${q1.min_words} từ` : "Min 150 từ";
      const timeReq2 = q2.suggested_time || "40 phút";
      const wordReq2 = q2.min_words ? `Min ${q2.min_words} từ` : "Min 250 từ";

      // Hiển thị duy nhất một khối gồm: Writing Task 1, Writing Task 2, và nút Chọn đề thi màu xanh lá ở góc dưới bên phải
      drawer.innerHTML = `
        <div class="sample-test-bundle-block">
          <!-- Đề Writing Task 1 -->
          <div class="bundle-task-section">
            <div class="question-item-header">
              <span class="task-badge badge-task1">Writing Task 1</span>
              <span class="question-meta-info">⏱ ${escapeHtml(timeReq1)} • 📝 ${escapeHtml(wordReq1)}</span>
            </div>
            <h5 class="question-item-title">${escapeHtml(q1.title || "Writing Task 1")}</h5>
            <div class="question-prompt-text">${escapeHtml(q1.prompt)}</div>
          </div>

          <!-- Đường phân cách giữa Task 1 và Task 2 -->
          <div class="bundle-task-divider"></div>

          <!-- Đề Writing Task 2 -->
          <div class="bundle-task-section">
            <div class="question-item-header">
              <span class="task-badge badge-task2">Writing Task 2</span>
              <span class="question-meta-info">⏱ ${escapeHtml(timeReq2)} • 📝 ${escapeHtml(wordReq2)}</span>
            </div>
            <h5 class="question-item-title">${escapeHtml(q2.title || "Writing Task 2")}</h5>
            <div class="question-prompt-text">${escapeHtml(q2.prompt)}</div>
          </div>

          <!-- Nút Chọn đề thi nằm phía dưới bên phải màu xanh lá -->
          <div class="bundle-footer-row">
            <button type="button" class="btn-select-test-green" data-test-idx="${testIdx}">
              Chọn đề thi
            </button>
          </div>
        </div>
      `;

      function toggleDrawer() {
        const isHidden = drawer.classList.contains("hidden");
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

    sampleTestsList.querySelectorAll(".btn-select-test-green").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const testIdx = parseInt(btn.dataset.testIdx, 10);
        const loadSample = Boolean(e.shiftKey);
        loadTestSetIntoExam(testIdx, loadSample);
      });
    });
  }

  function loadTestSetIntoExam(testIdx, loadSampleEssay = false) {
    const list = examState.sampleTestsData.length > 0 ? examState.sampleTestsData : DEFAULT_SAMPLE_TESTS;
    const test = list[testIdx];
    if (!test || !test.questions) return;

    let q1 = test.questions.find(q => q.task_type === "task1");
    let q2 = test.questions.find(q => q.task_type === "task2" && q !== q1);

    if (!q1 && !q2 && test.questions.length > 0) {
      q1 = test.questions[0];
      if (test.questions.length > 1) q2 = test.questions[1];
    } else if (!q1 && q2) {
      q1 = test.questions.find(q => q !== q2);
    } else if (q1 && !q2) {
      q2 = test.questions.find(q => q !== q1);
    }

    if (!q1) {
      q1 = { prompt: DEFAULT_SAMPLE_TESTS[0].questions[0].prompt };
    }
    if (!q2) {
      q2 = { prompt: DEFAULT_SAMPLE_TESTS[0].questions[1].prompt };
    }

    examState.task1.prompt = q1.prompt;
    examState.task1.essay = (loadSampleEssay && q1.sample_essay) ? q1.sample_essay : "";
    examState.task1.wordCount = countWords(examState.task1.essay);
    examState.task1.completed = examState.task1.wordCount > 0;

    examState.task2.prompt = q2.prompt;
    examState.task2.essay = (loadSampleEssay && q2.sample_essay) ? q2.sample_essay : "";
    examState.task2.wordCount = countWords(examState.task2.essay);
    examState.task2.completed = examState.task2.wordCount > 0;

    examState.activePart = "task1";
    examState.timeLeftSeconds = 60 * 60;

    closeSampleTestsModal();
    switchView("writing");
  }

  // --- Event Listeners Setup ---

  function setupEventListeners() {
    // Navigation bar buttons
    navHomeBtn.addEventListener("click", () => switchView("home"));
    navWritingBtn.addEventListener("click", () => switchView("writing"));
    btnHomeFromResults.addEventListener("click", () => switchView("home"));
    btnBackToExamFromResults.addEventListener("click", () => switchView("writing"));

    // Home: Start writing test button opens options modal
    btnStartWriting.addEventListener("click", (e) => {
      e.stopPropagation();
      openWritingOptionsModal();
    });

    // Options modal choices
    optSelectSampleBtn.addEventListener("click", openSampleTestsModal);
    optCustomTestBtn.addEventListener("click", () => {
      closeWritingOptionsModal();
      // Clean custom exam
      examState.task1.prompt = "The table below shows information about water consumption. Summarise the information by selecting and reporting the main features.";
      examState.task1.essay = "";
      examState.task1.wordCount = 0;
      examState.task1.completed = false;

      examState.task2.prompt = "Some people believe that university education should be free for all students. Discuss both views and give your opinion.";
      examState.task2.essay = "";
      examState.task2.wordCount = 0;
      examState.task2.completed = false;

      examState.activePart = "task1";
      examState.timeLeftSeconds = 60 * 60;

      switchView("writing");
    });

    closeWritingOptionsBtn.addEventListener("click", closeWritingOptionsModal);
    closeSampleTestsBtn.addEventListener("click", closeSampleTestsModal);

    // Close modals on clicking overlay backdrop
    writingOptionsModal.addEventListener("click", (e) => {
      if (e.target === writingOptionsModal) closeWritingOptionsModal();
    });
    sampleTestsModal.addEventListener("click", (e) => {
      if (e.target === sampleTestsModal) closeSampleTestsModal();
    });

    // Close modals on Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeWritingOptionsModal();
        closeSampleTestsModal();
      }
    });

    // Header "Nộp bài" button: opens review screen
    btnHeaderSubmitExam.addEventListener("click", () => {
      saveCurrentPartText();
      examState.task2.completed = true;
      updateProgressBottomBar();
      switchView("review");
    });

    // Review Screen Actions:
    // Nút trái: "Không" ô màu xám (kiểm tra hết giờ thì thông báo, còn giờ thì quay lại)
    btnReviewReject.addEventListener("click", handleReviewReject);

    // Nút phải: "Đồng ý" ô màu xanh lá (chấm bài và hiển thị kết quả)
    btnReviewConfirm.addEventListener("click", handleReviewConfirm);

    // Bottom Navigation Arrows
    btnArrowPrev.addEventListener("click", () => switchPart("task1"));
    btnArrowNext.addEventListener("click", () => switchPart("task2"));

    // Progress Bar Steps click
    progressStepPart1.addEventListener("click", () => switchPart("task1"));
    progressStepPart2.addEventListener("click", () => switchPart("task2"));

    // Realtime word counter
    essayInput.addEventListener("input", handleEssayInput);

    // Results Tab Switch (Part 1 vs Part 2 results)
    tabResultPart1.addEventListener("click", () => {
      examState.activeResultTab = "task1";
      renderAssessmentResults();
    });

    tabResultPart2.addEventListener("click", () => {
      examState.activeResultTab = "task2";
      renderAssessmentResults();
    });


  }
});
