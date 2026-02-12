const API_URL = "http://localhost:8000"; // Base API URL
const MAX_VISIBLE_GAUS = 5;
let currentResults = null; // Store search results for downloads
let examiners = []; // Store examiner names
let lawfirms = []; // Store law firm names
let patentContext = null;
let lastQueryType = null;
let prosecutors = []; // Store prosecutor names
// "patent" | "examiner" | "lawfirm" | "attorney"

document.addEventListener("DOMContentLoaded", function () {
  const fromDateInput = document.getElementById("fromDateAll");
  const toDateInput = document.getElementById("toDateAll");

  const fromDate = document.getElementById("fromDate");
  const toDate = document.getElementById("toDate");

  const today = new Date();
  const oneYearBack = new Date();

  oneYearBack.setFullYear(today.getFullYear() - 1);

  // Format as YYYY-MM-DD
  const formatDate = (date) => {
    return date.toISOString().split("T")[0];
  };

  toDateInput.value = formatDate(today);
  fromDateInput.value = formatDate(oneYearBack);

  toDate.value = formatDate(today);
  fromDate.value = formatDate(oneYearBack);
});

const sortDropdown = document.getElementById("statsSortOrder");
const limitLabel = document.getElementById("statsLimitLabel");

function updateStatsLimitLabel() {
  if (sortDropdown.value === "asc") {
    limitLabel.textContent = "Number of Least Stats:";
  } else {
    limitLabel.textContent = "Number of Top Stats:";
  }
}

// Run once on page load
updateStatsLimitLabel();

// Update whenever user changes sort
sortDropdown.addEventListener("change", updateStatsLimitLabel);

const statsTypeDropdown = document.getElementById("statsType");
const getStatsBtn = document.getElementById("getStatsBtn");

function updateGetStatsButtonText() {
  const selected = statsTypeDropdown.value;

  const labelMap = {
    examiner: "Examiner Stats",
    prosecutor: "Prosecutor Stats",
    lawfirm: "Law Firm Stats",
    gau: "GAU Stats",
    assignee: "Assignee Stats",
    usc: "USC Class Stats",
    entity: "Entity Type Stats",
    action: "Action Code Stats",
  };

  getStatsBtn.textContent = `📈 Get ${labelMap[selected] || "Stats"}`;
}

// Run once on page load
updateGetStatsButtonText();

// Update whenever dropdown changes
statsTypeDropdown.addEventListener("change", updateGetStatsButtonText);

// -------------------------------
// Prosecutor Input Handling
// -------------------------------
document.getElementById("prosecutorInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    const value = e.target.value.trim();
    if (!value) return;

    prosecutors.push(value);
    e.target.value = "";
    renderProsecutorTags();
  }
});

function addAdvancedFilter() {
  const container = document.getElementById("advancedFilters");

  const filterRow = document.createElement("div");
  filterRow.className = "advanced-filter";

  filterRow.innerHTML = `
    <select class="field">
      <option value="id">Patent ID</option>
      <option value="title">Title</option>
      <option value="examiner">Examiner</option>
      <option value="law_firm">Law Firm</option>
      <option value="all_attorney_names">Attorney / Prosecutor</option>
      <option value="disposal_type">Disposal Type</option>
      <option value="app_date_year">Application Year</option>
    </select>

    <select class="operator">
      <option value="equals">Equals</option>
      <option value="contains">Contains</option>
      <option value="starts_with">Starts With</option>
      <option value="range">Range</option>
    </select>

    <input class="value" placeholder="Enter value" />

    <button onclick="removeAdvancedFilter(this)">❌</button>
  `;

  container.appendChild(filterRow);
}

function renderProsecutorTags() {
  hideError();
  const container = document.getElementById("prosecutorTags");
  container.innerHTML = prosecutors
    .map(
      (name, i) =>
        `<span class="tag">
          ${name}
          <button onclick="removeProsecutor(${i})">×</button>
        </span>`,
    )
    .join("");
}

function removeProsecutor(index) {
  prosecutors.splice(index, 1);
  renderProsecutorTags();
}

