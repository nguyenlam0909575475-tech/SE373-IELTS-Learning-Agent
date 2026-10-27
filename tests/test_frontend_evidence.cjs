const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

// Exercise the actual app renderer without a browser or a second implementation.
const source = fs.readFileSync(path.join(__dirname, "../frontend/app.js"), "utf8");
const renderer = source.slice(source.indexOf("  function renderInteractiveEssay("),
  source.indexOf("  function highlightQuote("));
const escapeStart = source.indexOf("  function escapeHtml(");
const escapeFunction = source.slice(escapeStart, source.indexOf("\n  function ", escapeStart + 1));

function render(essay, criteria) {
  const context = { essay, criteria, highlightedEssayContent: { innerHTML: "" },
    document: { querySelectorAll: () => [] } };
  vm.runInNewContext(`${escapeFunction}\n${renderer}\nrenderInteractiveEssay(essay, criteria);`, context);
  return context.highlightedEssayContent.innerHTML;
}

function plainText(html) {
  return html.replace(/<[^>]*>/g, "").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#039;/g, "'").replace(/&amp;/g, "&");
}

test("Python code-point offsets preserve emoji, accents and surrounding whitespace", () => {
  const essay = "  😀 café <note> tail\n";
  const html = render(essay, [{ criterion: "lexical_resource", comment: 'A "quote" <tag>',
    evidence: [{ quote: "café", start_char: 4, end_char: 8 }] }]);
  assert.match(html, />café<\/mark>/);
  assert.match(html, /&quot;quote&quot; &lt;tag&gt;/);
  assert.equal(plainText(html), essay);
});

test("overlapping and identical quotes retain all criterion targets without duplicating text", () => {
  const evidence = (quote, start_char, end_char) => [{ quote, start_char, end_char }];
  const html = render("alpha beta gamma", [
    { criterion: "task_response", comment: "first", evidence: evidence("alpha beta", 0, 10) },
    { criterion: "coherence_cohesion", comment: "second", evidence: evidence("beta gamma", 6, 16) },
    { criterion: "lexical_resource", comment: "third", evidence: evidence("alpha beta", 0, 10) },
  ]);
  assert.equal(plainText(html), "alpha beta gamma");
  assert.match(html, /data-quote-ids="quote-0-0 quote-1-0 quote-2-0"[^>]*>beta<\/mark>/);
});

test("invalid or fabricated spans do not highlight unrelated characters", () => {
  const html = render("Original text", [{ criterion: "task_response", comment: "bad",
    evidence: [{ quote: "Missing", start_char: 0, end_char: 7 },
      { quote: "Original", start_char: -1, end_char: 8 }] }]);
  assert.equal(html, "Original text");
});

test("PR22 feedback renders supplied fields, escapes text and hides absent sections", () => {
  const names = [
    ["topPrioritiesSection", "topPrioritiesList"], ["errorPatternsSection", "errorPatternsList"],
    ["sentenceRewritesSection", "sentenceRewritesList"], ["paragraphAnalysisSection", "paragraphAnalysesList"],
    ["grammarRulesSection", "grammarRulesList"], ["modelSentencesSection", "modelSentencesList"],
  ];
  const context = { document: { createElement: () => ({ className: "", innerHTML: "" }) } };
  for (const pair of names) for (const name of pair) {
    const hidden = new Set(["hidden"]);
    context[name] = { innerHTML: "", children: [],
      appendChild(child) { this.children.push(child); },
      classList: { add: value => hidden.add(value), remove: value => hidden.delete(value),
        contains: value => hidden.has(value) } };
  }
  const start = source.indexOf("  function renderPedagogicalFeedback(");
  const end = source.indexOf("  async function fetchServerConfig(", start);
  vm.runInNewContext(`${escapeFunction}\n${source.slice(start, end)}`, context);
  context.renderPedagogicalFeedback({ top_priorities: [{ rank: 1, title: "Improve <clarity>",
    example_quote: "😀 <student>", why_it_matters: "Explain precisely.",
    fix_principle: "Use clear wording.", related_criterion: "coherence_cohesion" }] });
  assert.equal(context.topPrioritiesSection.classList.contains("hidden"), false);
  assert.match(context.topPrioritiesList.children[0].innerHTML, /😀 &lt;student&gt;/);
  assert.equal(context.grammarRulesSection.classList.contains("hidden"), true);
  context.renderPedagogicalFeedback({});
  for (const [section] of names) assert.equal(context[section].classList.contains("hidden"), true);
});

function resultsContext(mode) {
  function element() {
    const classes = new Set();
    return {
      children: [], dataset: {}, textContent: "", html: "",
      set innerHTML(value) { this.html = value; this.children = []; },
      get innerHTML() { return this.html; },
      appendChild(child) { this.children.push(child); },
      querySelectorAll: () => [], addEventListener() {},
      classList: { add: name => classes.add(name), remove: name => classes.delete(name),
        contains: name => classes.has(name) },
    };
  }
  const elements = {};
  const context = { window: {}, console: { log() {} }, document: {
    createElement: element, querySelectorAll: () => [],
    getElementById: id => elements[id] || null,
  } };
  for (const [, name, id] of source.matchAll(/const (\w+) = document.getElementById\("([^"]+)"\)/g)) {
    context[name] = elements[id] = element();
  }
  const examState = { mode, activeResultTab: "task1", results: {}, timeSpentSeconds: 65 };
  for (const task of ["task1", "task2"]) {
    const quote = `${task} detail.`;
    const essay = `😀 Introduction.\n\n${quote}\n\nConclusion.`;
    const start = Array.from(essay.slice(0, essay.indexOf(quote))).length;
    examState[task] = { essay };
    examState.results[task] = { duration_ms: 4500, assessment: {
      overall_band: 6, word_count: 5, disclaimer: "Synthetic practice assessment.",
      flags: ["under_length"], corrections: [],
      criteria: [task === "task1" ? "task_achievement" : "task_response",
        "coherence_and_cohesion", "lexical_resource", "grammatical_range_and_accuracy"]
        .map(criterion => ({ criterion, band: 6, comment: "Synthetic feedback.",
          descriptor_refs: [], evidence: [{ quote, start_char: start, end_char: start + quote.length }] })),
    } };
  }
  context.examState = examState;
  const start = source.indexOf("  function renderAssessmentResults(");
  const end = source.indexOf("  async function fetchServerConfig(", start);
  vm.runInNewContext(`${escapeFunction}\n${source.slice(start, end)}`, context);
  return context;
}

for (const mode of ["task1", "task2", "full"]) {
  test(`assessment results render scores, essay and criterion locations in ${mode} mode`, () => {
    const context = resultsContext(mode);
    const tabs = mode === "full" ? ["task1", "task2"] : [mode];
    for (const task of tabs) {
      context.examState.activeResultTab = task;
      context.renderAssessmentResults();
      assert.equal(context.overallBandValue.textContent, "6.0");
      assert.equal(context.assessmentResults.classList.contains("hidden"), false);
      assert.equal(plainText(context.highlightedEssayContent.innerHTML), context.examState[task].essay);
      assert.equal(context.criteriaGrid.children.length, 4);
      assert.match(context.criteriaGrid.children[0].innerHTML, /Đoạn 2 \(Thân bài 1\)/);
      assert.match(context.criteriaGrid.children[0].innerHTML, new RegExp(`${task} detail\\.`));
      assert.equal(context.window.lastAssessmentResult, context.examState.results[task]);
      assert.deepEqual(JSON.parse(context.document.getElementById("jsonViewerContent").textContent),
        context.examState.results[task]);
    }
  });
}
