// Shared ranked-papers table. Each row of papers.json is:
// [paperId, title, rank, rankByAI, aiWritten, status]   (null = blank; status: A/R/W/D/U, see STATUS)
(function () {
  const BATCH = 500;
  const dataUrl = document.currentScript.dataset.papers; // set on the page's <script> tag
  const FORUM = "https://openreview.net/forum?id=";
  const $ = (sel) => document.querySelector(sel);
  const input = $("#q"), status = $("#status"), tbody = $("#rows"), more = $("#more");
  const COLS = { rank: 2, jev: 3, ai: 4, accept: 5 };
  // Accept column status codes -> what to show. Order here is the sort order.
  const STATUS = {
    A: { text: "✓", cls: "ok", label: "Accepted" },
    R: { text: "✗", cls: "no", label: "Rejected" },
    W: { text: "🏳️", cls: "", label: "Withdrawn" },
    D: { text: "🙅‍♂️🙅‍♀️", cls: "", label: "Desk-rejected" },
    U: { text: "⏳", cls: "", label: "Under review" },
  };
  const STATUS_ORDER = Object.keys(STATUS);

  let papers = [], haystack = [], shown = [], next = 0, timer = 0;
  let sortKey = "rank", sortDir = 1;

  const sortValue = (row, key) => {
    const v = row[COLS[key]];
    if (v === null || v === undefined) return null;
    return key === "accept" ? STATUS_ORDER.indexOf(v) : v;
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
    const status = STATUS[row[5]];
    if (status) {
      accept.textContent = status.text;
      if (status.cls) accept.classList.add(status.cls);
      accept.title = status.label;
      accept.setAttribute("aria-label", status.label);
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

  // ---- Password gate -------------------------------------------------------
  // papers.enc.json is gzip + AES-256-GCM, key = PBKDF2-SHA256(normalized password).
  // Keep in sync with crawler/crypto.py.
  const gate = $("#gate"), content = $("#content"), pw = $("#pw"), gateMsg = $("#gate-msg");
  const KEY = "openreview-crawling:pw:" + dataUrl;
  const b64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
  const normalize = (s) => s.toLowerCase().split(/\s+/).filter(Boolean).join(" ");

  async function decrypt(enc, password) {
    const material = await crypto.subtle.importKey(
      "raw", new TextEncoder().encode(normalize(password)), "PBKDF2", false, ["deriveKey"]);
    const key = await crypto.subtle.deriveKey(
      { name: "PBKDF2", salt: b64(enc.salt), iterations: enc.iter, hash: "SHA-256" },
      material, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
    const sealed = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(enc.iv) }, key, b64(enc.data));
    const text = await new Response(
      new Blob([sealed]).stream().pipeThrough(new DecompressionStream("gzip"))).text();
    return JSON.parse(text);
  }

  // Start downloading right away so unlocking is quick once the password is typed.
  const encrypted = fetch(dataUrl).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
  encrypted.catch(() => {});

  function unlock(data) {
    papers = data;
    haystack = papers.map((p) => (p[1] + " " + p[0]).toLowerCase());
    gate.hidden = true;
    content.hidden = false;
    input.disabled = false;
    refresh();
  }

  async function tryPassword(password, silent) {
    if (!silent) gateMsg.textContent = "";
    let enc;
    try { enc = await encrypted; }
    catch { if (!silent) gateMsg.textContent = "Could not load the data. Please reload the page."; return false; }
    let data;
    try { data = await decrypt(enc, password); }
    catch { if (!silent) gateMsg.textContent = "Wrong password."; return false; }
    try { sessionStorage.setItem(KEY, password); } catch (e) { /* storage unavailable: just ask again next time */ }
    unlock(data);
    return true;
  }

  gate.addEventListener("submit", (e) => { e.preventDefault(); tryPassword(pw.value, false); });

  // Remember the password for this browser tab only, so a refresh doesn't ask again.
  try {
    const saved = sessionStorage.getItem(KEY);
    if (saved) tryPassword(saved, true).then((ok) => { if (!ok) sessionStorage.removeItem(KEY); });
  } catch (e) { /* storage unavailable */ }
})();