// -------------------------------
// Search by Prosecutor
// -------------------------------
async function searchByProsecutor() {
  hideError();

  if (prosecutors.length === 0) {
    showError("Please add at least one prosecutor");
    return;
  }

  const searchType = document.querySelector(
    'input[name="prosecutorType"]:checked',
  )?.value;

  const limit =
    parseInt(document.getElementById("prosecutorLimit").value) || 10;

  try {
    lastQueryType = "attorney";

    const res = await fetch(`${API_URL}/build/prosecutor-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prosecutors,
        search_type: searchType,
        limit,
      }),
    });

    if (!res.ok) throw new Error("Failed to build prosecutor query");

    const data = await res.json();
    displayUrl(data.solr_query_url);
  } catch (error) {
    console.error(error);
    showError(error.message);
  }
}

// -------------------------------
// Examiner Input Handling
// -------------------------------
document.getElementById("examinerInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    const value = e.target.value.trim();
    if (!value) return;

    examiners.push(value);
    e.target.value = "";
    renderExaminerTags();
  }
});

// Remaininder tags
function renderExaminerTags() {
  hideError();
  const container = document.getElementById("examinerTags");
  container.innerHTML = examiners
    .map(
      (name, i) =>
        `<span class="tag">
            ${name}
            <button onclick="removeExaminer(${i})">×</button>
          </span>`,
    )
    .join("");
}

function removeExaminer(index) {
  examiners.splice(index, 1);
  renderExaminerTags();
}

// -------------------------------
// Law Firm Input Handling
// -------------------------------
document.getElementById("lawfirmInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    const value = e.target.value.trim();
    if (!value) return;

    lawfirms.push(value);
    e.target.value = "";
    renderLawFirmTags();
  }
});

function renderLawFirmTags() {
  hideError();
  const container = document.getElementById("lawfirmTags");
  container.innerHTML = lawfirms
    .map(
      (name, i) =>
        `<span class="tag">
            ${name}
            <button onclick="removeLawFirm(${i})">×</button>
          </span>`,
    )
    .join("");
}

function removeLawFirm(index) {
  lawfirms.splice(index, 1);
  renderLawFirmTags();
}

// -------------------------------
// Search by Law Firm
// -------------------------------
async function searchByLawFirm() {
  if (lawfirms.length === 0) {
    showError("Please add at least one law firm");
    return;
  }

  const searchType = document.querySelector(
    'input[name="lawfirmType"]:checked',
  )?.value;
  const limit = parseInt(document.getElementById("lawfirmLimit").value) || 10;

  try {
    const res = await fetch(`${API_URL}/build/lawfirm-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lawfirms, search_type: searchType, limit }),
    });

    if (!res.ok) throw new Error("Failed to build law firm query");

    const data = await res.json();
    displayUrl(data.solr_query_url);
  } catch (error) {
    console.error(error);
    alert(error.message);
    showError(error.message);
  }
}

// -------------------------------
// Search by Patent ID
// -------------------------------
let patentIds = [];

// Add patent ID on Enter
document.getElementById("patentInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    const value = e.target.value.trim();
    if (!value) return;

    patentIds.push(value);
    e.target.value = "";
    renderPatentTags();
  }
});

function renderPatentTags() {
  hideError();
  const container = document.getElementById("patentTags");
  container.innerHTML = patentIds
    .map(
      (id, i) =>
        `<span class="tag">
          ${id}
          <button onclick="removePatentId(${i})">×</button>
        </span>`,
    )
    .join("");
}

function removePatentId(index) {
  patentIds.splice(index, 1);
  renderPatentTags();
}

