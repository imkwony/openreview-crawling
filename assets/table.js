// Shared ranked-papers table. Each row of papers.json is:
// [paperId, title, rank, rankByAI, aiWritten, accept]   (null = blank, accept: 1 = yes, 0 = no)
(function () {
  const BATCH = 500;
  const FORUM = "https://openreview.net/forum?id=";
  const $ = (sel) => document.querySelector(sel);
  const input = $("#q"), status = $("#status"), tbody = $("#rows"), more = $("#more");
  const COLS = { rank: 2, jev: 3, ai: 4, accept: 5 };

  let papers = [], haystack = [], shown = [], next = 0, timer = 0;
  let sortKey = "rank", sortDir = 1;

  const sortValue = (row, key) => {
    const v = row[COLS[key]];
    if (v === null || v === undefined) return null;
    return key === "accept" ? (v === 1 ? 0 : 1) : v; // accepted first, then rejected
  };

  const tie = (a, b) =>
    a[1].toLowerCase().localeCompare(b[1].toLowerCase()) || a[0].localeCompare(b[0]);

  function compare(a, b) {
    const x = sortValue(a, sortKey), y = sortValue(b, sortKey);
    if (x === null || y === null) return x === y ? tie(a, b) : x === null ? 1 : -1; // blanks last
    return x !== y ? (x - y) * sortDir : tie(a, b);
  }

  function cell(text, cls) {
    const td = document.createElement("td");
    if (cls) td.className = cls;
    td.textContent = text;
    return td;
  }

  function renderRow(row) {
    const tr = document.createElement("tr");
    const id = cell("", "id"), title = cell("");
    for (const [td, text] of [[id, row[0]], [title, row[1]]]) {
      const a = document.createElement("a");
      a.href = FORUM + encodeURIComponent(row[0]);
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = text;
      td.appendChild(a);
    }
    const num = (v) => cell(v === null ? "" : String(v), "num");
    const accept = cell("", "accept");
    if (row[5] === 1) {
      accept.textContent = "✓"; accept.classList.add("ok"); accept.title = "Accepted";
    } else if (row[5] === 0) {
      accept.textContent = "✗"; accept.classList.add("no"); accept.title = "Not accepted";
    }
    tr.append(id, title, num(row[2]), num(row[3]), num(row[4]), accept);
    return tr;
  }

  function renderMore() {
    const end = Math.min(next + BATCH, shown.length);
    const frag = document.createDocumentFragment();
    for (; next < end; next++) frag.appendChild(renderRow(shown[next]));
    tbody.appendChild(frag);
    status.textContent =
      "Showing " + shown.length.toLocaleString() + " of " + papers.length.toLocaleString() + " papers";
  }

  function refresh() {
    const words = input.value.toLowerCase().split(/\s+/).filter(Boolean);
    shown = papers.filter((_, i) => words.every((w) => haystack[i].includes(w)));
    shown.sort(compare);
    tbody.textContent = "";
    next = 0;
    renderMore();
  }

  input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(refresh, 120); });

  document.querySelectorAll("button.sort").forEach((btn) => btn.addEventListener("click", () => {
    const key = btn.dataset.key;
    sortDir = key === sortKey ? -sortDir : 1;
    sortKey = key;
    document.querySelectorAll("thead th[aria-sort]").forEach((th) => th.setAttribute("aria-sort", "none"));
    btn.closest("th").setAttribute("aria-sort", sortDir === 1 ? "ascending" : "descending");
    refresh();
  }));

  const closeTips = () =>
    document.querySelectorAll(".info-btn").forEach((b) => b.setAttribute("aria-expanded", "false"));
  document.querySelectorAll(".info-btn").forEach((btn) => btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = btn.getAttribute("aria-expanded") === "true";
    closeTips();
    btn.setAttribute("aria-expanded", String(!open));
  }));
  document.addEventListener("click", closeTips);

  new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting) && next < shown.length) renderMore();
  }, { rootMargin: "600px" }).observe(more);

  // The page passes the data file's address (with a version tag) via data-papers.
  fetch(document.currentScript.dataset.papers)
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((data) => {
      papers = data;
      haystack = papers.map((p) => (p[1] + " " + p[0]).toLowerCase());
      input.disabled = false;
      refresh();
    })
    .catch(() => { status.textContent = "Could not load the papers. Please reload the page."; });
})();
