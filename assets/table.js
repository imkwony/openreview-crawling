// Shared ranked-papers table. Each row of papers.json is:
// [paperId, title, rank, rankByAI, aiWritten, status, keywords, publishedYYYYMM (journals only)]
// (null = blank; status: A/R/W/D/U, see STATUS; keywords: array of strings, searched with the title)
(function () {
  const BATCH = 500;
  const dataUrl = document.currentScript.dataset.papers; // set on the page's <script> tag
  const FORUM = document.currentScript.dataset.link || "https://openreview.net/forum?id="; // journals link to the DOI instead
  const $ = (sel) => document.querySelector(sel);
  const input = $("#q"), status = $("#status"), tbody = $("#rows"), more = $("#more");
  const COLS = { rank: 2, jev: 3, ai: 4, date: 7 };
  const filterBtn = $("#accept-filter-btn"), filterMenu = $("#accept-filter");
  // Accept column status codes -> what to show. Order here is the filter menu order.
  const STATUS = {
    A: { text: "✅", label: "Accepted" },
    R: { text: "❌", label: "Rejected" },
    W: { text: "🏳️", label: "Withdrawn" },
    D: { text: "🙅‍♂️🙅‍♀️", label: "Desk-rejected" },
    U: { text: "⏳", label: "Under review" },
  };
  const STATUS_ORDER = Object.keys(STATUS);

  let papers = [], haystack = [], shown = [], next = 0, timer = 0;
  const hasDate = !!$("button.sort[data-key=date]"); // journal pages: a Published column, newest first
  let sortKey = hasDate ? "date" : "rank", sortDir = hasDate ? -1 : 1;
  if (hasDate) {
    document.querySelectorAll("thead th[aria-sort]").forEach((th) => th.setAttribute("aria-sort", "none"));
    $("button.sort[data-key=date]").closest("th").setAttribute("aria-sort", "descending");
  }
  let available = [], selected = new Set(); // statuses present in the data / currently shown

  const isAll = () => available.every((c) => selected.has(c));

  const sortValue = (row, key) => {
    const v = row[COLS[key]];
    return v === null || v === undefined ? null : v;
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
      accept.title = status.label;
      accept.setAttribute("aria-label", status.label);
    }
    const keywords = cell((row[6] || []).join(", "), "kw");
    if (row[6] && row[6].length) { // narrow screens show keywords under the title instead of a column
      const sub = document.createElement("div");
      sub.className = "kw-sub";
      sub.textContent = row[6].join(", ");
      title.appendChild(sub);
    }
    const month = row[7] ? Math.floor(row[7] / 100) + "-" + String(row[7] % 100).padStart(2, "0") : "";
    tr.append(id, title, keywords);
    if (hasDate) tr.append(cell(month, "num"));
    tr.append(num(row[2]), num(row[3]), num(row[4]), accept);
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
    const everyStatus = isAll();
    shown = papers.filter((p, i) =>
      (everyStatus || selected.has(p[5])) && words.every((w) => haystack[i].includes(w)));
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

  // ---- Accept status filter ---------------------------------------------------
  const closeMenu = () => { filterMenu.hidden = true; filterBtn.setAttribute("aria-expanded", "false"); };

  function buildFilterMenu() {
    const counts = {};
    for (const p of papers) counts[p[5]] = (counts[p[5]] || 0) + 1;
    available = STATUS_ORDER.filter((c) => counts[c]); // skip statuses this conference has none of
    selected = new Set(available);
    filterMenu.textContent = "";
    const boxes = [];
    for (const code of available) {
      const label = document.createElement("label");
      label.className = "filter-item";
      const box = document.createElement("input");
      box.type = "checkbox";
      box.checked = true;
      box.addEventListener("change", () => {
        if (box.checked) selected.add(code); else selected.delete(code);
        applyFilter();
      });
      boxes.push([code, box]);
      label.append(box, " " + STATUS[code].text + " " + STATUS[code].label + " (" + counts[code].toLocaleString() + ")");
      filterMenu.appendChild(label);
    }
    const all = document.createElement("button");
    all.type = "button";
    all.className = "filter-all";
    all.textContent = "Show all";
    all.addEventListener("click", () => {
      selected = new Set(available);
      boxes.forEach(([, box]) => { box.checked = true; });
      applyFilter();
    });
    filterMenu.appendChild(all);
    filterBtn.classList.remove("active");
  }

  function applyFilter() {
    filterBtn.classList.toggle("active", !isAll());
    refresh();
  }

  filterBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = filterMenu.hidden;
    closeTips();
    filterMenu.hidden = !open;
    filterBtn.setAttribute("aria-expanded", String(open));
  });

  const closeTips = () =>
    document.querySelectorAll(".info-btn").forEach((b) => b.setAttribute("aria-expanded", "false"));
  document.querySelectorAll(".info-btn").forEach((btn) => btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = btn.getAttribute("aria-expanded") === "true";
    closeTips();
    closeMenu();
    btn.setAttribute("aria-expanded", String(!open));
  }));
  document.addEventListener("click", (e) => {
    closeTips();
    if (!filterMenu.contains(e.target)) closeMenu();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closeTips(); closeMenu(); } });

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
    haystack = papers.map((p) => (p[1] + " " + p[0] + " " + (p[6] || []).join(" ")).toLowerCase());
    buildFilterMenu();
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