// Build and display Solr query for multiple IDs
async function searchByPatent() {
  hideError();
  if (patentIds.length === 0) {
    showError("Please add at least one Patent ID");
    return;
  }

  try {
    lastQueryType = "patent";
    const res = await fetch(`${API_URL}/build/patent-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patent_ids: patentIds }),
    });

    if (!res.ok) throw new Error("Failed to build patent query");

    const data = await res.json();
    displayUrl(data.solr_query_url);
  } catch (error) {
    console.error(error);
    showError(error.message);
  }
}
// -------------------------------
// Search by Examiner
// -------------------------------
async function searchByExaminer() {
  lastQueryType = "examiner";
  hideError();
  if (examiners.length === 0) {
    showError("Please add at least one examiner");
    return;
  }

  const searchType = document.querySelector(
    'input[name="examinerType"]:checked',
  )?.value;
  const limit = parseInt(document.getElementById("examinerLimit").value) || 10;

  try {
    const res = await fetch(`${API_URL}/build/examiner-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ examiners, search_type: searchType, limit }),
    });

    if (!res.ok) throw new Error("Failed to build examiner query");

    const data = await res.json();
    displayUrl(data.solr_query_url);
  } catch (error) {
    console.error(error);
    alert(error.message);
    showError(error.message);
  }
}

// -------------------------------
// Load Statistics
// -------------------------------
async function loadStatistics() {
  showLoading(true);
  hideError();

  try {
    const response = await fetch(`${API_URL}/stats/total`);
    if (!response.ok) throw new Error("Failed to load statistics");

    const data = await response.json();
    displayStatistics(data);
  } catch (error) {
    console.error(error);
    alert(error.message);
    showError(error.message);
  } finally {
    showLoading(false);
  }
}

function displayStatistics(data) {
  const container = document.getElementById("statsContainer");
  container.style.display = "grid";
  container.innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Total Patents</div>
        <div class="stat-number">${data.total_patents.toLocaleString()}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Issued</div>
        <div class="stat-number">${data.total_approved.toLocaleString()}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Pending</div>
        <div class="stat-number">${data.total_pending.toLocaleString()}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Abandoned</div>
        <div class="stat-number">${data.total_abandoned.toLocaleString()}</div>
      </div>
    `;
}

// -------------------------------
// Display Solr URL
// -------------------------------
function displayUrl(url) {
  hideError();

  const el = document.getElementById("urlText");

  //store encoded URL (for execution)
  el.dataset.rawUrl = url;

  //show decoded URL (for humans)
  el.textContent = decodeURIComponent(url);

  document.getElementById("urlDisplay").classList.add("show");
}

// -------------------------------
// Execute Query
// -------------------------------
async function executeQuery() {
  const url = document.getElementById("urlText").dataset.rawUrl;
  showLoading(true);

  try {
    const res = await fetch(`${API_URL}/execute-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ solr_query_url: url }),
    });

    if (!res.ok) throw new Error("Failed to execute Solr query");
    console.log("hi");
    const data = await res.json();
    currentResults = data;
    displayResults(data);
  } catch (error) {
    console.error(error);
    alert(error.message);
    showError(error.message);
  } finally {
    showLoading(false);
  }
}

function executeQueryManually() {
  const url = document.getElementById("urlText").textContent;
  if (!url) {
    alert("No URL to open");
    return;
  }
  window.open(url, "_blank");
}

