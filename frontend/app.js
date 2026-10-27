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
  const progressLine = document.getElementById("progressLine");
  const cdNavArrows = document.getElementById("cdNavArrows");
  const btnArrowPrev = document.getElementById("btnArrowPrev");
  const btnArrowNext = document.getElementById("btnArrowNext");

  // Review Screen Elements
  const reviewCardPart1 = document.getElementById("reviewCardPart1");
  const reviewCardPart2 = document.getElementById("reviewCardPart2");
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
  const btnHomeFromResults = document.getElementById("btnHomeFromResults");
  const resultsTaskTabs = document.getElementById("resultsTaskTabs");
  const tabResultPart1 = document.getElementById("tabResultPart1");
  const tabResultPart2 = document.getElementById("tabResultPart2");
  const scorePartCaption = document.getElementById("scorePartCaption");
  const overallBandValue = document.getElementById("overallBandValue");
  const durationValue = document.getElementById("durationValue");
  const examDurationValue = document.getElementById("examDurationValue");
  const resWordCount = document.getElementById("resWordCount");
  const disclaimerText = document.getElementById("disclaimerText");
  const flagsContainer = document.getElementById("flagsContainer");
  const highlightedEssayContent = document.getElementById("highlightedEssayContent");
  const criteriaGrid = document.getElementById("criteriaGrid");
  const correctionsList = document.getElementById("correctionsList");
  const emptyResultState = document.getElementById("emptyResultState");
  const assessmentResults = document.getElementById("assessmentResults");

  // Pedagogical Elements
  const topPrioritiesSection = document.getElementById("topPrioritiesSection");
  const topPrioritiesList = document.getElementById("topPrioritiesList");
  const errorPatternsSection = document.getElementById("errorPatternsSection");
  const errorPatternsList = document.getElementById("errorPatternsList");
  const sentenceRewritesSection = document.getElementById("sentenceRewritesSection");
  const sentenceRewritesList = document.getElementById("sentenceRewritesList");
  const paragraphAnalysisSection = document.getElementById("paragraphAnalysisSection");
  const paragraphAnalysesList = document.getElementById("paragraphAnalysesList");
  const grammarRulesSection = document.getElementById("grammarRulesSection");
  const grammarRulesList = document.getElementById("grammarRulesList");
  const modelSentencesSection = document.getElementById("modelSentencesSection");
  const modelSentencesList = document.getElementById("modelSentencesList");

  // Modal Elements
  const sampleTestsModal = document.getElementById("sampleTestsModal");
  const closeSampleTestsBtn = document.getElementById("closeSampleTestsBtn");
  const sampleTestsList = document.getElementById("sampleTestsList");

  // Harmonized regex for word count (matches backend & harness)
  const WORD_REGEX = /\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b/g;

  // --- Authentic IELTS Practice Tests for Learners (from Official IELTS sources) ---
  const DEFAULT_SAMPLE_TESTS = [
    {
      id: "ielts_practice_test_01",
      name: "Bộ đề thi IELTS Academic 01",
      source: "IELTS.org Official Academic Sample",
      description: "Đề thi thực hành chính thức gồm Writing Task 1 (Biểu đồ cột) và Writing Task 2 (Nghị luận xã hội).",
      questions: [
        {
          id: "practice_01_task1",
          task_type: "task1",
          title: "Task 1: Trips Made by Children to School (1990 & 2010)",
          prompt: "The chart below shows the number of trips made by children in one country in 1990 and 2010 to travel to and from school using different modes of transport. Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words.\n\nChart key: solid black bars = 1990; hatched bars = 2010. The chart covers children aged 5-12. The vertical axis shows the total number of trips per year, in millions.",
          material: "/materials/basic_cases_school_trips.jpg",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: "The chart gives you information on how children travelled to and from school in the years 1990 and 2010. The modes of transport were by car, walking, cycling, walking and by bus and by bus only.\n\nA striking feature in this chart is that the number of children who travelled by car has increased from 1990 to 2010. In 1990 the most number of trips per year by children were by walking. However in 2010 it reduced to up to 6 million trips per year. The total number of trips to school by cycling and walking and bus were approximately 6 million in 1990. However the number of trips to school by cycling reduced to 2 million and the number of trips to school by walking and bus reduced to about 3 million in 2010. There isn’t a significant change to the number of trips to school by bus. In 1990 it was about 7 million and in 2010 it came down to approximately 5 million.\n\nIn 1990 the amount of children who travelled to and from school by car was significantly lower than the children who travelled by walking. In contrast in 2010 the number of children who travelled to school by car increased and the number of children walking to school has decreased.",
          sample_band: "6.5"
        },
        {
          id: "practice_01_task2",
          task_type: "task2",
          title: "Task 2: Future Health Standard",
          prompt: "The average standard of people's health is likely to be lower in the future than it is now. To what extent do you agree or disagree with this statement? Give reasons for your answer and include any relevant examples from your own knowledge or experience. Write at least 250 words.",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: "Some people believe that the average standard of people's health is likely to be lower in the future than it is now. In my opinion, I disagree with this point of view.\n\nFirst of all, medical science and technology are developing rapidly. Physicians and researchers can now cure and treat numerous illnesses that were previously incurable. Furthermore, continuous breakthroughs in preventative medicine, genetic therapies, and advanced surgical interventions are significantly enhancing life expectancy and physical vitality across populations.\n\nSecondly, contemporary societies exhibit heightened awareness regarding personal wellbeing, nutrition, and exercise. Widespread access to health information empowers citizens to adopt balanced diets, curb harmful habits such as smoking, and engage in active lifestyles. Governments also invest substantially in public healthcare infrastructure and recreational facilities.\n\nIn conclusion, despite contemporary challenges related to sedentary lifestyles and processed foods, ongoing medical advancements and informed lifestyle choices will ensure higher health standards in the future.",
          sample_band: "7.0"
        }
      ]
    },
    {
      id: "ielts_practice_test_02",
      name: "Bộ đề thi IELTS Academic 02",
      source: "Cambridge IELTS Official Practice",
      description: "Đề thi thực hành chuẩn Cambridge gồm Writing Task 1 (Biểu đồ đường) và Writing Task 2 (Thảo luận quan điểm giáo dục).",
      questions: [
        {
          id: "practice_02_task1",
          task_type: "task1",
          title: "Task 1: Energy Consumption in the USA (1980–2030)",
          prompt: "The graph below gives information from a report about consumption of energy in the USA since 1980 with projections until 2030. Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words.",
          material: "/materials/uc02_063fb5734c0491b3_1.png",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: "The line graph illustrates energy consumption trends in the United States across six different fuel sources from 1980, with future projections up to 2030.\n\nOverall, fossil fuels have historically dominated and are expected to continue leading overall consumption throughout the period. Petrol and oil consistently represent the largest share, starting at 35 quadrillion units in 1980 and projected to rise steadily to nearly 50 quadrillion by 2030.\n\nNatural gas and coal experienced similar consumption levels in 1980 at approximately 20 quadrillion units each. However, while coal shows a gradual upward trajectory reaching about 31 quadrillion units, natural gas fluctuates before stabilizing around 25 quadrillion.\n\nIn contrast, cleaner energy sources—nuclear, solar/wind, and hydropower—remain comparatively minor contributors, each remaining below 10 quadrillion units over the entire projected timeframe.",
          sample_band: "7.5"
        },
        {
          id: "practice_02_task2",
          task_type: "task2",
          title: "Task 2: Free University Education Funding",
          prompt: "Some people feel that the government should pay the costs of running universities so that a university education is free for all students. To what extent do you agree or disagree with this opinion? Give reasons for your answer and include any relevant examples from your own knowledge or experience. Write at least 250 words.",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: "Access to tertiary education remains a vital catalyst for socio-economic mobility. While some contend that public treasuries should fully subsidize university tuition for every citizen, I believe that a cost-sharing model is both more economically viable and socially equitable.\n\nOn the one hand, abolishing university tuition removes financial obstacles for gifted students from underprivileged backgrounds. When academic admission is purely meritocratic rather than constrained by wealth, society maximizes intellectual capital and accelerates innovation.\n\nOn the other hand, funding universal tertiary education places an immense fiscal burden on taxpayers, which can lead to diminished educational quality and underfunded facilities. Since university graduates typically command significantly higher lifetime earnings, it is reasonable that recipients contribute partially toward their credentials through income-contingent loans.\n\nIn conclusion, while governments should guarantee comprehensive scholarships for disadvantaged students, full public subsidization for all students is neither sustainable nor necessary.",
          sample_band: "7.5"
        }
      ]
    },
    {
      id: "ielts_practice_test_03",
      name: "Bộ đề thi IELTS Academic 03",
      source: "British Council & IDP Sample Tests",
      description: "Đề thi thực hành chính thức gồm Writing Task 1 (Sơ đồ quy trình sản xuất) và Writing Task 2 (Đô thị và phát triển vùng).",
      questions: [
        {
          id: "practice_03_task1",
          task_type: "task1",
          title: "Task 1: Biofuel Ethanol Production Process",
          prompt: "The diagram below shows how a biofuel called ethanol is produced. Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words.",
          material: "/materials/uc02_1e82eae284e2726c_1.png",
          min_words: 150,
          suggested_time: "20 phút",
          sample_essay: "The flowchart illustrates the sequential industrial stages involved in manufacturing ethanol biofuel.\n\nOverall, ethanol production is a circular biochemical process comprising plant cultivation, mechanical processing, chemical fermentation, and final product distribution.\n\nInitially, crops absorb sunlight and atmospheric carbon dioxide during growth. Once mature, plants are harvested and mechanically shredded into fine cellulose fibers. The pre-processed material then undergoes chemical pretreatment to release essential sugars.\n\nSubsequently, microbes and enzymes are introduced to ferment the sugars into ethanol liquid. Following purification, the refined fuel is transported to filling stations for commercial vehicular use, ultimately releasing carbon dioxide that is re-absorbed by newly planted vegetation.",
          sample_band: "7.0"
        },
        {
          id: "practice_03_task2",
          task_type: "task2",
          title: "Task 2: Urban Congestion & Regional Development",
          prompt: "People living in big cities face several problems. What are these problems? Should governments encourage city residents to move to regional towns? Give reasons for your answer and include any relevant examples from your own knowledge or experience. Write at least 250 words.",
          min_words: 250,
          suggested_time: "40 phút",
          sample_essay: "Rapid urbanization across the globe has exacerbated numerous difficulties for metropolis inhabitants, notably severe traffic congestion, exorbitant housing costs, and escalating air pollution.\n\nTraffic gridlock consumes precious productive hours and induces psychological stress, while inflated real estate pricing forces younger demographics into precarious living situations. To alleviate these acute pressures, governmental initiatives aimed at decentralization and regional relocation represent a pragmatic and strategic remedy.\n\nBy offering corporate tax incentives and improving intercity transport infrastructure, authorities can motivate businesses and families to relocate to regional towns. This not only decompresses congested metropolises but also invigorates regional economic development and spreads prosperity equitably.\n\nIn conclusion, addressing urban distress requires proactive state intervention to stimulate balanced regional migration and sustainable infrastructure development.",
          sample_band: "7.5"
        }
      ]
    }
  ];

  const DEFAULT_BENCHMARK_TASKS = {
  "task1": [
    {
      "id": "uc02_063fb5734c0491b3_1",
      "task_type": "task1",
      "title": "Task 1: The graph below gives information from a 2008 report about consum...",
      "prompt": "The graph below gives information from a 2008 report about consumption of energy in the USA since 1980 with projections until 2030.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_063fb5734c0491b3_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-2829-band-5-5/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The graph illustrates the consumption of six categories of fuel in the USA in the year 1980 to 2008 and their prediction until 2030.\n\nTo begin with, it is noticeable that all kinds of energy had an upward trend except hydropower, which was a roughly steady pattern with an amount of 3 quadrillions unite (qu) between the year 1980 and 2030. With respect to the given graph, the highest usage was petrol and oil which was beginning from 35 quadrillions unite in the year 1980 with a dramatic increasing trend while the projections demonstrate it will be raised more than 45 (qu) in 2030. The secondly ranked was related to coal which was 16 (qu) in 1980. It is worth mentioning that it had a similar sharp climbing movement likes fossil fuel such as petrol and oil while in the end it will be reached 30 (qu) in 2030.\n\nOn the other hand, natural gas, nuclear, and solar/wind energy had a gradual rise. It is noteworthy that both nuclear and solar/wind sources had the same rate of consumption in 1980 that was almost 4 (qu), whereas the predictions show that people prefer to utilize nuclear more than solar/wind energy in the future.  However, natural gas had a similar movement but its utilization was equal to 20 (qu) in the year 1980 which will be arisen to 24 (qu) according to projections.\n\nTo sum up, it can be clearly seen that the fossil fuel practically petrol and oil was the most popular resource of energy in the USA and it will be the most common source till 2030.",
      "sample_band": "5.5"
    },
    {
      "id": "uc02_1e82eae284e2726c_1",
      "task_type": "task1",
      "title": "Task 1: The diagram below shows how a biofuel called ethanol is produced....",
      "prompt": "The diagram below shows how a biofuel called ethanol is produced.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_1e82eae284e2726c_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3433-band-8-0/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The diagram drawn below clearly illustrates the cycle of ethanol which is considered a biofuel. There are seven steps until ethanol reaches a level where it is used as fuel.\n\nThe entire process commences when trees and plants require energy to grow. This energy has two main components: carbon dioxide (CO2) and sunlight absorbed by plants and trees. Later, these plants and trees are harvested and fed into a preprocessing unit. The outcome is cellulose which begins the processing phase to form sugar molecules. In the end, special microbes are added so that ethanol can be produced.\n\nThe produced ethanol is fuel for airplanes, trucks, and cars. Once consumed, carbon dioxide is emitted into the atmosphere. The CO2 later cycles back to be absorbed by more trees and plants. Overall, ethanol’s journey to becoming a biofuel is lengthy; its application ranges from passenger cars to ground logistics and even aviation.",
      "sample_band": "8.0"
    },
    {
      "id": "uc02_2379a300f77b0c13_1",
      "task_type": "task1",
      "title": "Task 1: The figures give information about economic growth and household ...",
      "prompt": "The figures give information about economic growth and household expenditure across a range of categories.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_2379a300f77b0c13_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3317-band-7-0/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The line graph and pie charts given provide data on economic growth, as well as household spending patterns in housing, food, clothing, entertainment, travel, and other from 1995 to 2010.\n\nIn 1995, economic growth was approximately 1 per cent. The pie chart for that year illustrates that the spending on essentials such as housing and food accounted for two-thirds of overall household expenses; whereas, the spending on less crucial categories like clothing, entertainment, and travel was way lower at roughly 20 per cent.\n\nBy 2000, the growth has nearly doubled and expenditure on housing has shrunk to roughly one-quarter of total spending. On the other hand, expenses on food and non-essential items had risen. The trend of expansion of the latter category was even more evident in 2005, when the growth of economy had reached approximately 4.5 per cent.\n\nNevertheless, the trend had reversed when in 2010 growth returned to 1 per cent caused by economic decline. The breakdown of expenditure was similar to the pattern marked in 1995. Moreover, the decrease in non-essential spending was even more evident.\n\nOverall, the figures show that household expenditures were affected by economic growth.",
      "sample_band": "7.0"
    },
    {
      "id": "uc02_46ad2e8773a6a1e5_1",
      "task_type": "task1",
      "title": "Task 1: The maps below show an industrial area in the town of Norbiton, a...",
      "prompt": "The maps below show an industrial area in the town of Norbiton, and planned future development of the site.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_46ad2e8773a6a1e5_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3413-band-6-5/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The maps illustrate the present industrial area of Norbiton town and the proposed development in the future.\n\nOverall, the industrial area will observe drastic changes in its layout, ; namely, factories will be completely taken over by housing and amenities such as a school.\n\nThe current industrial area has a big roundabout in the centre that can be accessed from the road to its south. To this roundabout, there are three factories encircling it from south-west to the north. The site eastern’s side The site’s eastern side houses five factories, which can be reached via a lane. Across the northern part, farmland is present adjacent to a river.\n\nThe anticipated makeover will witness the addition of a small roundabout, by modifying the southern outlet, and joining the big roundabout. The big roundabout will also be transformed to accommodate two additional lanes. Factories on either side of the roundabout will be replaced by residential housing and other facilities like shops, a medical centre, and a playground. In the north, a T-shape road and a bridge will be constructed to access the housing on the farmland.",
      "sample_band": "6.5"
    },
    {
      "id": "uc02_636fdb29eb315501_1",
      "task_type": "task1",
      "title": "Task 1: The diagrams below show the changes that have taken place at West...",
      "prompt": "The diagrams below show the changes that have taken place at West Park Secondary School since its construction in 1950.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_636fdb29eb315501_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3081-band-5-0/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The given diagrams illustrates some alters in construction of secondary school at west park between 1950 and 2010. Overall, science block cannot be seen in 1950,however, in 1980 and 30 years later, 2010, the block is easily noticeable.\n\nAccording to the graph, houses have been omitted in 1980 and it is devoted to car park which was not available in 1950. It is noteworthy that in 2010 the car park is more spacious due in part to limitation of sports field and play ground.\n\nIn 1950, there is a farmland which is about 25 percent of the map, and it changed to sports field after 30 years and in 2010 the size changed to half.\n\nSize and location of main building remained fairly stable(on the right side of the map) and does not meet any changes during the mentioned years.",
      "sample_band": "5.0"
    },
    {
      "id": "uc02_963ff6b5def57655_1",
      "task_type": "task1",
      "title": "Task 1: The pie chart below shows the main reasons why agricultural land ...",
      "prompt": "The pie chart below shows the main reasons why agricultural land becomes less productive. The table shows how these causes affected three regions of the world during the 1990s.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_963ff6b5def57655_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3156-band-4-5/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The pie chart and table could noticed that what reasons are pivotal and essential for demolishing lands.\n\nOverall, as can be seen from the the most effective causes of land degradation is over-grazing by worldwide and it is clear from the table that Europe is a region which have the most impression on the land degradation.\n\nGetting back to details, the first and more importantly reason for demolishing is over-grazing by some domestic animals which its percentage is 35% after that the second reason is deforestation which its percentage is similar to over-grazing approximately (30%),the third reason is over-cultivation that  is roughly a quarter  and the last one is some other reasons that is included a tiny fraction.\n\nAs is illustrated by the table, the most percentage of over-grazing which was the main reason on the pie chart  above is allocated to Oceania which is included some islands such as  Australia and New Zealand; moreover, the enormous percentage of deforestation that was the second reason on the pie chart is relevant to Europe region.",
      "sample_band": "4.5"
    },
    {
      "id": "uc02_aa6b207e1c7d592d_1",
      "task_type": "task1",
      "title": "Task 1: The diagram below shows the process for recycling plastic bottles...",
      "prompt": "The diagram below shows the process for recycling plastic bottles.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_aa6b207e1c7d592d_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3357-band-7-5/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The illustration depicts the method how recycling plastic bottles is done.\n\nOverall, it is a cyclical, man-made process and consists of nine phases.  Bottles are broken-down into raw ingredients in order to produce items like containers and T-shirts.\n\nFirst of all, a person throws out a plastic bottle in a designated recycling pin which a reprocessing truck picks up and empties into its container. In the recycling centre, an employee selects which bottles are suitable for repurposing and discard the damaged bottles that are unsuitable for reusing; after that, they are compressed into blocks. From this, the cubes pass through two crushing wheels which dismantle them into smaller pieces, next they are placed in a water-filled holder and washed.\n\nFollowing that, the now-clean pieces are dumped in a pellet-producing machine and subsequently heated, and then raw materials are formed. The raw materials are molded to produce several products, such as containers, water bottles, T-shirts, pencils, and reusable bags.",
      "sample_band": "7.5"
    },
    {
      "id": "uc02_c2a5a14300bea658_1",
      "task_type": "task1",
      "title": "Task 1: The charts below show the average percentages in typical meals of...",
      "prompt": "The charts below show the average percentages in typical meals of three types of nutrients, all of which may be unhealthy if eaten too much.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_c2a5a14300bea658_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3322-band-7-5/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The pie charts given illustrate how much of three nutrients, which may be harmful for health if consumed exceeding the norms, are contained in standard meals in the USA. The nutrients in question are: Sodium, saturated fat, and added sugar. Apparently, dinner accounts for the highest level of Sodium and saturated fat, whereas snacks contain the biggest share of sugar that was added. Breakfast, on the other hand, accounts for the lowest percentage of all three nutrients combined.\n\nSodium and saturated fat consumption have similar patterns; namely, dinner includes them at 43% and 37%, respectively. It is followed by lunch, with 29% of salt and 26% of fat. Proportions of Sodium is the same in breakfast and snacks (14%), while the latter accounts for significantly higher share of saturated fat (21% versus 16%).\n\nThe highest level carrier of added sugar are snacks with 42 per cent. Followed by dinner that accounts for 23%, lunch (19%), and finally breakfast (16%).",
      "sample_band": "7.5"
    },
    {
      "id": "uc02_da3e4986de6b7901_1",
      "task_type": "task1",
      "title": "Task 1: The maps below show an industrial area in the town of Norbiton, a...",
      "prompt": "The maps below show an industrial area in the town of Norbiton, and planned future development of the site.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_da3e4986de6b7901_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3386-band-7-0/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The maps illustrate the current state and the future development plans for an industrial area in the town of Norbiton. Currently, the area consists mainly of factories arranged around a central roundabout, with farmland located to the north beyond a river.\n\nIn the future development plan, significant changes are proposed. The central roundabout will remain, but it will be surrounded by housing instead of factories. The existing factories will be replaced by various facilities including a playground, a medical center, shops, and a school to the east. Additionally, the river will remain as a natural boundary, but new housing developments will extend across it.\n\nMoreover, the area around the main roundabout will see the addition of more housing units, and the introduction of a playground suggests an emphasis on creating a more family-friendly environment. The establishment of a medical center and shops further indicates a shift from an industrial zone to a mixed-use development catering to residential needs.\n\nOverall, the planned future development of Norbiton’s industrial area is focused on transforming the site into a residential neighborhood with various amenities to support the community.",
      "sample_band": "7.0"
    },
    {
      "id": "uc02_e7a93d7ef21cc146_1",
      "task_type": "task1",
      "title": "Task 1: The chart below shows information about wages for health care pro...",
      "prompt": "The chart below shows information about wages for health care professionals in four different countries.\nSummarise the information by selecting and reporting the main features, and make comparisons where relevant.",
      "material": "/materials/uc02_e7a93d7ef21cc146_1.png",
      "source": "https://ieltsjuice.com/ielts-writing-task-1-report-sample-3147-band-6-0/",
      "suggested_time": "20 phút",
      "min_words": 150,
      "sample_essay": "The given table represents average salaries per month for two occupations in the health care sector: Doctors and nurses. The sample data distributed across four countries.\n\nObviously, source countries offer low payment amounts for both careers. Country A seems to be the poorest because nurses and doctors only earn $32, $64 per month, respectively. Whereas Country B, at the same time, they can get approximately ten times more. Nevertheless, these wages are still far away from destination nations.\n\nIn Countries C and D, which have been defined as a destination for health care immigrant workers, wages jump up significantly. Nurses in country C can get paid 2900$ monthly but 500$ more in Country D. Besides that, Doctors have the highest salaries levels can be as two times more than nurses in C, but its three times in Country D, which is considered the lucrative chances for them.\n\nGenerally, Countries that trained skilled human resources for medical services providers are poor payers, unlike destination countries that receive professionals and reward them generously.",
      "sample_band": "6.0"
    }
  ],
  "task2": [
    {
      "id": "uc02_22d537ebf11c2d6e_1",
      "task_type": "task2",
      "title": "Task 2: In the last decade, there has been a great increase in the number...",
      "prompt": "In the last decade, there has been a great increase in the number and variety of online courses available to adults. This has been welcomed as a great opportunity by many students, however, other students see these courses as less effective than classroom teaching.\nWhat are the advantages and disadvantages of studying an online course?",
      "material": null,
      "source": "https://ieltsonlinetests.com/writing-correction/advantages-and-disadvantages-studying-online-course-corrected-essay",
      "suggested_time": "40 phút",
      "min_words": 250,
      "sample_essay": "In recent years, distance teaching and learning has become increasingly popular among the students and this is perceived differently by learners. Many students perceive this as a beneficial aid in learning while others think that they are not as much effective as classroom teaching. This essay will discuss about the merits and demerits of distant learning.\nStudying an online course provides a flexible timing and less budgeted learning for students. They are able to learn their desire course and subjects on their suitable time. This gives a great opportunity for learners to gain new skills and strengthen their knowledge level staying in their own place. For instance, a Nepali student who wants an Australian degree in business management course does not have to stay in Australia, he can study online and complete course staying at his home. Hence, distant learning is economic and time saving.\nHowever, online courses give more emphasis on the theoretical part of learning and there is less teacher and student interaction. It lacks the practical aspects of learning and encourage the passive learning. This is very obvious that students find it as a less effective learning than in the classroom. A recent study suggests that a greater number of students found classroom teaching far more effective than the distance learning.\nIn conclusion, the ever growing availability of online learning has gained its popularity among the young adults for many years, which is perceived as beneficial by many people while others find it to be less effective. The emphasis can be given to its effectiveness to establish it as the most cost effective learning than the classroom teaching.",
      "sample_band": "7.0"
    },
    {
      "id": "uc02_2f6fda1c83715bcb_1",
      "task_type": "task2",
      "title": "Task 2: The goal of every country should be to produce more materials and...",
      "prompt": "The goal of every country should be to produce more materials and goods. Many people assume that the goal of every country should be to produce more materials and goods. To what extent do you agree or disagree that constantly increasing production is an appropriate goal?\nThe goal of every country should be to produce more materials and goods. Many people assume that the goal of every country should be to produce more materials and goods. To what extent do you agree or disagree that constantly increasing production is an appropriate goal?",
      "material": null,
      "source": "https://ieltsonlinetests.com/writing-correction/goal-every-country-should-be-produce-more-materials-and-goods",
      "suggested_time": "40 phút",
      "min_words": 250,
      "sample_essay": "It is thought by a majority of people that, to enhance the manufacturing of various things should be the major goal of countries. Since it results in both blessings and curse to human kind; this essay aims to find the controversial issues related to augmentation of production.\nIt can be stated undoubtedly that, a country can never soar its development without boosting its material production. Moreover, to meet the demands of ever growing population it needs to produce goods related to basic needs as food, clothing etc. Third world countries especially the least developed countries always feel such pressure. Besides this, in order to alleviate poverty from country there is a constant stress of enhancing GDP which in turn demands for continuous production. Every nation wants to keep them abreast with the flow of globalization, hence tend to manufacture more and more materials. If excess local product can be exported for example, foreign currency will be obtained and thus countries can catch the global market.\nHowever, tendency to increase production may cause negative consequences. When a country is in the mode of boosting market, it may often unaware of environmental soundness. More factories means more wastes and if such wastes cannot be managed carefully and properly, great havoc may occur such as air pollution, water pollution etc. Additionally it is irony that high production does not always suppose to eliminate scarcity of people until the yields are properly distributed. Lastly, the principle of long term development lies on the effective and efficient utilization of resources, not in unwise surge of production.\nIt can be concluded that, to cope with the modern era, countries have to emphasize on producing more products. But they should also think prudentially that such production must be sustainable and eco friendly.",
      "sample_band": "6.0"
    },
    {
      "id": "uc02_4dbed5f97b671f1e_1",
      "task_type": "task2",
      "title": "Task 2: Traffic and accommodation problems are increasing and government ...",
      "prompt": "Traffic and accommodation problems are increasing and government should encourage some businesses to move from cities to rural areas. Does the advantages outweigh the disadvantages?\nTraffic and accommodation problems are increasing and government should encourage some businesses to move from cities to rural areas. Does the advantages outweigh the disadvantages?",
      "material": null,
      "source": "https://ieltsonlinetests.com/writing-correction/traffic-and-accommodation-problems",
      "suggested_time": "40 phút",
      "min_words": 250,
      "sample_essay": "An increasing number of vehicles and buildings is overwhelming so some businesses are being encouraged to relocating their offices to somewhere less crowded. Although I tend towards the viewpoint that relocation will solve this contrerversial problem but this solution will cause some inconvenienences and disadvantages for both customers and companies.\nOn the one hand, relocation can help the urbanisation problem. The shortage of jobs along with young people's need to pursue a career, are the two main reasons of rural depopulaton. Moving businesses from crowded places to rural ones will balance workforces between cities and countrysides, which helps urban areas not being overpopulated from migration. Another benefit of relocation some businesses is traffic congestion. People will tend to use public transportation instead of their private cars for longer destination to save the traveling cost. This also prevents car accidents after a frustrated working day when people are very tired and don not suit for driving.\nOn the other hand, moving between urban areas and non-urban areas will cause some inconvenienences for people who already live in cities. Changing their workplaces also means young people probably have to change their lifestyles for young people, such as their daily routines. But people with families will have to move to rural areas to live as a family with lower living conditions, which is not easily to give up. Moreover, some businesses like service companies will have some troubles while moving from cities because most of their potential are in big cities. People in urban areas need more service compared to rural ones such as healh care, restaurants, technologies, furnitures.\nIn conclusion, it seems to me that the disadavantges of moving businesses between cities and rural areas will outweight the advatages it brings due to previous reasons.",
      "sample_band": "5.5"
    },
    {
      "id": "uc02_5beae22d98151bbb_1",
      "task_type": "task2",
      "title": "Task 2: Due to the development and rapid expansion of supermarket in some...",
      "prompt": "Due to the development and rapid expansion of supermarket in some countries, many small, local business are unable to compete. Some people think that the closure of local business will bring about the death of local communities.\nTo what extent do you agree or disagree?",
      "material": null,
      "source": "https://ieltsonlinetests.com/writing-correction/closure-local-business-will-bring-about-death-local-communities",
      "suggested_time": "40 phút",
      "min_words": 250,
      "sample_essay": "Nowadays a lot of large business such as supermarkets have been improved fastly and have become widespread in the world, therefore a lot of small business have affected and lost the ability to rival. Large number of people believe that closing like these small business will impact negatively and might destroy the local communities.\nFirstly, small business play an important function in keeping the economy of local communities safe. In fact,local communities are vital because a lot of factories rely on to sell their products thus without these small business,large number of factories will be threaten to close as a result a lot workers might lose their jobs and lead to increase the idleness. For example,in some Mediterranean countries they are completely depend on a small business.In addition,there is a study says that roughly 80% percent of a people tend to buy their requirement such as foods and vegetables from small supermarkets because they found them cheaper than large supermarkets therefore without these local business the standard of the life would be very expensive and a people can not afford it.\nSecondly, absence of local businesses will make the life very complicated for the people who life in a countryside areas.Moreover, in many Mediterranean countries,most people live in cities consequently large supermarkets not exist in a countryside as a result the people who live there buy their need from the the small supermarkets consequently we can not imagine our life without these small supermarket.\nIn conclusion,despite large supermarkets are important in our life since there are comprehensive and supply us with our need, however small supermarkets are also important and we have support them.",
      "sample_band": "5.0"
    },
    {
      "id": "uc02_919e00c990eb4019_1",
      "task_type": "task2",
      "title": "Task 2: Are famous people treated unfairly by the media? Should they be g...",
      "prompt": "Are famous people treated unfairly by the media? Should they be given more privacy, or is the price of their fame an invasion into their private life? Discuss both these views and give your own opinion. Give reasons for your answer and include any relevant examples from your own knowledge or experience.",
      "material": null,
      "source": "https://ieltsonlinetests.com/writing-correction/are-famous-people-treated-unfairly-media",
      "suggested_time": "40 phút",
      "min_words": 250,
      "sample_essay": "Different people hold different point of view regarding the way media treat famous personalities, specifically in terms of coverage of their private lives. I strongly believe that the media should refrain itself from breaching the privacy of notable personalities & I will provide suitable reasoning to support my stand. To further strengthen my position, light on the other view point will also be shed along with discussing its faults.\nFirstly, it should be noted that privacy is equally needed by everyone. For me privacy is our right & cannot be compromised in any way. In my opinion, media nowadays fail to draw line between private & social life. It greatly confuses the two and the result is obnoxious, unethical, spiced up news. Taking the example of the latest news hype about a Pakistani actress wearing western clothes & smoking with an Indian star; the act itself is very personal but media of both countries didn’t fail to fully cover it and make a fuss out of it. It can be easily estimated that 40% of news influx is related to private matters of celebrities and this needs to change. They use it to increase their channel rankings & get maximum viewership.\nOn the other hand, there is a school of thought that believes that fame comes for a certain price & that is to sacrifice your privacy. They are comfortable with media breaching privacy of celebrities as they are of the opinion that a celebrity becomes a national asset & is the bearer of national culture. I again, condemn this thought & believes that it is unethical to poke around into private matters of anyone.\nConcluding, I want to say that line must be drawn between a celebrity’s private & social life & media should avoid invading their lives, as privacy is our psychological need. It is not an acceptable trend to use such news for increased channel ratings.",
      "sample_band": "6.5"
    },
    {
      "id": "case_04_off_topic_advanced",
      "task_type": "task2",
      "title": "Task 2 [Case 04: Lạc đề]: International travel can bring considerable economic be...",
      "prompt": "International travel can bring considerable economic benefits to destinations, but it may also impose costs on local communities and natural ecosystems. Do the disadvantages of international tourism outweigh the advantages? Support your position with reasons and examples. Write at least 250 words.",
      "material": null,
      "source": "IELTS.org Official (Case 04: Lạc đề)",
      "suggested_time": "40 phút",
      "min_words": 250,
      "sample_essay": "The ability to cope with the demands of adult life is not determined solely by the financial circumstances into which a child is born. It is shaped by early responsibilities, parental expectations, access to guidance, and opportunities to make consequential decisions. In my view, children from less affluent households may develop practical independence at an earlier age, but this advantage is conditional rather than inevitable. Material hardship can encourage resourcefulness; it can also undermine the very confidence and stability that young people need to flourish.\n\nOne reason for associating modest family incomes with greater maturity is that financial constraints make everyday trade-offs unusually visible. A teenager who helps plan a household budget, compares the cost of essential purchases, or contributes to domestic responsibilities may gain an appreciation of scarcity that cannot easily be acquired through theoretical instruction. Such experiences can cultivate prudence, delayed gratification, and a more discriminating attitude towards consumption. Moreover, when parents cannot resolve every difficulty through expenditure, children may be encouraged to negotiate disagreements, repair possessions, and devise workable alternatives. These habits are valuable because adult life repeatedly demands decisions under conditions of imperfect information and limited resources.\n\nNevertheless, it would be simplistic to assume that wealth necessarily produces dependence. Financially secure parents can deliberately foster autonomy by setting boundaries, expecting their children to undertake paid work, and allowing them to experience the consequences of their choices. They may also provide access to mentors, extracurricular programmes, and educational institutions that strengthen analytical thinking and emotional self-regulation. A young person who learns to manage a demanding academic schedule while participating in community activities can acquire substantial organisational skills, regardless of the family's income. The decisive variable is therefore not prosperity itself, but the extent to which adults combine support with meaningful accountability.\n\nEqually important, persistent economic insecurity should not be romanticised as a character-building exercise. A household struggling to meet basic needs may expose children to prolonged anxiety, interrupted schooling, or obligations that are inappropriate for their developmental stage. Under these circumstances, apparent self-reliance may conceal exhaustion rather than genuine resilience. The distinction matters: being forced to cope with adversity is not equivalent to receiving the psychological tools needed to process it constructively. Supportive relationships, predictable routines, and opportunities for reflection are essential if difficult experiences are to become lessons rather than lasting disadvantages.\n\nUltimately, preparation for adulthood depends on a balance between protection and responsibility. Children benefit when they are trusted with age-appropriate decisions, taught to evaluate competing priorities, and encouraged to recover from manageable setbacks. Families with limited means sometimes provide these lessons through necessity, whereas affluent families must often create them intentionally. Neither background guarantees competence. What matters most is whether children emerge from their upbringing with sound judgement, emotional resilience, and the confidence to act independently without losing the capacity to seek help.",
      "sample_band": ""
    },
    {
      "id": "case_05_grammar_errors",
      "task_type": "task2",
      "title": "Task 2 [Case 05: Lỗi ngữ pháp]: Children who are brought up in families that do not hav...",
      "prompt": "Children who are brought up in families that do not have large amounts of money are better prepared to deal with the problems of adult life than children brought up by wealthy parents. To what extent do you agree or disagree with this opinion? Give reasons for your answer and include any relevant examples from your own knowledge or experience. Write at least 250 words.",
      "material": null,
      "source": "IELTS.org Official (Case 05: Lỗi ngữ pháp)",
      "suggested_time": "40 phút",
      "min_words": 250,
      "sample_essay": "I disagree that point about children brought up in families. because I show that situation arounds me at our country parents. They want they had everything give to their children. but. their behavior is not good effect to them On the other hands, children brought up by wealthy parents. they are strong. that means they can do prepare to deal with the problems of adult life In my case I start work from 20 ages. I had social experience and I got a money for myself. however, My age is late to work by children ages and I heard about child doing work by another countries that countries had a culture about childrens That is they doing work for their pocketmoney they could their money buy something or entrance to the bank also our country childrens do this. but many childrens accept the money by their parents. which persons got a pocketmoney over the 20 ages. I think if childrens had a work and they study at money. they perfectly prepared their adult life after they must be parents",
      "sample_band": ""
    }
  ]
};

  // --- Central Exam Application State ---
  const examState = {
    mode: "full", // "full" (cả 2 part 60m), "task1" (chỉ Task 1 20m), "task2" (chỉ Task 2 40m)
    activePart: "task1", // "task1" (Part 1) or "task2" (Part 2)
    currentView: "home", // "home", "writing", "review", "results"
    totalTimeSeconds: 60 * 60,
    timeLeftSeconds: 60 * 60, // 60 minutes countdown default
    timeSpentSeconds: 0,
    timerRunning: false,
    timerInterval: null,
    sampleTestsData: [],
    benchmarkTasks: DEFAULT_BENCHMARK_TASKS,
    activeSampleTab: "full", // "full", "task1", "task2"
    task1: {
      title: "Writing Task 1",
      prompt: DEFAULT_SAMPLE_TESTS[0].questions[0].prompt,
      material: DEFAULT_SAMPLE_TESTS[0].questions[0].material || null,
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
  fetchBenchmarkTasks();
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

    // Header buttons state (if present)
    if (navHomeBtn) navHomeBtn.classList.remove("active");
    if (navWritingBtn) navWritingBtn.classList.remove("active");

    if (viewName === "writing") {
      document.body.classList.add("cd-test-active");
      writingTestView.classList.remove("hidden");
      if (navWritingBtn) navWritingBtn.classList.add("active");
      btnHeaderSubmitExam.classList.remove("hidden");
      examTimerBox.classList.remove("hidden");
      startExamTimer();
      renderCurrentPart();
    } else {
      document.body.classList.remove("cd-test-active");
      if (viewName === "home") {
        homeView.classList.remove("hidden");
        if (navHomeBtn) navHomeBtn.classList.add("active");
        btnHeaderSubmitExam.classList.add("hidden");
        examTimerBox.classList.add("hidden");
        pauseExamTimer();
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else if (viewName === "review") {
        reviewScreenView.classList.remove("hidden");
        if (navWritingBtn) navWritingBtn.classList.add("active");
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
        if (examState.mode === "task1") {
          alert("⚠️ Đã hết 20 phút làm bài thi Writing Task 1!");
        } else if (examState.mode === "task2") {
          alert("⚠️ Đã hết 40 phút làm bài thi Writing Task 2!");
        } else {
          alert("⚠️ Đã hết 60 phút làm bài thi IELTS Writing!");
        }
      }
    }, 1000);
  }

  function pauseExamTimer() {
    if (examState.timerInterval) {
      clearInterval(examState.timerInterval);
    }
    examState.timerRunning = false;
    const total = examState.totalTimeSeconds || 3600;
    examState.timeSpentSeconds = Math.max(0, total - examState.timeLeftSeconds);
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
    let promptHtml = formatParagraphs(partData.prompt);
    if (partData.material) {
      const matSrc = partData.material.startsWith("/")
        ? partData.material
        : "/" + partData.material.replace(/^evals\//, "");
      promptHtml = `
        <div class="prompt-material-wrapper">
          <img src="${escapeHtml(matSrc)}" alt="Biểu đồ / sơ đồ đề bài Task 1" class="prompt-material-img" />
        </div>
      ` + promptHtml;
    }
    cdPromptTextFormatted.innerHTML = promptHtml;
    const materialGroup = document.getElementById("taskMaterialGroup");
    const materialInput = document.getElementById("taskMaterialInput");
    materialGroup.classList.toggle("hidden", !isPart1);
    materialInput.value = partData.materialText || "";
    materialInput.oninput = () => { partData.materialText = materialInput.value; };
    cdPromptView.classList.remove("hidden");

    // 3. Cột phải: Khung nhập liệu và bộ đếm từ
    essayInput.value = partData.essay;
    const currentWc = countWords(partData.essay);
    partData.wordCount = currentWc;
    cdWordCountDisplay.textContent = currentWc;

    // 4. Thanh tiến trình dưới đáy
    updateProgressBottomBar();

    // 5. Hai biểu tượng mũi tên góc dưới bên phải
    if (examState.mode === "task1" || examState.mode === "task2") {
      if (cdNavArrows) cdNavArrows.classList.add("hidden");
      btnArrowPrev.disabled = true;
      btnArrowPrev.classList.remove("active");
      btnArrowPrev.classList.add("disabled");

      btnArrowNext.disabled = true;
      btnArrowNext.classList.remove("active");
      btnArrowNext.classList.add("disabled");
    } else {
      if (cdNavArrows) cdNavArrows.classList.remove("hidden");
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
    if (examState.mode === "task1" && targetPart === "task2") return;
    if (examState.mode === "task2" && targetPart === "task1") return;
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
    // Chế độ chỉ làm Task 1: Ẩn hoàn toàn Part 2, đường nối và mũi tên
    if (examState.mode === "task1") {
      progressStepPart1.classList.remove("hidden");
      progressStepPart1.classList.add("active");
      if (progressLine) progressLine.classList.add("hidden");
      progressStepPart2.classList.add("hidden");
      progressStepPart2.classList.remove("active");
      if (cdNavArrows) cdNavArrows.classList.add("hidden");

      if (examState.task1.completed) {
        progressStepPart1.classList.add("completed");
      } else {
        progressStepPart1.classList.remove("completed");
      }
      return;
    }

    // Chế độ chỉ làm Task 2: Ẩn hoàn toàn Part 1, đường nối và mũi tên
    if (examState.mode === "task2") {
      progressStepPart1.classList.add("hidden");
      progressStepPart1.classList.remove("active");
      if (progressLine) progressLine.classList.add("hidden");
      progressStepPart2.classList.remove("hidden");
      progressStepPart2.classList.add("active");
      if (cdNavArrows) cdNavArrows.classList.add("hidden");

      if (examState.task2.completed) {
        progressStepPart2.classList.add("completed");
      } else {
        progressStepPart2.classList.remove("completed");
      }
      return;
    }

    // Chế độ toàn phần (full exam): Hiển thị cả Part 1 và Part 2
    progressStepPart1.classList.remove("hidden");
    if (progressLine) progressLine.classList.remove("hidden");
    progressStepPart2.classList.remove("hidden");
    if (cdNavArrows) cdNavArrows.classList.remove("hidden");

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

    if (examState.mode === "task1") {
      if (reviewCardPart1) reviewCardPart1.classList.remove("hidden");
      if (reviewCardPart2) reviewCardPart2.classList.add("hidden");

      reviewPart1WcBadge.textContent = `Words: ${examState.task1.wordCount}`;
      reviewPart1PromptText.textContent = examState.task1.prompt || "(Chưa có đề bài)";
      reviewPart1EssayText.textContent = examState.task1.essay || "(Học viên chưa nhập bài làm Task 1)";
    } else if (examState.mode === "task2") {
      if (reviewCardPart1) reviewCardPart1.classList.add("hidden");
      if (reviewCardPart2) reviewCardPart2.classList.remove("hidden");

      reviewPart2WcBadge.textContent = `Words: ${examState.task2.wordCount}`;
      reviewPart2PromptText.textContent = examState.task2.prompt || "(Chưa có đề bài)";
      reviewPart2EssayText.textContent = examState.task2.essay || "(Học viên chưa nhập bài làm Task 2)";
    } else {
      if (reviewCardPart1) reviewCardPart1.classList.remove("hidden");
      if (reviewCardPart2) reviewCardPart2.classList.remove("hidden");

      // Part 1 Review Content
      reviewPart1WcBadge.textContent = `Words: ${examState.task1.wordCount}`;
      reviewPart1PromptText.textContent = examState.task1.prompt || "(Chưa có đề bài)";
      reviewPart1EssayText.textContent = examState.task1.essay || "(Học viên chưa nhập bài làm Part 1)";

      // Part 2 Review Content
      reviewPart2WcBadge.textContent = `Words: ${examState.task2.wordCount}`;
      reviewPart2PromptText.textContent = examState.task2.prompt || "(Chưa có đề bài)";
      reviewPart2EssayText.textContent = examState.task2.essay || "(Học viên chưa nhập bài làm Part 2)";
    }
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
    // 1. Cập nhật trạng thái hoàn thành theo chế độ thi
    if (examState.mode === "task1") {
      examState.task1.completed = true;
    } else if (examState.mode === "task2") {
      examState.task2.completed = true;
    } else {
      examState.task1.completed = Boolean(examState.task1.essay.trim());
      examState.task2.completed = true;
    }
    updateProgressBottomBar();

    // 2. Dừng đồng hồ làm bài
    pauseExamTimer();

    // 3. Kiểm tra xem có bài làm nào để chấm không
    const hasPart1 = Boolean(examState.task1.essay.trim());
    const hasPart2 = Boolean(examState.task2.essay.trim());

    if (examState.mode === "task1") {
      if (!hasPart1) {
        alert("Vui lòng nhập bài làm cho Writing Task 1 trước khi nộp!");
        switchView("writing");
        return;
      }
    } else if (examState.mode === "task2") {
      if (!hasPart2) {
        alert("Vui lòng nhập bài làm cho Writing Task 2 trước khi nộp!");
        switchView("writing");
        return;
      }
    } else {
      if (!hasPart1 && !hasPart2) {
        alert("Vui lòng nhập bài làm cho ít nhất Part 1 hoặc Part 2 trước khi nộp!");
        switchView("writing");
        return;
      }
    }

    // Hiển thị trạng thái đang chấm
    submitReviewSpinner.classList.remove("hidden");
    submitReviewText.textContent = "Đang thẩm định & Chấm bài...";
    btnReviewConfirm.disabled = true;

    try {
      // Đưa Agent chấm bài theo mode
      if (examState.mode === "task1") {
        examState.results.task1 = await requestAssessment("task1", examState.task1.prompt, examState.task1.essay);
        examState.activeResultTab = "task1";
      } else if (examState.mode === "task2") {
        examState.results.task2 = await requestAssessment("task2", examState.task2.prompt, examState.task2.essay);
        examState.activeResultTab = "task2";
      } else {
        if (hasPart2) {
          examState.results.task2 = await requestAssessment("task2", examState.task2.prompt, examState.task2.essay);
        }
        if (hasPart1) {
          examState.results.task1 = await requestAssessment("task1", examState.task1.prompt, examState.task1.essay);
        }
        examState.activeResultTab = hasPart2 ? "task2" : "task1";
      }

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
      essay: essay,
      task_material_text: taskType === "task1" ? examState.task1.materialText || null : null,
    };

    const res = await fetch("/api/assess-writing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const detail = errorData.detail;
      const messages = {
        INVALID_TASK: "Task 1 cần số liệu và chú giải biểu đồ đầy đủ.",
        RETRIEVAL_INVALID: "Kho tiêu chí chấm chưa sẵn sàng.",
        DEPENDENCY_UNAVAILABLE: "Dữ liệu hoặc công cụ chấm chưa sẵn sàng.",
        LLM_CONFIGURATION_ERROR: "Dịch vụ chấm chưa được cấu hình đầy đủ.",
        LLM_TIMEOUT: "Dịch vụ chấm phản hồi chậm. Vui lòng thử lại.",
        LLM_RATE_LIMITED: "Dịch vụ đang quá tải. Vui lòng thử lại sau.",
      };
      throw new Error(typeof detail === "string" ? detail :
        messages[detail?.code] || "Không thể chấm bài lúc này. Vui lòng thử lại.");
    }

    return await res.json();
  }

  // --- Assessment Results Rendering (Giao diện chấm bài cũ) ---

  function renderAssessmentResults() {
    if (examState.mode === "task1") {
      if (resultsTaskTabs) resultsTaskTabs.classList.add("hidden");
      tabResultPart1.classList.remove("hidden");
      tabResultPart2.classList.add("hidden");
      examState.activeResultTab = "task1";
    } else if (examState.mode === "task2") {
      if (resultsTaskTabs) resultsTaskTabs.classList.add("hidden");
      tabResultPart1.classList.add("hidden");
      tabResultPart2.classList.remove("hidden");
      examState.activeResultTab = "task2";
    } else {
      if (resultsTaskTabs) resultsTaskTabs.classList.remove("hidden");
      tabResultPart1.classList.remove("hidden");
      tabResultPart2.classList.remove("hidden");
    }

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
      scorePartCaption.textContent = "Overall";
    } else {
      tabResultPart2.classList.add("active");
      tabResultPart1.classList.remove("active");
      scorePartCaption.textContent = "Overall";
    }

    // Score Header
    overallBandValue.textContent = a.overall_band.toFixed(1);
    const durationMs = typeof currentRes.duration_ms === "number" ? currentRes.duration_ms : parseFloat(currentRes.duration_ms) || 0;
    const durationSec = (durationMs / 1000).toFixed(4);
    durationValue.textContent = `${durationSec} s`;

    if (examDurationValue) {
      const timeSpent = examState.timeSpentSeconds || 0;
      const mins = Math.floor(timeSpent / 60);
      const secs = timeSpent % 60;
      examDurationValue.textContent = `${mins}m ${String(secs).padStart(2, "0")}s`;
    }

    resWordCount.textContent = a.word_count;
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
        if (flag === "off_topic") label = "⚠️ Lạc đề hoàn toàn";
        if (flag === "possible_plagiarism") label = "⚠️ Nghi vấn đạo văn";
        if (flag === "injection_detected") label = "⚠️ Phát hiện Prompt Injection";
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
    renderCriteriaCards(a.criteria, essayText);

    // Render Actionable Corrections
    renderCorrections(a.corrections);
    renderPedagogicalFeedback(a);

    // Render Raw Agent JSON Viewer
    const jsonViewerContent = document.getElementById("jsonViewerContent");
    if (jsonViewerContent) {
      jsonViewerContent.textContent = JSON.stringify(currentRes, null, 2);
    }
    window.lastAssessmentResult = currentRes;
    console.log("Assessment Result JSON:", currentRes);
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
        const criterionClass = active.map((span) => `crit-${span.criterion}`).join(" ");
        html += `<mark class="quote-highlight ${escapeHtml(criterionClass)}" data-quote-ids="${ids}" title="${escapeHtml(title)}">${text}</mark>`;
      } else {
        html += text;
      }
    }

    highlightedEssayContent.innerHTML = html;

    // Attach click events on marks
    document.querySelectorAll(".quote-highlight").forEach((el) => {
      el.addEventListener("click", () => {
        const quoteId = el.dataset.quoteIds.split(" ")[0];
        highlightQuote(quoteId);
        const criterionIndex = Number(quoteId.split("-")[1]);
        document.querySelectorAll(".criterion-card").forEach((card, index) => {
          card.classList.toggle("selected-card", index === criterionIndex);
        });
        document.querySelectorAll(".crit-evidence-item").forEach((item) => item.classList.remove("active-evidence-glow"));
        const item = document.querySelector(`.crit-evidence-item[data-quote-id="${quoteId}"]`);
        if (item) {
          item.classList.add("active-evidence-glow");
          item.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
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

  function getParagraphLabelForOffset(essayText, startChar) {
    if (!essayText || typeof startChar !== "number") return "";
    startChar = Array.from(essayText).slice(0, startChar).join("").length;
    const rawParagraphs = essayText.split(/\n+/);
    let curOffset = 0;
    const paraRanges = [];
    rawParagraphs.forEach((pText, pIdx) => {
      const trimmed = pText.trim();
      if (!trimmed) return;
      const pStart = essayText.indexOf(pText, curOffset);
      if (pStart !== -1) {
        const pEnd = pStart + pText.length;
        paraRanges.push({ index: pIdx + 1, start: pStart, end: pEnd });
        curOffset = pEnd;
      }
    });

    const total = paraRanges.length;
    for (let i = 0; i < total; i++) {
      const pr = paraRanges[i];
      if (startChar >= pr.start && startChar <= pr.end) {
        if (total >= 3) {
          if (i === 0) return "Đoạn 1 (Mở bài / Tổng quan)";
          if (i === total - 1) return `Đoạn ${total} (Kết luận)`;
          return `Đoạn ${i + 1} (Thân bài ${i})`;
        }
        return `Đoạn ${i + 1}`;
      }
    }
    return "";
  }

  function renderCriteriaCards(criteria, essayText) {
    criteriaGrid.innerHTML = "";
    const criterionDisplayNames = {
      task_achievement: "Task Achievement (Mức độ hoàn thành đề bài)",
      task_response: "Task Response (Khả năng phát triển luận điểm)",
      coherence_cohesion: "Coherence & Cohesion",
      coherence_and_cohesion: "Coherence & Cohesion (Tính mạch lạc & Liên kết)",
      lexical_resource: "Lexical Resource (Vốn từ vựng học thuật)",
      grammatical_range_accuracy: "Grammatical Range & Accuracy",
      grammatical_range_and_accuracy: "Grammatical Range & Accuracy (Ngữ pháp đa dạng & Chính xác)",
    };

    const criterionEvidenceMeta = {
      task_achievement: { icon: "🎯", label: "Luận điểm chính / Câu tổng quan" },
      task_response: { icon: "🎯", label: "Luận điểm chính & Lập trường" },
      coherence_and_cohesion: { icon: "🔗", label: "Phương tiện liên kết & Chuyển ý" },
      lexical_resource: { icon: "📚", label: "Vốn từ vựng học thuật & Collocation" },
      grammatical_range_and_accuracy: { icon: "⚙️", label: "Cấu trúc câu phức & Ngữ pháp" },
    };

    criteria.forEach((crit, idx) => {
      const card = document.createElement("div");
      card.className = "criterion-card";
      card.dataset.crit = crit.criterion;

      const title = criterionDisplayNames[crit.criterion] || crit.criterion;
      const refsHtml = (crit.descriptor_refs || [])
        .map((r) => `<span class="ref-pill">#${escapeHtml(r)}</span>`)
        .join(" ");

      let evidenceContainerHtml = "";
      if (crit.evidence && crit.evidence.length > 0) {
        const meta = criterionEvidenceMeta[crit.criterion] || {
          icon: "📝",
          label: "Dẫn chứng phân tích",
        };

        const evidenceItemsHtml = crit.evidence
          .map((ev, evIdx) => {
            const paraLabel = getParagraphLabelForOffset(essayText, ev.start_char);
            const locationTag = paraLabel
              ? `<span class="evidence-para-tag">📍 ${escapeHtml(paraLabel)}</span>`
              : "";
            return `
            <div class="crit-evidence-item" data-quote-id="quote-${idx}-${evIdx}">
              <div class="evidence-item-header">
                <div class="evidence-item-title-group">
                  <span class="evidence-type-badge">${meta.icon} Dẫn chứng #${evIdx + 1}</span>
                  ${locationTag}
                </div>
                <span class="evidence-offset-tag">Ký tự [${ev.start_char}:${ev.end_char}]</span>
              </div>
              <div class="evidence-quote-content">"${escapeHtml(ev.quote)}"</div>
              <div class="evidence-footer-actions">
                <button class="btn-view-evidence" data-quote-id="quote-${idx}-${evIdx}">
                  📍 Nhảy tới dẫn chứng này trên bài viết
                </button>
              </div>
            </div>
          `;
          })
          .join("");

        evidenceContainerHtml = `
          <div class="crit-evidence-container">
            <div class="evidence-container-header">
              <span class="evidence-container-title">📑 Dẫn chứng phân tích xuyên suốt toàn bài (${crit.evidence.length} dẫn chứng):</span>
            </div>
            <div class="evidence-items-list">
              ${evidenceItemsHtml}
            </div>
          </div>
        `;
      }

      card.innerHTML = `
        <div class="crit-header">
          <span class="crit-title">${title}</span>
          <span class="crit-band">Band ${crit.band.toFixed(1)}</span>
        </div>
        <p class="crit-comment">${escapeHtml(crit.comment)}</p>
        <div class="crit-refs">${refsHtml}</div>
        ${evidenceContainerHtml}
      `;

      card.querySelectorAll(".btn-view-evidence").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const qId = btn.getAttribute("data-quote-id");
          highlightQuote(qId);
          document.querySelectorAll(".criterion-card").forEach((c) => c.classList.remove("selected-card"));
          card.classList.add("selected-card");

          document.querySelectorAll(".crit-evidence-item").forEach((it) => it.classList.remove("active-evidence-glow"));
          const parentItem = btn.closest(".crit-evidence-item");
          if (parentItem) parentItem.classList.add("active-evidence-glow");
        });
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
      correctionsList.innerHTML = `<p class="empty-state" style="padding: 12px; color: #10b981; font-weight: 500;">✓ Bài viết diễn đạt tự nhiên, không phát hiện lỗi ngữ pháp hoặc từ vựng đáng kể cần chỉnh sửa.</p>`;
      return;
    }

    const categoryLabels = {
      grammar: "Ngữ pháp (Grammar)",
      lexis: "Từ vựng (Lexis)",
      cohesion: "Tính liên kết (Cohesion)",
      task: "Phát triển ý (Task)",
    };

    corrections.forEach((item) => {
      const row = document.createElement("div");
      row.className = "correction-card";
      const catKey = (item.category || "").toLowerCase();
      const catLabel = categoryLabels[catKey] || item.category;

      row.innerHTML = `
        <div class="corr-header">
          <span class="corr-tag corr-tag-${escapeHtml(catKey)}">${escapeHtml(catLabel)}</span>
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

  function renderPedagogicalFeedback(a) {
    const categoryDisplayMap = {
      grammar: "Ngữ pháp",
      lexis: "Từ vựng",
      cohesion: "Mạch lạc & Liên kết",
      task: "Yêu cầu đề bài",
    };
    const priorityDisplayMap = {
      high: "Ưu tiên cao",
      medium: "Ưu tiên vừa",
      low: "Ưu tiên thấp",
    };
    const critTagMap = {
      task_achievement: "🎯 Task Achievement",
      task_response: "🎯 Task Response",
      coherence_cohesion: "Coherence & Cohesion",
      coherence_and_cohesion: "🔗 Coherence & Cohesion",
      lexical_resource: "📚 Lexical Resource",
      grammatical_range_accuracy: "Grammatical Range & Accuracy",
      grammatical_range_and_accuracy: "⚙️ Grammatical Range",
    };

    // 1. Top Priorities
    if (topPrioritiesSection && topPrioritiesList) {
      if (a.top_priorities && a.top_priorities.length > 0) {
        topPrioritiesSection.classList.remove("hidden");
        topPrioritiesList.innerHTML = "";
        a.top_priorities.forEach((p) => {
          const card = document.createElement("div");
          card.className = "priority-card";
          const critLabel = critTagMap[p.related_criterion] || p.related_criterion;
          card.innerHTML = `
            <div class="priority-header">
              <span class="priority-rank-badge">Ưu tiên #${p.rank}</span>
              <span class="priority-title">${escapeHtml(p.title)}</span>
              <span class="ref-pill" style="margin-left:auto;">${escapeHtml(critLabel)}</span>
            </div>
            <div class="priority-quote-box">
              <span style="font-size:0.75rem; color:#64748b; display:block; margin-bottom:2px;">📝 Câu trích xuất minh họa từ bài viết:</span>
              "${escapeHtml(p.example_quote)}"
            </div>
            <div class="priority-meta">
              <div><strong>⚠️ Vì sao bị trừ điểm:</strong> ${escapeHtml(p.why_it_matters)}</div>
              <div style="margin-top:4px;"><strong>💡 Nguyên tắc khắc phục:</strong> ${escapeHtml(p.fix_principle)}</div>
            </div>
          `;
          topPrioritiesList.appendChild(card);
        });
      } else {
        topPrioritiesSection.classList.add("hidden");
      }
    }

    // 2. Error Patterns
    if (errorPatternsSection && errorPatternsList) {
      if (a.error_patterns && a.error_patterns.length > 0) {
        errorPatternsSection.classList.remove("hidden");
        errorPatternsList.innerHTML = "";
        a.error_patterns.forEach((ep) => {
          const card = document.createElement("div");
          card.className = "pattern-card";
          const priorityBadgeClass = ep.priority === "high" ? "badge-priority-high" : (ep.priority === "medium" ? "badge-priority-medium" : "badge-priority-low");
          const prioLabel = priorityDisplayMap[ep.priority] || ep.priority;
          const catLabel = categoryDisplayMap[ep.category] || ep.category;
          let instHtml = "";
          if (ep.instances && ep.instances.length > 0) {
            instHtml = ep.instances.map(i => `<span style="display:inline-block; margin-right:8px; font-size:0.8rem;">❌ <del>${escapeHtml(i.original)}</del> ➔ ✅ <strong>${escapeHtml(i.suggestion)}</strong></span>`).join("");
          }
          card.innerHTML = `
            <div class="pattern-header">
              <span class="pattern-name">${escapeHtml(ep.pattern_name)}</span>
              <div class="pattern-badges">
                <span class="ref-pill">${escapeHtml(catLabel)} (xuất hiện ${ep.frequency} lần)</span>
                <span class="${priorityBadgeClass}">${escapeHtml(prioLabel)}</span>
              </div>
            </div>
            <div class="pattern-rule">📌 <strong>Quy tắc giải thích:</strong> ${escapeHtml(ep.rule)}</div>
            ${instHtml ? `<div style="margin-top:6px; background:#f8fafc; padding:6px 10px; border-radius:4px;">${instHtml}</div>` : ""}
          `;
          errorPatternsList.appendChild(card);
        });
      } else {
        errorPatternsSection.classList.add("hidden");
      }
    }

    // 3. Sentence Rewrites
    if (sentenceRewritesSection && sentenceRewritesList) {
      if (a.sentence_rewrites && a.sentence_rewrites.length > 0) {
        sentenceRewritesSection.classList.remove("hidden");
        sentenceRewritesList.innerHTML = "";
        a.sentence_rewrites.forEach((sr) => {
          const card = document.createElement("div");
          card.className = "rewrite-card";
          const changesHtml = (sr.changes_made || []).map(c => `<span class="change-pill">✔ ${escapeHtml(c)}</span>`).join(" ");
          card.innerHTML = `
            <div class="rewrite-orig">❌ <strong>Câu gốc của thí sinh:</strong> "${escapeHtml(sr.original_sentence)}"</div>
            <div class="rewrite-new">✨ <strong>Gợi ý viết lại nâng cấp (Band 8.0+):</strong> "${escapeHtml(sr.rewritten_sentence)}"</div>
            ${changesHtml ? `<div class="rewrite-changes"><div style="font-size:0.75rem; color:#475569; margin-bottom:4px; font-weight:600;">🛠 Các điểm cải tiến chi tiết:</div>${changesHtml}</div>` : ""}
          `;
          sentenceRewritesList.appendChild(card);
        });
      } else {
        sentenceRewritesSection.classList.add("hidden");
      }
    }

    // 4. Paragraph Analysis
    if (paragraphAnalysisSection && paragraphAnalysesList) {
      if (a.paragraph_analyses && a.paragraph_analyses.length > 0) {
        paragraphAnalysisSection.classList.remove("hidden");
        paragraphAnalysesList.innerHTML = "";
        a.paragraph_analyses.forEach((pa) => {
          const card = document.createElement("div");
          card.className = "para-card";
          card.innerHTML = `
            <div class="para-header">
              <span class="para-role">Đoạn ${pa.paragraph_number}: ${escapeHtml(pa.paragraph_role)}</span>
            </div>
            <div class="para-works">✅ <strong>Điểm làm tốt:</strong> ${escapeHtml(pa.what_works)}</div>
            <div class="para-improve">⚠️ <strong>Cần cải thiện:</strong> ${escapeHtml(pa.what_to_improve)}</div>
          `;
          paragraphAnalysesList.appendChild(card);
        });
      } else {
        paragraphAnalysisSection.classList.add("hidden");
      }
    }

    // 5. Grammar Rules
    if (grammarRulesSection && grammarRulesList) {
      if (a.grammar_rules && a.grammar_rules.length > 0) {
        grammarRulesSection.classList.remove("hidden");
        grammarRulesList.innerHTML = "";
        a.grammar_rules.forEach((gr) => {
          const card = document.createElement("div");
          card.className = "grammar-rule-card";
          card.innerHTML = `
            <div class="rule-name">📘 <strong>Quy tắc:</strong> ${escapeHtml(gr.rule_name)}</div>
            <p style="margin-bottom:6px; color:#334155; line-height:1.5;">💡 <strong>Giải thích chi tiết:</strong> ${escapeHtml(gr.explanation)}</p>
            <div style="font-size:0.8rem; display:flex; flex-direction:column; gap:4px; background:#f8fafc; padding:8px 10px; border-radius:4px;">
              <div style="color:#b91c1c;">❌ <em>Ví dụ lỗi sai:</em> "${escapeHtml(gr.incorrect_example)}"</div>
              <div style="color:#15803d;">✅ <em>Cách sửa đúng:</em> "${escapeHtml(gr.correct_example)}"</div>
            </div>
          `;
          grammarRulesList.appendChild(card);
        });
      } else {
        grammarRulesSection.classList.add("hidden");
      }
    }

    // 6. Model Sentences
    if (modelSentencesSection && modelSentencesList) {
      if (a.model_sentences && a.model_sentences.length > 0) {
        modelSentencesSection.classList.remove("hidden");
        modelSentencesList.innerHTML = "";
        a.model_sentences.forEach((ms) => {
          const card = document.createElement("div");
          card.className = "model-sentence-card";
          const phrasesHtml = (ms.useful_phrases || []).map(p => `<span class="model-phrase-pill">💎 ${escapeHtml(p)}</span>`).join(" ");
          card.innerHTML = `
            <div style="font-weight:600; color:#1e293b; margin-bottom:6px; font-style:italic;">"${escapeHtml(ms.sentence)}"</div>
            ${phrasesHtml ? `<div style="margin-top:6px;"><div style="font-size:0.75rem; color:#475569; margin-bottom:4px; font-weight:600;">Cụm từ đắt giá và ngữ nghĩa:</div>${phrasesHtml}</div>` : ""}
          `;
          modelSentencesList.appendChild(card);
        });
      } else {
        modelSentencesSection.classList.add("hidden");
      }
    }
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

  async function fetchBenchmarkTasks() {
    try {
      const res = await fetch("/api/benchmark-tasks");
      if (res.ok) {
        examState.benchmarkTasks = await res.json();
      } else {
        examState.benchmarkTasks = DEFAULT_BENCHMARK_TASKS;
      }
    } catch (e) {
      console.warn("Could not fetch /api/benchmark-tasks, using fallback tasks.", e);
      examState.benchmarkTasks = DEFAULT_BENCHMARK_TASKS;
    }
  }

  function switchSampleTab(tab) {
    examState.activeSampleTab = tab;
    const tabBtns = document.querySelectorAll(".sample-tab-btn");
    tabBtns.forEach(btn => {
      const isActive = btn.dataset.tab === tab;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    renderSampleTestsList();
  }

  function openSampleTestsModal() {
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
    const currentTab = examState.activeSampleTab || "full";

    if (currentTab === "full") {
      // --- TAB 1: BỘ ĐỀ THI ĐẦY ĐỦ CẢ TASK 1 & TASK 2 CÙNG MỘT BỘ ĐỀ ---
      const fullList = (examState.sampleTestsData.length > 0 ? examState.sampleTestsData : DEFAULT_SAMPLE_TESTS)
        .filter(test => {
          const qs = test.questions || [];
          return qs.some(q => q.task_type === "task1") && qs.some(q => q.task_type === "task2");
        });

      if (fullList.length === 0) {
        sampleTestsList.innerHTML = `<div class="empty-tests-msg">Hiện chưa có bộ đề thi đầy đủ cả 2 phần.</div>`;
        return;
      }

      fullList.forEach((test, testIdx) => {
        const card = document.createElement("div");
        card.className = "sample-test-card";
        card.id = `testCard-${test.id || testIdx}`;

        const header = document.createElement("div");
        header.className = "sample-test-header";
        header.setAttribute("role", "button");
        header.setAttribute("tabindex", "0");
        header.setAttribute("title", "Nhấn vào đây để xem chi tiết đề bài");
        header.innerHTML = `
          <div class="sample-test-info">
            <div class="sample-test-name-row">
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

        let q1 = (test.questions || []).find(q => q.task_type === "task1");
        let q2 = (test.questions || []).find(q => q.task_type === "task2" && q !== q1);

        const timeReq1 = (q1 && q1.suggested_time) || "20 phút";
        const wordReq1 = (q1 && q1.min_words) ? `Min ${q1.min_words} từ` : "Min 150 từ";
        const timeReq2 = (q2 && q2.suggested_time) || "40 phút";
        const wordReq2 = (q2 && q2.min_words) ? `Min ${q2.min_words} từ` : "Min 250 từ";

        drawer.innerHTML = `
          <div class="sample-test-bundle-block">
            <!-- Đề Writing Task 1 -->
            <div class="bundle-task-section">
              <div class="question-item-header">
                <h5 class="question-item-title">${escapeHtml((q1 && q1.title) || "Writing Task 1")}</h5>
                <span class="question-meta-info">⏱ ${escapeHtml(timeReq1)} - ${escapeHtml(wordReq1)}</span>
              </div>
              <div class="question-prompt-text">${escapeHtml((q1 && q1.prompt) || "")}</div>
            </div>

            <!-- Đường phân cách giữa Task 1 và Task 2 -->
            <div class="bundle-task-divider"></div>

            <!-- Đề Writing Task 2 -->
            <div class="bundle-task-section">
              <div class="question-item-header">
                <h5 class="question-item-title">${escapeHtml((q2 && q2.title) || "Writing Task 2")}</h5>
                <span class="question-meta-info">⏱ ${escapeHtml(timeReq2)} - ${escapeHtml(wordReq2)}</span>
              </div>
              <div class="question-prompt-text">${escapeHtml((q2 && q2.prompt) || "")}</div>
            </div>

            <!-- Nút Chọn đề thi nằm phía dưới bên phải màu xanh lá -->
            <div class="bundle-footer-row">
              <button type="button" class="btn-select-test-green" data-test-idx="${testIdx}">
                Chọn bộ đề thi (60 phút)
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

    } else if (currentTab === "task1") {
      // --- TAB 2: WRITING TASK 1 (ĐỀ RIÊNG LẺ TỪ BENCHMARK TEST) ---
      const t1List = (examState.benchmarkTasks && examState.benchmarkTasks.task1 && examState.benchmarkTasks.task1.length > 0)
        ? examState.benchmarkTasks.task1
        : DEFAULT_BENCHMARK_TASKS.task1;

      t1List.forEach((task, taskIdx) => {
        const card = document.createElement("div");
        card.className = "single-task-card";
        card.id = `task1Card-${task.id || taskIdx}`;

        const timeReq = task.suggested_time || "20 phút";
        const wordReq = task.min_words ? `Min ${task.min_words} từ` : "Min 150 từ";
        const hasMaterial = Boolean(task.material);

        card.innerHTML = `
          <div class="single-task-header-row">
            <div class="single-task-source">
              <span class="source-tag">🏛 Nguồn:</span> ${escapeHtml(task.source)}
            </div>
          </div>
          <h4 class="single-task-title">${escapeHtml(task.title || "Writing Task 1")}</h4>
          ${hasMaterial ? `
            <div class="single-task-thumb-wrapper">
              <img src="${escapeHtml(task.material)}" alt="Biểu đồ Task 1" class="single-task-thumb-img" loading="lazy" />
            </div>
          ` : ""}
          <div class="single-task-prompt">${escapeHtml(task.prompt)}</div>
          <div class="single-task-footer">
            <button type="button" class="btn-select-test-green btn-select-benchmark-task" data-task-idx="${taskIdx}" data-task-type="task1">
              Bắt đầu làm Task 1 (20 phút)
            </button>
          </div>
        `;

        sampleTestsList.appendChild(card);
      });

      sampleTestsList.querySelectorAll(".btn-select-benchmark-task[data-task-type='task1']").forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const taskIdx = parseInt(btn.dataset.taskIdx, 10);
          const loadSample = Boolean(e.shiftKey);
          loadBenchmarkTaskIntoExam(t1List[taskIdx], "task1", loadSample);
        });
      });

    } else if (currentTab === "task2") {
      // --- TAB 3: WRITING TASK 2 (ĐỀ RIÊNG LẺ TỪ BENCHMARK TEST & BASIC CASES) ---
      const t2List = (examState.benchmarkTasks && examState.benchmarkTasks.task2 && examState.benchmarkTasks.task2.length > 0)
        ? examState.benchmarkTasks.task2
        : DEFAULT_BENCHMARK_TASKS.task2;

      t2List.forEach((task, taskIdx) => {
        const card = document.createElement("div");
        card.className = "single-task-card";
        card.id = `task2Card-${task.id || taskIdx}`;

        const timeReq = task.suggested_time || "40 phút";
        const wordReq = task.min_words ? `Min ${task.min_words} từ` : "Min 250 từ";

        card.innerHTML = `
          <div class="single-task-header-row">
            <div class="single-task-source">
              <span class="source-tag">🏛 Nguồn:</span> ${escapeHtml(task.source)}
            </div>
          </div>
          <h4 class="single-task-title">${escapeHtml(task.title || "Writing Task 2")}</h4>
          <div class="single-task-prompt">${escapeHtml(task.prompt)}</div>
          <div class="single-task-footer">
            <button type="button" class="btn-select-test-green btn-select-benchmark-task" data-task-idx="${taskIdx}" data-task-type="task2">
              Bắt đầu làm Task 2 (40 phút)
            </button>
          </div>
        `;

        sampleTestsList.appendChild(card);
      });

      sampleTestsList.querySelectorAll(".btn-select-benchmark-task[data-task-type='task2']").forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const taskIdx = parseInt(btn.dataset.taskIdx, 10);
          const loadSample = Boolean(e.shiftKey);
          loadBenchmarkTaskIntoExam(t2List[taskIdx], "task2", loadSample);
        });
      });
    }
  }

  function loadBenchmarkTaskIntoExam(task, taskType, loadSampleEssay = false) {
    if (!task) return;

    if (taskType === "task1") {
      examState.mode = "task1";
      examState.activePart = "task1";
      examState.totalTimeSeconds = 20 * 60;
      examState.timeLeftSeconds = 20 * 60; // 20 phút chuẩn Task 1

      examState.task1.title = task.title || "Writing Task 1";
      examState.task1.prompt = task.prompt;
      examState.task1.materialText = task.task_material_text || "";
      examState.task1.material = task.material || null;
      examState.task1.essay = (loadSampleEssay && task.sample_essay) ? task.sample_essay : "";
      examState.task1.wordCount = countWords(examState.task1.essay);
      examState.task1.completed = examState.task1.wordCount > 0;

      // Xóa và cô lập hoàn toàn Task 2 để không xuất hiện khi luyện tập Task 1
      examState.task2.title = "";
      examState.task2.prompt = "";
      examState.task2.material = null;
      examState.task2.essay = "";
      examState.task2.wordCount = 0;
      examState.task2.completed = false;
      examState.results.task2 = null;
    } else {
      examState.mode = "task2";
      examState.activePart = "task2";
      examState.totalTimeSeconds = 40 * 60;
      examState.timeLeftSeconds = 40 * 60; // 40 phút chuẩn Task 2

      examState.task2.title = task.title || "Writing Task 2";
      examState.task2.prompt = task.prompt;
      examState.task2.material = null;
      examState.task2.essay = (loadSampleEssay && task.sample_essay) ? task.sample_essay : "";
      examState.task2.wordCount = countWords(examState.task2.essay);
      examState.task2.completed = examState.task2.wordCount > 0;

      // Xóa và cô lập hoàn toàn Task 1 để không xuất hiện khi luyện tập Task 2
      examState.task1.title = "";
      examState.task1.prompt = "";
      examState.task1.material = null;
      examState.task1.essay = "";
      examState.task1.wordCount = 0;
      examState.task1.completed = false;
      examState.results.task1 = null;
    }

    closeSampleTestsModal();
    switchView("writing");
  }

  function loadSingleTaskIntoExam(testIdx, taskType, loadSampleEssay = false) {
    if (taskType === "task1") {
      const t1List = (examState.benchmarkTasks && examState.benchmarkTasks.task1 && examState.benchmarkTasks.task1.length > 0)
        ? examState.benchmarkTasks.task1
        : DEFAULT_BENCHMARK_TASKS.task1;
      if (t1List[testIdx]) {
        loadBenchmarkTaskIntoExam(t1List[testIdx], "task1", loadSampleEssay);
      }
    } else {
      const t2List = (examState.benchmarkTasks && examState.benchmarkTasks.task2 && examState.benchmarkTasks.task2.length > 0)
        ? examState.benchmarkTasks.task2
        : DEFAULT_BENCHMARK_TASKS.task2;
      if (t2List[testIdx]) {
        loadBenchmarkTaskIntoExam(t2List[testIdx], "task2", loadSampleEssay);
      }
    }
  }

  function loadTestSetIntoExam(testIdx, loadSampleEssay = false) {
    const fullList = (examState.sampleTestsData.length > 0 ? examState.sampleTestsData : DEFAULT_SAMPLE_TESTS)
      .filter(test => {
        const qs = test.questions || [];
        return qs.some(q => q.task_type === "task1") && qs.some(q => q.task_type === "task2");
      });
    const test = fullList[testIdx];
    if (!test || !test.questions) return;

    let q1 = test.questions.find(q => q.task_type === "task1");
    let q2 = test.questions.find(q => q.task_type === "task2");

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

    examState.mode = "full";
    examState.activePart = "task1";
    examState.totalTimeSeconds = 60 * 60;
    examState.timeLeftSeconds = 60 * 60; // 60 phút cả 2 task

    examState.task1.title = q1.title || "Writing Task 1";
    examState.task1.prompt = q1.prompt;
    examState.task1.materialText = q1.task_material_text || "";
    examState.task1.material = q1.material || null;
    examState.task1.essay = (loadSampleEssay && q1.sample_essay) ? q1.sample_essay : "";
    examState.task1.wordCount = countWords(examState.task1.essay);
    examState.task1.completed = examState.task1.wordCount > 0;

    examState.task2.title = q2.title || "Writing Task 2";
    examState.task2.prompt = q2.prompt;
    examState.task2.material = q2.material || null;
    examState.task2.essay = (loadSampleEssay && q2.sample_essay) ? q2.sample_essay : "";
    examState.task2.wordCount = countWords(examState.task2.essay);
    examState.task2.completed = examState.task2.wordCount > 0;

    closeSampleTestsModal();
    switchView("writing");
  }
  // --- Event Listeners Setup ---

  function setupEventListeners() {
    // Navigation & logo click
    if (navHomeBtn) navHomeBtn.addEventListener("click", () => switchView("home"));
    if (navWritingBtn) navWritingBtn.addEventListener("click", () => switchView("writing"));

    btnHomeFromResults.addEventListener("click", () => switchView("home"));

    // Home: Start writing test button directly opens sample tests modal
    btnStartWriting.addEventListener("click", (e) => {
      e.stopPropagation();
      openSampleTestsModal();
    });

    // Sample tests modal tab buttons
    document.querySelectorAll(".sample-tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        if (tab) switchSampleTab(tab);
      });
    });

    closeSampleTestsBtn.addEventListener("click", closeSampleTestsModal);

    // Close modal on clicking overlay backdrop
    sampleTestsModal.addEventListener("click", (e) => {
      if (e.target === sampleTestsModal) closeSampleTestsModal();
    });

    // Close modal on Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeSampleTestsModal();
      }
    });

    // Header "Nộp bài" button: opens review screen
    btnHeaderSubmitExam.addEventListener("click", () => {
      saveCurrentPartText();
      if (examState.mode === "task1") {
        examState.task1.completed = true;
      } else if (examState.mode === "task2") {
        examState.task2.completed = true;
      } else {
        if (examState.activePart === "task1") examState.task1.completed = true;
        if (examState.activePart === "task2") examState.task2.completed = true;
      }
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
      if (examState.mode === "task2") return;
      examState.activeResultTab = "task1";
      renderAssessmentResults();
    });

    tabResultPart2.addEventListener("click", () => {
      if (examState.mode === "task1") return;
      examState.activeResultTab = "task2";
      renderAssessmentResults();
    });

    // Copy JSON Result helper and listeners
    function copyTextToClipboard(text, btnElement) {
      if (!text || text.trim() === "{}") {
        btnElement.textContent = "⚠️ Chưa có dữ liệu";
        setTimeout(() => { btnElement.textContent = "📋 Copy JSON"; }, 2000);
        return;
      }

      const setSuccess = () => {
        btnElement.textContent = "✅ Đã chép!";
        setTimeout(() => { btnElement.textContent = "📋 Copy JSON"; }, 2000);
      };

      const fallbackCopy = () => {
        try {
          const textArea = document.createElement("textarea");
          textArea.value = text;
          textArea.style.top = "0";
          textArea.style.left = "0";
          textArea.style.position = "fixed";
          textArea.style.opacity = "0";
          document.body.appendChild(textArea);
          textArea.focus();
          textArea.select();
          const successful = document.execCommand("copy");
          document.body.removeChild(textArea);
          if (successful) {
            setSuccess();
          } else {
            btnElement.textContent = "❌ Lỗi sao chép";
            setTimeout(() => { btnElement.textContent = "📋 Copy JSON"; }, 2000);
          }
        } catch (err) {
          console.error("Fallback clipboard copy failed:", err);
          btnElement.textContent = "❌ Lỗi sao chép";
          setTimeout(() => { btnElement.textContent = "📋 Copy JSON"; }, 2000);
        }
      };

      if (navigator.clipboard && window.isSecureContext && typeof navigator.clipboard.writeText === "function") {
        navigator.clipboard.writeText(text).then(setSuccess).catch(fallbackCopy);
      } else {
        fallbackCopy();
      }
    }

    function handleCopyJsonClick(e, btn) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      const jsonBox = document.getElementById("jsonViewerContent");
      let text = (jsonBox && jsonBox.textContent && jsonBox.textContent.trim() !== "{}")
        ? jsonBox.textContent
        : "";
      if (!text) {
        const currentRes = examState.results[examState.activeResultTab] || window.lastAssessmentResult;
        if (currentRes) {
          text = JSON.stringify(currentRes, null, 2);
        }
      }
      copyTextToClipboard(text, btn);
    }

    const btnCopyJson = document.getElementById("btnCopyJson");
    if (btnCopyJson) {
      btnCopyJson.addEventListener("click", (e) => handleCopyJsonClick(e, btnCopyJson));
    }

    const btnCopyJsonInner = document.getElementById("btnCopyJsonInner");
    if (btnCopyJsonInner) {
      btnCopyJsonInner.addEventListener("click", (e) => handleCopyJsonClick(e, btnCopyJsonInner));
    }

    const btnOpenJson = document.getElementById("btnOpenJson");
    if (btnOpenJson) {
      btnOpenJson.addEventListener("click", (e) => {
        e.stopPropagation();
      });
    }

  }
});
