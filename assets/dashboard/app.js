const sections = [
  ["overview", "Overview", "◇"], ["programs", "Programs", "P"], ["faculty", "Faculty", "F"],
  ["materials", "Materials", "M"], ["recommenders", "Letters", "L"], ["tasks", "Tasks", "T"],
  ["contacts", "Outreach", "O"], ["interviews", "Interviews", "I"], ["offers", "Offers", "$"],
  ["profile", "Profile", "@"], ["research-narrative", "Research story", "R"], ["offer-decision", "Offer decision", "D"], ["wellbeing-plan", "Wellbeing", "W"],
];

const tableConfig = {
  programs: { description: "Programs, requirements, funding, fit, and source freshness.", columns: ["institution", "program", "country", "deadline_date", "status", "verification_status"] },
  faculty: { description: "Research and mentoring fit across every plausible advisor.", columns: ["faculty_name", "program_id", "question_fit", "recruiting_status", "last_checked"] },
  materials: { description: "Every prompt, version, reviewer, and deadline—kept separate.", columns: ["document_type", "program_id", "word_or_page_limit", "version", "status", "deadline_date"] },
  recommenders: { description: "Letter strength, evidence packets, reminders, and submission state.", columns: ["recommender_name", "relationship", "strong_letter_confirmed", "next_reminder_date", "status"] },
  tasks: { description: "A deadline-aware queue for the work that moves applications forward.", columns: ["task", "program_id", "owner", "due_date", "priority", "status"] },
  contacts: { description: "Purposeful faculty and admissions communication without inbox guesswork.", columns: ["contact_name", "program_id", "purpose", "sent_date", "response_status"] },
  interviews: { description: "Preparation, research conversations, questions, and follow-up evidence.", columns: ["program_id", "interview_date", "participants", "format", "status"] },
  offers: { description: "Compare people, funding, climate, accessibility, risks, and unknowns.", columns: ["program_id", "advisor_fit", "funding_amount", "funding_duration", "concerns", "decision_status"] },
};

const humanize = (value) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const today = () => new Date().toISOString().slice(0, 10);
let state = null;
let active = "overview";
let editingIndex = -1;