// -------------------------------
// Display Results
// -------------------------------
function displayResults(data) {
  // Store context ONLY if exactly one patent result
  // ONLY control context buttons for PATENT search
  const titleEl = document.getElementById("resultsTitle");

  document.getElementById("results").classList.add("show");

  switch (lastQueryType) {
    case "patent":
      titleEl.textContent = "Results – Patent Search";
      break;

    case "examiner":
      titleEl.textContent = patentContext?.examiner
        ? `Results – Examiner: ${patentContext.examiner}`
        : "Results – Examiner Search";
      break;

    case "lawfirm":
      titleEl.textContent = patentContext?.lawfirm
        ? `Results – Law Firm: ${patentContext.lawfirm}`
        : "Results – Law Firm Search";
      break;

    case "attorney":
      titleEl.textContent = "Results – Attorney Search";
      break;

    case "gau":
      titleEl.textContent = "Results – GAU Search";
      break;

    default:
      titleEl.textContent = "Results";
  }

  if (lastQueryType === "patent") {
    if (data.results && data.results.length === 1) {
      const r = data.results[0];

      patentContext = {
        examiner: r.examiner?.trim() || null,
        lawfirm: Array.isArray(r.law_firm) ? r.law_firm[0].trim() : null,
        attorneys: Array.isArray(r.all_attorney_names)
          ? r.all_attorney_names
          : [],
        gaus: Array.isArray(r.gau) ? r.gau : [],
      };

      showPatentContextActions();
    } else {
      patentContext = null;
      hidePatentContextActions();
    }
  }

  const container = document.getElementById("resultsContainer");
  const countElement = document.getElementById("resultCount");
  countElement.textContent = `Total ${data.total_found} result(s)`;

  if (data.results.length === 0) {
    container.innerHTML = "<p>No results found.</p>";
  } else {
    container.innerHTML = data.results
      .map((result, index) => createResultCard(result, index + 1))
      .join("");
  }

  if (lastQueryType === "examiner") {
    const gauCounts = extractGAUCounts(data.results);

    const gauSection = `
    <div class="gau-group">
      <h3 class="gau-groups"> Unique Group Art Unit (GAU)</h3>
      <div class="gau-buttons">
        ${Object.entries(gauCounts)
          .map(
            ([gau, count]) =>
              `<button class="link-btn" onclick="searchByGAU('${gau}')">
        GAU ${gau} <span class="gau-count">(${count})</span>
      </button>`,
          )
          .join("")}
      </div>
    </div>
  `;

    const cardsSection = data.results
      .map((result, index) => createResultCard(result, index + 1))
      .join("");

    container.innerHTML = gauSection + cardsSection;
    return;
  }

  document.getElementById("results").classList.add("show");
}

function createResultCard(result, index) {
  const fields = [
    "id",
    "title",
    "app_date",
    "disposal_type",
    "application_status",
    "first_named_inventor",
    "law_firm",
    "all_attorney_names",
    "examiner",
    "small_entity_indicator",
    "lawfirm",
    "law_firm_address",
    "gau",
    "app_date_year",
  ];

  return `<div class="result-card">
      <h3>Result #${index}</h3>
      ${fields
        .map((field) => {
          if (result[field] === undefined) return "";
          const value = Array.isArray(result[field])
            ? result[field].join(", ")
            : result[field];
          const label = field
            .split("_")
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(" ");
          return `<div class="result-field"><strong>${label}:</strong> ${value}</div>`;
        })
        .join("")}
    </div>`;
}

// -------------------------------
// Download Results
// -------------------------------
async function downloadJSON() {
  if (!currentResults) return showError("No results to download");
  try {
    const response = await fetch(`${API_URL}/download/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentResults),
    });

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "patent_results.json";
    a.click();
  } catch (error) {
    console.error(error);
    alert(error.message);
    showError(error.message);
  }
}

async function downloadExcel() {
  if (!currentResults) return showError("No results to download");
  try {
    const response = await fetch(`${API_URL}/download/excel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentResults),
    });

    if (!response.ok) throw new Error("Failed to convert to Excel");

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "patent_results.xlsx";
    a.click();
  } catch (error) {
    console.error(error);
    alert(error.message);
    showError(error.message);
  }
}

async function exploreContext(type) {
  lastQueryType = type;
  if (!patentContext) {
    showError("No patent context available");
    return;
  }

  if (type === "examiner" && patentContext.examiner) {
    await fetch(`${API_URL}/build/examiner-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        examiners: [patentContext.examiner],
        search_type: "latest_filed",
        limit: 10,
      }),
    })
      .then((res) => res.json())
      .then((data) => displayUrl(data.solr_query_url));
  }

  if (type === "lawfirm" && patentContext.lawfirm) {
    const lawfirm = patentContext.lawfirm?.trim();
    if (!lawfirm) {
      showError("No law firm data available");
      return;
    }
    await fetch(`${API_URL}/build/lawfirm-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lawfirms: [lawfirm.toLowerCase()],
        search_type: "latest_filed",
        limit: 10,
      }),
    })
      .then((res) => res.json())
      .then((data) => displayUrl(data.solr_query_url));
  }

  if (type === "attorney" && patentContext.attorneys.length) {
    await fetch(`${API_URL}/build/attorney-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        attorneys: [patentContext.attorneys[0]],
        search_type: "latest_filed",
        limit: 10,
      }),
    })
      .then((res) => res.json())
      .then((data) => displayUrl(data.solr_query_url));
  }

  if (type === "gau" && patentContext.gaus.length) {
    await fetch(`${API_URL}/build/gau-query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gaus: patentContext.gaus, // first GAU
        limit: 20,
      }),
    })
      .then((res) => res.json())
      .then((data) => displayUrl(data.solr_query_url));
  }
}

