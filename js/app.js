/* Backend Lab — 앱 로직 */
(function () {
  "use strict";

  // ── Storage ────────────────────────────────────────────────
  const STORAGE_KEY = "backend-lab-v1";

  const defaultState = {
    known: {}, // conceptId: true
    wrong: [], // { id, question, choices, correctIndex, myIndex, explanation, category, at, mastered, sourceId }
    stats: { answered: 0, correct: 0 },
    daily: {}, // YYYY-MM-DD: { answered, correct }
  };

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return structuredClone(defaultState);
      const parsed = JSON.parse(raw);
      return {
        known: parsed.known || {},
        wrong: Array.isArray(parsed.wrong) ? parsed.wrong : [],
        stats: parsed.stats || { answered: 0, correct: 0 },
        daily: parsed.daily || {},
      };
    } catch {
      return structuredClone(defaultState);
    }
  }

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  let state = loadState();

  // ── Helpers ────────────────────────────────────────────────
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  function categoryOf(id) {
    return CATEGORIES.find((c) => c.id === id) || { id: id, name: id, icon: "📘" };
  }

  function todayKey() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function showToast(msg) {
    const el = $("#toast");
    el.textContent = msg;
    el.hidden = false;
    requestAnimationFrame(() => el.classList.add("is-show"));
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => {
      el.classList.remove("is-show");
      setTimeout(() => {
        el.hidden = true;
      }, 220);
    }, 1800);
  }

  function formatAt(ts) {
    try {
      return new Date(ts).toLocaleString("ko-KR", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  }

  // ── Views ──────────────────────────────────────────────────
  const VIEW_META = {
    dashboard: { title: "대시보드", desc: "백엔드 핵심 개념 학습 현황을 한눈에 확인하세요." },
    cards: { title: "개념 카드", desc: "카드를 뒤집으며 용어와 정의를 암기하세요." },
    vocab: { title: "단어장", desc: "모든 개념을 검색하고 한 번에 훑어보세요." },
    quiz: { title: "퀴즈", desc: "선다형 문제로 이해도를 점검하세요." },
    wrong: { title: "오답노트", desc: "틀린 문제를 모아 반복 학습하세요." },
  };

  function switchView(name) {
    $$(".nav-item").forEach((b) => b.classList.toggle("is-active", b.dataset.view === name));
    $$(".view").forEach((v) => v.classList.toggle("is-active", v.id === `view-${name}`));
    $("#view-title").textContent = VIEW_META[name].title;
    $("#view-desc").textContent = VIEW_META[name].desc;

    if (name === "dashboard") renderDashboard();
    if (name === "cards") renderCard();
    if (name === "vocab") renderVocab();
    if (name === "wrong") renderWrong();
    if (name === "quiz") resetQuizScreens();
  }

  // ── Dashboard ──────────────────────────────────────────────
  function renderDashboard() {
    const total = CONCEPTS.length;
    const known = Object.keys(state.known).filter((id) => state.known[id]).length;
    const acc =
      state.stats.answered > 0 ? Math.round((state.stats.correct / state.stats.answered) * 100) : null;
    const openWrong = state.wrong.filter((w) => !w.mastered).length;

    $("#stat-total-concepts").textContent = total;
    $("#stat-known").textContent = known;
    $("#stat-quiz-acc").textContent = acc === null ? "—" : `${acc}%`;
    $("#stat-wrong").textContent = openWrong;

    const pct = total ? Math.round((known / total) * 100) : 0;
    $("#progress-text").textContent = `${pct}%`;
    $("#progress-fill").style.width = `${pct}%`;

    const daily = state.daily[todayKey()] || { answered: 0, correct: 0 };
    $("#today-stats").textContent = `오늘 ${daily.answered}문항 · ${daily.correct}정답`;

    // 카테고리 진도
    const box = $("#category-progress");
    box.innerHTML = CATEGORIES.map((cat) => {
      const items = CONCEPTS.filter((c) => c.category === cat.id);
      const k = items.filter((c) => state.known[c.id]).length;
      const p = items.length ? Math.round((k / items.length) * 100) : 0;
      return `
        <div class="cat-row">
          <div class="cat-name">${cat.icon} ${cat.name}</div>
          <div class="cat-bar"><div class="cat-fill" style="width:${p}%"></div></div>
          <div class="cat-pct">${p}%</div>
        </div>`;
    }).join("");

    updateWrongBadge();
  }

  function updateWrongBadge() {
    const n = state.wrong.filter((w) => !w.mastered).length;
    const badge = $("#wrong-badge");
    badge.hidden = n === 0;
    badge.textContent = n;
  }

  // ── Flashcards ─────────────────────────────────────────────
  let cardDeck = [];
  let cardIndex = 0;
  let cardFilter = "all";
  let cardCategory = "all";

  function buildCardDeck() {
    let items = [...CONCEPTS];
    if (cardCategory !== "all") items = items.filter((c) => c.category === cardCategory);
    if (cardFilter === "known") items = items.filter((c) => state.known[c.id]);
    if (cardFilter === "unknown") items = items.filter((c) => !state.known[c.id]);
    return items;
  }

  function renderCard() {
    cardDeck = buildCardDeck();
    if (cardIndex >= cardDeck.length) cardIndex = 0;

    const card = cardDeck[cardIndex];
    const stage = $("#flashcard");
    stage.classList.remove("is-flipped");

    if (!card) {
      $("#card-term").textContent = "해당 조건의 카드가 없습니다";
      $("#card-definition").textContent = "필터를 변경해 보세요.";
      $("#card-example").textContent = "";
      $("#card-counter").textContent = "0 / 0";
      $("#card-category-chip").textContent = "—";
      $("#card-status-chip").textContent = "—";
      return;
    }

    const cat = categoryOf(card.category);
    const known = !!state.known[card.id];

    $("#card-category-chip").textContent = `${cat.icon} ${cat.name}`;
    $("#card-category-chip-back").textContent = `${cat.icon} ${cat.name}`;
    $("#card-status-chip").textContent = known ? "외움" : "학습 중";
    $("#card-term").textContent = card.term;
    $("#card-definition").textContent = card.definition;
    $("#card-example").textContent = card.example || "";
    $("#card-example-wrap").style.display = card.example ? "" : "none";
    $("#card-counter").textContent = `${cardIndex + 1} / ${cardDeck.length}`;
  }

  function flipCard() {
    $("#flashcard").classList.toggle("is-flipped");
  }

  function moveCard(delta) {
    if (!cardDeck.length) return;
    cardIndex = (cardIndex + delta + cardDeck.length) % cardDeck.length;
    renderCard();
  }

  function markCard(known) {
    const card = cardDeck[cardIndex];
    if (!card) return;
    state.known[card.id] = known;
    saveState();
    showToast(known ? "외운 것으로 표시했어요 ✅" : "모르는 것으로 표시했어요");
    // 모르는 것은 남기고, 외운 것은 다음 카드로
    if (known) {
      if (cardFilter === "unknown") {
        cardDeck = buildCardDeck();
        if (cardIndex >= cardDeck.length) cardIndex = Math.max(0, cardDeck.length - 1);
      } else {
        moveCard(1);
      }
      renderCard();
    } else {
      renderCard();
    }
    renderDashboardSoft();
  }

  function renderDashboardSoft() {
    const total = CONCEPTS.length;
    const known = Object.keys(state.known).filter((id) => state.known[id]).length;
    const pct = total ? Math.round((known / total) * 100) : 0;
    $("#progress-text").textContent = `${pct}%`;
    $("#progress-fill").style.width = `${pct}%`;
    updateWrongBadge();
  }

  // ── Vocab ──────────────────────────────────────────────────
  function renderVocab() {
    const q = ($("#vocab-search").value || "").trim().toLowerCase();
    const cat = $("#vocab-category").value;

    let items = [...CONCEPTS];
    if (cat !== "all") items = items.filter((c) => c.category === cat);
    if (q) {
      items = items.filter(
        (c) =>
          c.term.toLowerCase().includes(q) ||
          c.definition.toLowerCase().includes(q) ||
          (c.example || "").toLowerCase().includes(q)
      );
    }

    $("#vocab-count").textContent = `${items.length}개`;

    $("#vocab-list").innerHTML = items
      .map((c) => {
        const meta = categoryOf(c.category);
        const known = !!state.known[c.id];
        return `
        <article class="vocab-card">
          <div class="card-meta" style="margin-bottom:12px">
            <span class="chip">${meta.icon} ${meta.name}</span>
            <span class="chip chip-soft">${known ? "외움" : "학습 중"}</span>
          </div>
          <h3 class="vocab-term">${escapeHtml(c.term)}</h3>
          <p class="vocab-def">${escapeHtml(c.definition)}</p>
          ${c.example ? `<div class="vocab-example">${escapeHtml(c.example)}</div>` : ""}
          <div class="vocab-foot">
            <span class="muted">${known ? "✅ 외운 개념" : "아직 외우지 않음"}</span>
            <button class="btn ${known ? "btn-secondary" : "btn-success"}" data-toggle-known="${c.id}" style="padding:8px 12px">
              ${known ? "학습 중으로" : "외웠어요"}
            </button>
          </div>
        </article>`;
      })
      .join("");
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ── Quiz engine ────────────────────────────────────────────
  // 문제 타입 1: 용어 → 정의 고르기 (개념 카드에서 생성)
  // 문제 타입 2: 정의 → 용어 고르기 (개념 카드에서 생성)
  // 문제 타입 3: 심화 선다형 (QUIZ_QUESTIONS)

  function buildConceptChoiceQuestion(concept, pool, mode) {
    // mode: "def" = 용어를 보고 정의 선택, "term" = 정의를 보고 용어 선택
    const others = shuffle(pool.filter((c) => c.id !== concept.id)).slice(0, 3);
    if (others.length < 3) return null;

    const cat = categoryOf(concept.category);

    if (mode === "term") {
      const choices = shuffle([
        { text: concept.term, correct: true },
        ...others.map((c) => ({ text: c.term, correct: false })),
      ]);
      return {
        id: `auto-term-${concept.id}`,
        sourceId: concept.id,
        category: concept.category,
        type: "용어 찾기",
        question: `다음 정의에 해당하는 용어는?\n\n"${concept.definition}"`,
        choices: choices.map((c) => c.text),
        correctIndex: choices.findIndex((c) => c.correct),
        explanation: concept.example ? `${concept.term} — ${concept.example}` : concept.term,
        chip: `${cat.icon} ${cat.name}`,
      };
    }

    const choices = shuffle([
      { text: concept.definition, correct: true },
      ...others.map((c) => ({ text: c.definition, correct: false })),
    ]);
    return {
      id: `auto-def-${concept.id}`,
      sourceId: concept.id,
      category: concept.category,
      type: "정의 찾기",
      question: `"${concept.term}"의 올바른 정의는?`,
      choices: choices.map((c) => c.text),
      correctIndex: choices.findIndex((c) => c.correct),
      explanation: concept.example || concept.definition,
      chip: `${cat.icon} ${cat.name}`,
    };
  }

  function buildAdvancedQuestion(q) {
    const cat = categoryOf(q.category);
    return {
      id: q.id,
      sourceId: q.id,
      category: q.category,
      type: "심화",
      question: q.question,
      choices: q.choices,
      correctIndex: q.correctIndex,
      explanation: q.explanation,
      chip: `${cat.icon} ${cat.name}`,
    };
  }

  function generateQuiz({ size = 10, category = "all", fromWrong = false } = {}) {
    let questions = [];

    if (fromWrong) {
      const open = state.wrong.filter((w) => !w.mastered);
      questions = shuffle(open).map((w) => ({
        id: `wrong-${w.id}`,
        sourceId: w.sourceId,
        category: w.category,
        type: "오답",
        question: w.question,
        choices: w.choices,
        correctIndex: w.correctIndex,
        explanation: w.explanation,
        chip: `${categoryOf(w.category).icon} ${categoryOf(w.category).name}`,
        wrongKey: w.id,
      }));
      return questions.slice(0, Math.max(size, questions.length));
    }

    let pool = [...CONCEPTS];
    if (category !== "all") pool = pool.filter((c) => c.category === category);

    const advPool = QUIZ_QUESTIONS.filter((q) => category === "all" || q.category === category);

    // 고급 문항 최대 40%, 나머지는 개념 기반
    const advCount = Math.min(advPool.length, Math.max(1, Math.floor(size * 0.4)));
    const autoCount = Math.max(0, size - advCount);

    const pickedAdv = shuffle(advPool).slice(0, advCount).map(buildAdvancedQuestion);

    const modes = ["def", "term", "def"];
    const pickedAuto = [];
    const used = new Set();
    const shuffledConcepts = shuffle(pool);
    for (const c of shuffledConcepts) {
      if (pickedAuto.length >= autoCount) break;
      if (used.has(c.id)) continue;
      const mode = modes[pickedAuto.length % modes.length];
      const q = buildConceptChoiceQuestion(c, pool, mode);
      if (!q) continue;
      used.add(c.id);
      pickedAuto.push(q);
    }

    questions = shuffle([...pickedAdv, ...pickedAuto]);
    return questions;
  }

  let quizSession = {
    questions: [],
    index: 0,
    answered: 0,
    correct: 0,
    locked: false,
  };

  function resetQuizScreens() {
    $("#quiz-start").hidden = false;
    $("#quiz-play").hidden = true;
    $("#quiz-result").hidden = true;
  }

  function startQuiz(opts) {
    const questions = generateQuiz(opts);
    if (!questions.length) {
      showToast("출제할 문제가 없습니다");
      return;
    }
    quizSession = {
      questions,
      index: 0,
      answered: 0,
      correct: 0,
      locked: false,
      wrongOnly: !!opts.fromWrong,
    };
    $("#quiz-start").hidden = true;
    $("#quiz-result").hidden = true;
    $("#quiz-play").hidden = false;
    renderQuizQuestion();
  }

  function renderQuizQuestion() {
    const q = quizSession.questions[quizSession.index];
    if (!q) {
      finishQuiz();
      return;
    }

    quizSession.locked = false;
    const total = quizSession.questions.length;
    $("#quiz-progress-fill").style.width = `${((quizSession.index) / total) * 100}%`;
    $("#quiz-progress-text").textContent = `${quizSession.index + 1} / ${total}`;
    $("#quiz-category-chip").textContent = q.chip;
    $("#quiz-type-chip").textContent = q.type;
    $("#quiz-question").textContent = q.question;

    const keys = ["A", "B", "C", "D"];
    $("#quiz-choices").innerHTML = q.choices
      .map(
        (text, i) => `
      <button class="choice" data-choice="${i}">
        <span class="key">${keys[i] || i + 1}</span>
        <span>${escapeHtml(text)}</span>
      </button>`
      )
      .join("");

    const fb = $("#quiz-feedback");
    fb.hidden = true;
    fb.className = "quiz-feedback";
    fb.innerHTML = "";
    $("#quiz-next-btn").hidden = true;
    $("#quiz-next-btn").textContent =
      quizSession.index === total - 1 ? "결과 보기" : "다음 문제";
  }

  function answerQuiz(choiceIndex) {
    if (quizSession.locked) return;
    const q = quizSession.questions[quizSession.index];
    if (!q) return;

    quizSession.locked = true;
    const isCorrect = choiceIndex === q.correctIndex;

    // 하이라이트
    $$("#quiz-choices .choice").forEach((btn, i) => {
      btn.disabled = true;
      if (i === q.correctIndex) btn.classList.add("is-correct");
      else if (i === choiceIndex && !isCorrect) btn.classList.add("is-wrong");
    });

    const fb = $("#quiz-feedback");
    fb.hidden = false;
    fb.className = `quiz-feedback ${isCorrect ? "is-correct" : "is-wrong"}`;
    fb.innerHTML = `
      <strong>${isCorrect ? "정답입니다! 🎉" : `아쉬워요 — 정답: ${escapeHtml(q.choices[q.correctIndex])}`}</strong>
      <div>${escapeHtml(q.explanation || "")}</div>`;

    $("#quiz-next-btn").hidden = false;

    quizSession.answered += 1;
    if (isCorrect) quizSession.correct += 1;

    // 통계
    state.stats.answered += 1;
    if (isCorrect) state.stats.correct += 1;
    const day = todayKey();
    if (!state.daily[day]) state.daily[day] = { answered: 0, correct: 0 };
    state.daily[day].answered += 1;
    if (isCorrect) state.daily[day].correct += 1;

    // 오답 처리
    if (!isCorrect) {
      addWrongAnswer(q, choiceIndex);
    } else if (q.wrongKey) {
      // 오답 퀴즈에서 맞으면 마스터 처리
      const w = state.wrong.find((x) => x.id === q.wrongKey);
      if (w) {
        w.mastered = true;
        w.masteredAt = Date.now();
      }
    }

    saveState();
    renderDashboardSoft();
  }

  function addWrongAnswer(q, myIndex) {
    const existing = state.wrong.find((w) => w.sourceId === q.sourceId && w.question === q.question);
    if (existing) {
      existing.myIndex = myIndex;
      existing.at = Date.now();
      existing.mastered = false;
      existing.count = (existing.count || 1) + 1;
    } else {
      state.wrong.push({
        id: `w-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        sourceId: q.sourceId,
        category: q.category,
        type: q.type,
        question: q.question,
        choices: q.choices,
        correctIndex: q.correctIndex,
        myIndex,
        explanation: q.explanation,
        at: Date.now(),
        mastered: false,
        count: 1,
      });
    }
  }

  function nextQuizQuestion() {
    quizSession.index += 1;
    if (quizSession.index >= quizSession.questions.length) {
      finishQuiz();
    } else {
      renderQuizQuestion();
    }
  }

  function finishQuiz() {
    const total = quizSession.questions.length;
    const score = quizSession.correct;
    const pct = total ? Math.round((score / total) * 100) : 0;

    $("#quiz-play").hidden = true;
    $("#quiz-result").hidden = false;
    $("#quiz-progress-fill").style.width = "100%";

    $("#result-score").textContent = `${score}/${total}`;
    $("#result-summary").innerHTML =
      pct >= 80
        ? `정답률 <strong>${pct}%</strong> — 훌륭해요! 이 상태를 유지하세요.`
        : pct >= 50
          ? `정답률 <strong>${pct}%</strong> — 절반 이상을 맞혔어요. 오답노트로 약점을 보완해 보세요.`
          : `정답률 <strong>${pct}%</strong> — 개념 카드를 먼저 훑고 다시 도전해 보세요.`;

    updateWrongBadge();
    renderDashboardSoft();
  }

  // ── Wrong note ─────────────────────────────────────────────
  let wrongFilter = "all";

  function renderWrong() {
    let items = [...state.wrong].sort((a, b) => b.at - a.at);
    if (wrongFilter === "open") items = items.filter((w) => !w.mastered);
    if (wrongFilter === "mastered") items = items.filter((w) => w.mastered);

    $("#wrong-count").textContent = `${items.length}개`;
    $("#wrong-empty").hidden = items.length > 0;
    $("#wrong-list").innerHTML = items
      .map((w) => {
        const cat = categoryOf(w.category);
        return `
        <article class="wrong-card ${w.mastered ? "is-mastered" : ""}" data-wrong-id="${w.id}">
          <div class="wrong-top">
            <h3 class="wrong-q">${escapeHtml(w.question)}</h3>
            <span class="chip ${w.mastered ? "chip-soft" : ""}">${w.mastered ? "정복 완료" : `${cat.icon} ${cat.name}`}</span>
          </div>
          <div class="wrong-answers">
            <div class="wrong-line">
              <span class="tag tag-mine">내 답</span>
              <span>${escapeHtml(w.choices[w.myIndex] ?? "(무응답)")}</span>
            </div>
            <div class="wrong-line">
              <span class="tag tag-correct">정답</span>
              <span>${escapeHtml(w.choices[w.correctIndex] ?? "")}</span>
            </div>
            <div class="wrong-line">
              <span class="tag tag-exp">해설</span>
              <span>${escapeHtml(w.explanation || "")}</span>
            </div>
          </div>
          <div class="wrong-foot">
            <div class="wrong-meta">${formatAt(w.at)} · 틀린 횟수 ${w.count || 1}회</div>
            <div style="display:flex;gap:8px">
              <button class="btn btn-secondary" data-wrong-master="${w.id}" style="padding:8px 12px">
                ${w.mastered ? "다시 학습" : "정복 완료"}
              </button>
            </div>
          </div>
        </article>`;
      })
      .join("");
    updateWrongBadge();
  }

  // ── Events ─────────────────────────────────────────────────
  function bindEvents() {
    // Navigation
    $$(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    // Quick actions
    $$("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        if (action === "start-cards") {
          cardFilter = "unknown";
          $$("#card-filter .seg").forEach((s) =>
            s.classList.toggle("is-active", s.dataset.filter === "unknown")
          );
          cardIndex = 0;
          switchView("cards");
        } else if (action === "start-quiz") {
          switchView("quiz");
          startQuiz({ size: Number($("#quiz-size").value), category: $("#quiz-category").value });
        } else if (action === "start-wrong") {
          switchView("wrong");
        }
      });
    });

    // Cards
    $("#flashcard").addEventListener("click", flipCard);
    $("#flashcard").addEventListener("keydown", (e) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        flipCard();
      }
    });
    $("#card-prev").addEventListener("click", () => moveCard(-1));
    $("#card-next").addEventListener("click", () => moveCard(1));
    $("#card-known").addEventListener("click", () => markCard(true));
    $("#card-unknown").addEventListener("click", () => markCard(false));
    $("#card-shuffle").addEventListener("click", () => {
      cardDeck = shuffle(cardDeck);
      cardIndex = 0;
      renderCard();
      showToast("카드를 셔플했어요");
    });

    $$("#card-filter .seg").forEach((seg) => {
      seg.addEventListener("click", () => {
        $$("#card-filter .seg").forEach((s) => s.classList.remove("is-active"));
        seg.classList.add("is-active");
        cardFilter = seg.dataset.filter;
        cardIndex = 0;
        renderCard();
      });
    });

    // Vocab
    $("#vocab-search").addEventListener("input", renderVocab);
    $("#vocab-category").addEventListener("change", renderVocab);
    $("#vocab-list").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-toggle-known]");
      if (!btn) return;
      const id = btn.dataset.toggleKnown;
      state.known[id] = !state.known[id];
      saveState();
      renderVocab();
      renderDashboardSoft();
      showToast(state.known[id] ? "외운 것으로 표시했어요" : "학습 중으로 되돌렸어요");
    });

    // Quiz
    $("#quiz-start-btn").addEventListener("click", () => {
      startQuiz({
        size: Number($("#quiz-size").value),
        category: $("#quiz-category").value,
      });
    });
    $("#quiz-choices").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-choice]");
      if (!btn) return;
      answerQuiz(Number(btn.dataset.choice));
    });
    $("#quiz-next-btn").addEventListener("click", nextQuizQuestion);
    $("#quiz-retry").addEventListener("click", () => {
      resetQuizScreens();
      startQuiz({
        size: Number($("#quiz-size").value),
        category: $("#quiz-category").value,
      });
    });
    $("#quiz-goto-wrong").addEventListener("click", () => switchView("wrong"));

    // Wrong
    $$("#wrong-filter .seg").forEach((seg) => {
      seg.addEventListener("click", () => {
        $$("#wrong-filter .seg").forEach((s) => s.classList.remove("is-active"));
        seg.classList.add("is-active");
        wrongFilter = seg.dataset.filter;
        renderWrong();
      });
    });

    $("#wrong-list").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-wrong-master]");
      if (!btn) return;
      const id = btn.dataset.wrongMaster;
      const item = state.wrong.find((w) => w.id === id);
      if (!item) return;
      item.mastered = !item.mastered;
      if (item.mastered) item.masteredAt = Date.now();
      saveState();
      renderWrong();
      showToast(item.mastered ? "정복 완료로 표시했어요 🎉" : "다시 학습 목록으로 옮겼어요");
    });

    $("#wrong-review-btn").addEventListener("click", () => {
      const open = state.wrong.filter((w) => !w.mastered);
      if (!open.length) {
        showToast("복습할 오답이 없습니다");
        return;
      }
      switchView("quiz");
      startQuiz({ fromWrong: true, size: open.length });
    });

    $("#wrong-clear").addEventListener("click", () => {
      const before = state.wrong.length;
      state.wrong = state.wrong.filter((w) => !w.mastered);
      const removed = before - state.wrong.length;
      saveState();
      renderWrong();
      showToast(removed ? `정복 완료 ${removed}개를 비웠어요` : "비울 항목이 없습니다");
    });

    // Reset
    $("#reset-progress").addEventListener("click", () => {
      if (!confirm("학습 진도·오답·통계를 모두 초기화할까요?")) return;
      state = structuredClone(defaultState);
      saveState();
      renderDashboard();
      renderCard();
      renderVocab();
      renderWrong();
      showToast("진도를 초기화했어요");
    });

    // Keyboard shortcuts (cards)
    document.addEventListener("keydown", (e) => {
      const cardsView = $("#view-cards").classList.contains("is-active");
      if (!cardsView) return;
      if (e.target.matches("input, select, textarea")) return;

      if (e.key === "ArrowLeft") moveCard(-1);
      if (e.key === "ArrowRight") moveCard(1);
      if (e.key.toLowerCase() === "k") markCard(true);
      if (e.key.toLowerCase() === "x") markCard(false);
    });
  }

  // ── Select options ─────────────────────────────────────────
  function fillCategorySelects() {
    const options = CATEGORIES.map((c) => `<option value="${c.id}">${c.icon} ${c.name}</option>`).join("");
    const targets = ["#card-category", "#vocab-category", "#quiz-category"];
    targets.forEach((sel) => {
      const el = $(sel);
      if (!el) return;
      const allLabel = el.querySelector('option[value="all"]');
      el.innerHTML = "";
      if (allLabel) el.appendChild(allLabel);
      el.insertAdjacentHTML("beforeend", options);
    });

    $("#card-category").addEventListener("change", (e) => {
      cardCategory = e.target.value;
      cardIndex = 0;
      renderCard();
    });
  }

  // ── Init ───────────────────────────────────────────────────
  function init() {
    fillCategorySelects();
    bindEvents();
    renderDashboard();
    renderCard();
    renderVocab();
    renderWrong();
  }

  init();
})();