const navigation = document.querySelector("#navigation");
const content = document.querySelector("#content");
const pageTitle = document.querySelector("#page-title");
const pageDescription = document.querySelector("#page-description");
const eyebrow = document.querySelector("#eyebrow");
const action = document.querySelector("#primary-action");
const saveStatus = document.querySelector("#save-status");
const dialog = document.querySelector("#record-dialog");
const form = document.querySelector("#record-form");
const recordFields = document.querySelector("#record-fields");

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function setStatus(message, error = false) {
  saveStatus.textContent = message;
  saveStatus.style.color = error ? "#a63a3a" : "#667085";
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed: ${response.status}`);
  return payload;
}

function renderNavigation() {
  navigation.replaceChildren();
  sections.forEach(([id, label, icon]) => {
    const button = node("button", `nav-button${active === id ? " active" : ""}`);
    button.type = "button";
    button.dataset.section = id;
    button.append(node("span", "nav-icon", icon), node("span", "", label));
    navigation.append(button);
  });
}

function labelFor(id) {
  return sections.find(([section]) => section === id)?.[1] || humanize(id);
}

function setHeading(title, description) {
  pageTitle.textContent = title;
  pageDescription.textContent = description;
  eyebrow.textContent = `${state.profile.cycle || "CURRENT"} APPLICATION CYCLE`;
}

function daysUntil(raw) {
  if (!raw) return null;
  const date = new Date(`${raw}T12:00:00Z`);
  if (Number.isNaN(date.valueOf())) return null;
  return Math.ceil((date - new Date()) / 86400000);
}

function overviewCard(label, value) {
  const card = node("article", "card stat");
  card.append(node("span", "", label), node("strong", "", String(value)));
  return card;
}

function renderOverview() {
  setHeading("Overview", "See deadlines, materials, and risks in one place.");
  action.hidden = true;
  const programs = state.tables.programs.rows;
  const materials = state.tables.materials.rows;
  const upcoming = programs.filter((row) => {
    const days = daysUntil(row.deadline_date);
    return days !== null && days >= 0 && days <= 30 && !["submitted", "complete", "withdrawn"].includes(row.status.toLowerCase());
  });
  const unfinished = materials.filter((row) => !["final", "submitted", "complete"].includes(row.status.toLowerCase()));

  const stats = node("div", "stats");
  stats.append(
    overviewCard("Programs", programs.length),
    overviewCard("Faculty matches", state.tables.faculty.rows.length),
    overviewCard("Open materials", unfinished.length),
    overviewCard("Deadlines ≤ 30 days", upcoming.length),
  );

  const alerts = [];
  upcoming.forEach((row) => alerts.push({ text: `${row.institution || row.program_id} deadline`, detail: `${row.deadline_date} · ${row.deadline_timezone || "time zone missing"}` }));
  programs.forEach((row) => {
    const age = row.last_checked ? Math.floor((new Date() - new Date(`${row.last_checked}T12:00:00`)) / 86400000) : null;
    if (!row.official_url || !row.last_checked) alerts.push({ text: `${row.institution || row.program_id} needs source verification`, detail: "Official URL or last-checked date missing" });
    else if (age > 45) alerts.push({ text: `${row.institution || row.program_id} has stale requirements`, detail: `Last checked ${row.last_checked}` });
  });
  state.tables.recommenders.rows.forEach((row) => {
    if (!["yes", "true", "confirmed"].includes(row.strong_letter_confirmed.toLowerCase())) alerts.push({ text: `${row.recommender_name || "A recommender"}: strong letter not confirmed`, detail: row.status || "Needs attention" });
  });

  const section = node("section", "card section");
  const head = node("div", "section-head");
  const copy = node("div"); copy.append(node("h2", "", "Attention queue"), node("p", "", "The dashboard surfaces risk; official pages remain authoritative."));
  head.append(copy, node("span", "badge", `${alerts.length} item${alerts.length === 1 ? "" : "s"}`));
  section.append(head);
  const list = node("div", "alert-list");
  if (!alerts.length) list.append(node("div", "empty", "No immediate risks found. Run the audit script before submitting."));
  alerts.slice(0, 10).forEach((item) => {
    const row = node("div", "alert"); row.append(node("span", "", item.text), node("small", "", item.detail)); list.append(row);
  });
  section.append(list);
  content.replaceChildren(stats, section);
}

function formatCell(field, value) {
  if (!value) return "—";
  return value.length > 120 ? `${value.slice(0, 117)}…` : value;
}

function renderTable(name, query = "") {
  const config = tableConfig[name];
  const table = state.tables[name];
  setHeading(labelFor(name), config.description);
  action.hidden = false;
  action.textContent = `Add ${labelFor(name).replace(/s$/, "").toLowerCase()}`;
  action.dataset.table = name;

  const toolbar = node("div", "toolbar");
  const search = node("input", "search");
  search.type = "search"; search.placeholder = `Filter ${labelFor(name).toLowerCase()}…`; search.value = query; search.dataset.searchTable = name;
  toolbar.append(search, node("span", "badge", `${table.rows.length} record${table.rows.length === 1 ? "" : "s"}`));

  const wrap = node("div", "table-wrap");
  const element = node("table");
  const thead = node("thead"); const headerRow = node("tr");
  config.columns.forEach((field) => headerRow.append(node("th", "", humanize(field))));
  headerRow.append(node("th", "", "Actions")); thead.append(headerRow); element.append(thead);
  const tbody = node("tbody");
  const lowered = query.trim().toLowerCase();
  const rows = table.rows.map((row, index) => ({ row, index })).filter(({ row }) => !lowered || Object.values(row).some((value) => String(value).toLowerCase().includes(lowered)));
  rows.forEach(({ row, index }) => {
    const tr = node("tr");
    config.columns.forEach((field, columnIndex) => {
      const td = node("td", columnIndex === 0 ? "row-title" : "", formatCell(field, row[field] || ""));
      tr.append(td);
    });
    const actions = node("td", "row-actions");
    const edit = node("button", "text-button", "Edit"); edit.type = "button"; edit.dataset.editIndex = String(index); edit.dataset.table = name;
    const remove = node("button", "text-button danger", "Delete"); remove.type = "button"; remove.dataset.deleteIndex = String(index); remove.dataset.table = name;
    actions.append(edit, remove); tr.append(actions); tbody.append(tr);
  });
  if (!rows.length) {
    const tr = node("tr"); const td = node("td", "empty", query ? "No records match this filter." : "No records yet. Add one when you are ready."); td.colSpan = config.columns.length + 1; tr.append(td); tbody.append(tr);
  }
  element.append(tbody); wrap.append(element); content.replaceChildren(toolbar, wrap);
}

function inputFor(field, value) {
  const holder = node("div", `field${["prompt", "notes", "fit_thesis", "primary_risk", "evidence_themes", "questions_to_ask", "evidence_learned", "concerns", "unknowns"].includes(field) ? " full" : ""}`);
  const label = node("label", "", humanize(field)); label.htmlFor = `field-${field}`;
  const long = ["prompt", "notes", "fit_thesis", "primary_risk", "funding_summary", "evidence_themes", "question_fit", "method_fit", "purpose", "authoritative_answer", "questions_to_ask", "evidence_learned", "mentoring_evidence", "concerns", "unknowns"].includes(field);
  const input = node(long ? "textarea" : "input"); input.id = `field-${field}`; input.name = field; input.value = value || "";
  if (field.includes("date") || field === "last_checked") input.type = "date";
  if (field.includes("url")) input.type = "url";
  holder.append(label, input); return holder;
}

function openRecordDialog(name, index = -1) {
  editingIndex = index;
  form.dataset.table = name;
  document.querySelector("#dialog-title").textContent = `${index >= 0 ? "Edit" : "Add"} ${labelFor(name).replace(/s$/, "").toLowerCase()}`;
  recordFields.replaceChildren();
  const table = state.tables[name];
  const row = index >= 0 ? table.rows[index] : {};
  table.fields.forEach((field) => recordFields.append(inputFor(field, row[field])));
  dialog.showModal();
}

async function saveTable(name, rows) {
  setStatus("Saving…");
  try {
    const payload = await api(`/api/table/${name}`, { method: "PUT", body: JSON.stringify({ rows }) });
    state.tables[name].rows = payload.rows;
    setStatus(`Saved ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`);
  } catch (error) {
    setStatus(error.message, true); throw error;
  }
}

function renderProfile() {
  setHeading("Applicant profile", "Cycle goals and constraints used by both the dashboard and your AI collaborator.");
  action.hidden = true;
  const section = node("section", "card section");
  const profileForm = node("form", "profile-grid"); profileForm.id = "profile-form";
  Object.entries(state.profile).forEach(([field, value]) => {
    if (["created_at", "updated_at"].includes(field)) return;
    const display = Array.isArray(value) ? value.join("\n") : value ?? "";
    profileForm.append(inputFor(field, String(display)));
  });
  const actions = node("div", "field full"); const save = node("button", "button primary", "Save profile"); save.type = "submit"; actions.append(save); profileForm.append(actions); section.append(profileForm); content.replaceChildren(section);
}

function renderNote(name) {
  const title = labelFor(name);
  const descriptions = {
    "research-narrative": "Develop a coherent question-led story from real evidence.",
    "offer-decision": "Turn the comparison table into a reasoned decision without averaging away veto conditions.",
    "wellbeing-plan": "Keep the application sustainable and connected to life outside admission.",
  };
  setHeading(title, descriptions[name]);
  action.hidden = true;
  const section = node("section", "card section");
  const editor = node("textarea", "note-editor"); editor.id = "note-editor"; editor.value = state.notes[name]; editor.setAttribute("aria-label", title);
  const controls = node("div", "dialog-actions"); controls.style.position = "static"; controls.style.margin = "16px 0 0";
  const save = node("button", "button primary", "Save note"); save.type = "button"; save.dataset.saveNote = name; controls.append(save); section.append(editor, controls); content.replaceChildren(section);
}

function render() {
  renderNavigation();
  if (active === "overview") renderOverview();
  else if (tableConfig[active]) renderTable(active);
  else if (active === "profile") renderProfile();
  else renderNote(active);
}

navigation.addEventListener("click", (event) => {
  const button = event.target.closest("[data-section]"); if (!button) return;
  active = button.dataset.section; render();
});

action.addEventListener("click", () => openRecordDialog(action.dataset.table));
document.querySelector("#cancel-dialog").addEventListener("click", () => dialog.close());

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = form.dataset.table;
  const row = Object.fromEntries(new FormData(form).entries());
  const idField = state.tables[name].fields.find((field) => field.endsWith("_id"));
  if (idField && !row[idField]) row[idField] = `${name.slice(0, 4)}-${Date.now().toString(36)}`;
  if (row.last_checked === "") row.last_checked = today();
  const rows = [...state.tables[name].rows];
  if (editingIndex >= 0) rows[editingIndex] = row; else rows.push(row);
  try { await saveTable(name, rows); dialog.close(); renderTable(name); } catch (_) { /* status already shown */ }
});

content.addEventListener("input", (event) => {
  if (event.target.dataset.searchTable) renderTable(event.target.dataset.searchTable, event.target.value);
});

content.addEventListener("click", async (event) => {
  const edit = event.target.closest("[data-edit-index]");
  if (edit) { openRecordDialog(edit.dataset.table, Number(edit.dataset.editIndex)); return; }
  const remove = event.target.closest("[data-delete-index]");
  if (remove) {
    const name = remove.dataset.table; const index = Number(remove.dataset.deleteIndex);
    if (!window.confirm("Delete this local record? A backup will be kept in archive/dashboard-backups.")) return;
    const rows = state.tables[name].rows.filter((_, rowIndex) => rowIndex !== index);
    await saveTable(name, rows); renderTable(name); return;
  }
  const note = event.target.closest("[data-save-note]");
  if (note) {
    const name = note.dataset.saveNote; setStatus("Saving…");
    try { const payload = await api(`/api/note/${name}`, { method: "PUT", body: JSON.stringify({ content: document.querySelector("#note-editor").value }) }); state.notes[name] = payload.content; setStatus("Saved"); }
    catch (error) { setStatus(error.message, true); }
  }
});

content.addEventListener("submit", async (event) => {
  if (event.target.id !== "profile-form") return;
  event.preventDefault();
  const entries = Object.fromEntries(new FormData(event.target).entries());
  const profile = { ...state.profile };
  Object.entries(entries).forEach(([field, value]) => {
    profile[field] = Array.isArray(profile[field]) ? value.split(/\n|,/).map((item) => item.trim()).filter(Boolean) : value;
  });
  setStatus("Saving…");
  try { const payload = await api("/api/profile", { method: "PUT", body: JSON.stringify(profile) }); state.profile = payload.profile; setStatus("Saved"); renderProfile(); }
  catch (error) { setStatus(error.message, true); }
});

async function start() {
  try { state = await api("/api/state"); render(); }
  catch (error) { setHeading("Dashboard unavailable", "Check that the workspace was initialized correctly."); content.append(node("div", "card empty", error.message)); setStatus("Load failed", true); }
}

start();