// -------------------------------
// Utility Functions
// -------------------------------
function showLoading(show) {
  document.getElementById("loading").classList.toggle("show", show);
}

function showError(message) {
  const errorDiv = document.getElementById("error");
  errorDiv.textContent = message;
  errorDiv.classList.add("show");
}

function hideError() {
  document.getElementById("error").classList.remove("show");
}

function hideResults() {
  document.getElementById("results").classList.remove("show");
}

function hideUrl() {
  document.getElementById("urlDisplay").classList.remove("show");
}

function showPatentContextActions() {
  const section = document.getElementById("contextActions");
  section.style.display = "block";
  document.querySelector("button[onclick*='examiner']").disabled =
    !patentContext.examiner;
  document.querySelector("button[onclick*='lawfirm']").disabled =
    !patentContext.lawfirm;
  document.querySelector("button[onclick*='attorney']").disabled =
    !patentContext.attorneys.length;

  document.querySelector("button[onclick*='gau']").disabled =
    !patentContext.gaus?.length;
}

function hidePatentContextActions() {
  document.getElementById("contextActions").style.display = "none";
}

async function searchByGAU(gau) {
  showLoading(true);

  lastQueryType = "gau";

  const payload = {
    gaus: [gau],
    limit: 20,
  };

  const res = await fetch("http://localhost:8000/build/gau-query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  displayUrl(data.solr_query_url);
  showLoading(false);
}

function extractGAUCounts(results) {
  const gauCountMap = {};

  results.forEach((doc) => {
    if (!Array.isArray(doc.gau)) return;

    doc.gau.forEach((g) => {
      if (!g) return;
      gauCountMap[g] = (gauCountMap[g] || 0) + 1;
    });
  });

  return gauCountMap; // { "3682": 12, "3685": 7, ... }
}

function extractUniqueGAUs(results) {
  return [
    ...new Set(
      results
        .flatMap((doc) => (Array.isArray(doc.gau) ? doc.gau : []))
        .filter(Boolean),
    ),
  ];
}

async function searchExaminerStatsByDate() {
  const fromDate = document.getElementById("fromDate").value;
  const toDate = document.getElementById("toDate").value;
  const limit = document.getElementById("examinerStatsLimit").value;

  hideUrl();

  if (!fromDate || !toDate) {
    alert("Please select both From and To dates");
    return;
  }

  showLoading(true);

  try {
    const res = await fetch(`${API_URL}/stats/examiners-by-date`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        from_date: fromDate,
        to_date: toDate,
        limit: Number(limit),
      }),
    });

    if (!res.ok) throw new Error("Failed to fetch examiner stats");

    const data = await res.json();
    renderExaminerStats(data);
  } catch (err) {
    console.error(err);
    showError(err.message);
  } finally {
    showLoading(false);
  }
}

function renderExaminerStats(data) {
  const container = document.getElementById("resultsContainer");
  const titleEl = document.getElementById("resultsTitle");
  const countEl = document.getElementById("resultCount");

  document.getElementById("results").classList.add("show");

  titleEl.textContent = "Top Examiners (By Date Range)";
  countEl.textContent = `${data.examiners.length} examiner(s)`;

  container.innerHTML = data.examiners
    .map(
      (ex, i) => `
        <div class="result-card">
          <h3>#${i + 1} ${ex.examiner}</h3>

          <div><b>Total Applications:</b> ${ex.application_count}</div>
          <div><b>Unique GAUs:</b> ${ex.unique_gau_count}</div>

          ${
            ex.gaus && ex.gaus.length
              ? `
                <div class="gau-group">
                  <b>GAUs:</b>
                  <div class="gau-scroll">
                    <div class="gau-buttons">
                      ${ex.gaus
                        .map(
                          (g) => `
                            <button
                              class="link-btn"
                              onclick="searchByGAU('${g.gau}')"
                            >
                              GAU ${g.gau}
                              <span class="gau-count">(${g.application_count})</span>
                            </button>
                          `,
                        )
                        .join("")}
                    </div>
                  </div>
                </div>
              `
              : ""
          }
        <div><b>Unique CPCS(Only Top):</b> ${ex.unique_cpc_count}</div>
          ${
            ex.cpcs && ex.cpcs.length
              ? `
            <div class="cpc-group">
              <b>CPC Classifications:</b>
              <div class="gau-scroll">
                <div class="gau-buttons cpc-button">
                  ${ex.cpcs
                    .map(
                      (c) => `
                        <button
                          class="link-btn cpc-btn"
                          disabled
                        >
                          ${c.cpc}
                          <span class="gau-count">(${c.application_count})</span>
                        </button>
                      `,
                    )
                    .join("")}
                </div>
              </div>
            </div>
          `
              : ""
          }
        </div>
      `,
    )
    .join("");

  document.getElementById("downloadButtons").style.display = "none";
}

async function searchStatsByDateRange() {
  const type = document.getElementById("statsType").value;
  const fromDate = document.getElementById("fromDateAll").value;
  const toDate = document.getElementById("toDateAll").value;
  const limit = document.getElementById("allStatsLimit").value || 10;
  const sortOrder = document.getElementById("statsSortOrder").value;

  if (!fromDate || !toDate) {
    showError("Please select both From and To dates");
    return;
  }

  showLoading();

  try {
    const res = await fetch(`${API_URL}/stats/by-date-range`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type,
        from_date: fromDate,
        to_date: toDate,
        limit: Number(limit),
        sort_order: sortOrder,
      }),
    });

    const data = await res.json();

    renderStatsResults(data, type);
  } catch (err) {
    showLoading(false);
    showError("Failed to fetch stats");
  } finally {
    showLoading(false);
  }
}

function renderStatsResults(data, type) {
  const container = document.getElementById("resultsContainer");
  const titleEl = document.getElementById("resultsTitle");
  const countEl = document.getElementById("resultCount");

  document.getElementById("results").classList.add("show");
  container.innerHTML = "";

  // dynamic key: examiners | prosecutors | lawfirms
  const listKey = `${type}s`;
  const results = data[listKey] || [];

  titleEl.textContent = `Top ${type}s (By Date Range)`;
  countEl.textContent = `${results.length} ${type}(s)`;

  results.forEach((item, index) => {
    const gau_count = (container.innerHTML += `
      <div class="result-card">
        <h3>#${index + 1} ${item[type]}</h3>
        <div class="result-field">
        <div><b>Total Applications:</b> ${item.application_count}</div>
          ${
            item.unique_gau_count !== undefined
              ? `<div><b>Unique GAUs:</b> ${item.unique_gau_count}</div>`
              : ""
          }
       
          ${
            item.gaus && item.gaus.length
              ? `
                <div class="gau-group">
                  <b>GAUs:</b>
                  <div class="gau-scroll">
                    <div class="gau-buttons">
                      ${item.gaus
                        .map(
                          (g) => `
                            <button
                              class="link-btn"
                              onclick="searchByGAU('${g.gau}')"
                            >
                              GAU ${g.gau}
                              <span class="gau-count">(${g.application_count})</span>
                            </button>
                          `,
                        )
                        .join("")}
                    </div>
                  </div>
                </div>
              `
              : ""
          }
         
       </div>
      </div>
    `);
  });

  document.getElementById("downloadButtons").style.display = "none";
}
