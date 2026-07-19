// Auth guard
const TOKEN_KEY = "gt_token";
const token = localStorage.getItem(TOKEN_KEY);
if (!token || token === "null" || token === "undefined") {
  window.location.replace("/login");
}
const authHeaders = { "Authorization": "Bearer " + token };
const jsonAuthHeaders = { "Content-Type": "application/json", "Authorization": "Bearer " + token };

// State
let allGuests = [];
let currentRange = "today";
let barChartInstance = null;
let donutChartInstance = null;
let reportLineChartInstance = null;

// Clock
function updateClock() {
  const el = document.getElementById("clock");
  if (el) el.textContent = new Date().toLocaleTimeString();
}
updateClock();
setInterval(updateClock, 1000);

// Page navigation
function showPage(name) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById("page-" + name).classList.add("active");
  document.getElementById("nav-" + name).classList.add("active");

  if (name === "reports") {
    loadReports();
  }
}

// Toast
function toast(msg, type = "info") {
  const container = document.getElementById("toastContainer");
  const el = document.createElement("div");
  el.className = "toast " + type;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => {
    el.style.animation = "toastOut 0.3s ease forwards";
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

// API helper
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, options);
    const data = await res.json().catch(() => ({}));
    if (res.status === 401 || res.status === 422) {
      localStorage.removeItem(TOKEN_KEY);
      window.location.replace("/login");
      return null;
    }
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    toast("Network error. Check your connection.", "error");
    return null;
  }
}

// Escape HTML
function esc(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Render table
function renderTable() {
  const query  = (document.getElementById("searchInput").value || "").trim().toLowerCase();
  const filter = document.getElementById("filterStatus").value;
  const tbody  = document.getElementById("guestTableBody");

  let rows = allGuests.filter(g => {
    const matchSearch =
      g.name.toLowerCase().includes(query) ||
      g.room.toLowerCase().includes(query) ||
      g.purpose.toLowerCase().includes(query) ||
      (g.host || "").toLowerCase().includes(query);
    const isActive = g.check_out === null;
    const matchFilter = filter === "all" || (filter === "active" && isActive) || (filter === "out" && !isActive);
    return matchSearch && matchFilter;
  });

  if (rows.length === 0) {
    tbody.innerHTML = `<tr class="placeholder-row"><td colspan="9"><div class="empty-wrap">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
      <span>No guests found</span></div></td></tr>`;
  } else {
    tbody.innerHTML = rows.map(g => {
      const isActive = g.check_out === null;
      return `<tr>
        <td>${g.id}</td>
        <td>${esc(g.name)}</td>
        <td>${esc(g.purpose)}</td>
        <td>${esc(g.room)}</td>
        <td>${esc(g.host || "—")}</td>
        <td>${g.check_in}</td>
        <td>${g.check_out ?? "—"}</td>
        <td>${isActive ? `<span class="badge active">Active</span>` : `<span class="badge out">Checked Out</span>`}</td>
        <td>${isActive ? `<button class="btn-checkout" onclick="checkoutGuest(${g.id}, this)">Check Out</button>` : "—"}</td>
      </tr>`;
    }).join("");
  }

  document.getElementById("tableCount").textContent =
    `Showing ${rows.length} of ${allGuests.length} guest${allGuests.length !== 1 ? "s" : ""}`;
}

// Fetch guests
async function fetchGuests(silent = false) {
  const refreshBtn = document.getElementById("refreshBtn");
  if (!silent && refreshBtn) refreshBtn.classList.add("spinning");

  const result = await apiFetch(`/api/guests?range=${currentRange}`, { headers: authHeaders });
  if (refreshBtn) refreshBtn.classList.remove("spinning");
  if (!result || !result.ok) { toast("Failed to load guests.", "error"); return; }

  allGuests = result.data;
  const total  = allGuests.length;
  const active = allGuests.filter(g => g.check_out === null).length;

  // Also fetch full stats for today count
  const statsResult = await apiFetch("/api/stats", { headers: authHeaders });
  if (statsResult && statsResult.ok) {
    document.getElementById("totalGuests").textContent  = statsResult.data.total;
    document.getElementById("activeGuests").textContent = statsResult.data.active;
    document.getElementById("checkedOut").textContent   = statsResult.data.checked_out;
    document.getElementById("todayGuests").textContent  = statsResult.data.today;
  } else {
    document.getElementById("totalGuests").textContent  = total;
    document.getElementById("activeGuests").textContent = active;
    document.getElementById("checkedOut").textContent   = total - active;
  }

  renderTable();
  loadBarChart();
  loadDonutChart(active, total - active);
}

// Checkout
window.checkoutGuest = async function(id, btn) {
  btn.disabled = true;
  btn.textContent = "…";
  const result = await apiFetch(`/api/checkout/${id}`, { method: "POST", headers: authHeaders });
  if (!result) return;
  if (!result.ok) { toast(result.data.msg || "Checkout failed.", "error"); btn.disabled = false; btn.textContent = "Check Out"; return; }
  toast("Guest checked out successfully.", "success");
  await fetchGuests(true);
};

// Check-in form
document.getElementById("checkinForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("checkinError");
  const sucEl = document.getElementById("checkinSuccess");
  errEl.classList.remove("visible");
  sucEl.classList.remove("visible");

  const name    = document.getElementById("name").value.trim();
  const room    = document.getElementById("room").value.trim();
  const purpose = document.getElementById("purpose").value.trim();
  const host    = document.getElementById("host").value.trim();
  const phone   = document.getElementById("phone").value.trim();
  const id_type = document.getElementById("id_type").value;

  if (!name || !room || !purpose) {
    errEl.textContent = "Name, Room and Purpose are required.";
    errEl.classList.add("visible");
    return;
  }

  const btn = document.getElementById("checkinBtn");
  btn.disabled = true;

  const result = await apiFetch("/api/checkin", {
    method: "POST", headers: jsonAuthHeaders,
    body: JSON.stringify({ name, purpose, room, host, phone, id_type }),
  });

  btn.disabled = false;
  if (!result) return;

  if (!result.ok) {
    errEl.textContent = result.data.msg || "Check-in failed.";
    errEl.classList.add("visible");
    return;
  }

  sucEl.textContent = `${name} checked in successfully!`;
  sucEl.classList.add("visible");
  setTimeout(() => sucEl.classList.remove("visible"), 3500);

  ["name","room","purpose","host","phone"].forEach(id => document.getElementById(id).value = "");
  document.getElementById("id_type").value = "";
  toast(`${name} has been checked in.`, "success");
  await fetchGuests(true);
});

// Date filter buttons
document.querySelectorAll(".df-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".df-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentRange = btn.dataset.range;
    fetchGuests(true);
  });
});

// Search & filter
document.getElementById("searchInput").addEventListener("input", renderTable);
document.getElementById("filterStatus").addEventListener("change", renderTable);

// Refresh
document.getElementById("refreshBtn").addEventListener("click", () => fetchGuests(false));

// Logout
document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem(TOKEN_KEY);
  window.location.replace("/login");
});

// Export CSV
function doExport(range) {
  const url = `/api/export/csv?range=${range}`;
  const a = document.createElement("a");
  a.href = url;
  a.setAttribute("download", "guests.csv");

  // Need auth — use fetch then blob
  fetch(url, { headers: authHeaders })
    .then(res => {
      if (res.status === 401 || res.status === 422) { localStorage.removeItem(TOKEN_KEY); window.location.replace("/login"); return; }
      return res.blob();
    })
    .then(blob => {
      if (!blob) return;
      const url2 = URL.createObjectURL(blob);
      a.href = url2;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url2);
      toast("CSV exported successfully!", "success");
    });
}

document.getElementById("exportBtn").addEventListener("click", () => doExport(currentRange));
document.getElementById("exportBtnReport") && document.getElementById("exportBtnReport").addEventListener("click", () => doExport("all"));
document.getElementById("exportAll") && document.getElementById("exportAll").addEventListener("click", () => doExport("all"));
document.getElementById("exportToday") && document.getElementById("exportToday").addEventListener("click", () => doExport("today"));

// Print
function doPrint() {
  window.print();
  toast("Sent to printer.", "info");
}
document.getElementById("printBtn").addEventListener("click", doPrint);
document.getElementById("printBtnReport") && document.getElementById("printBtnReport").addEventListener("click", doPrint);
document.getElementById("printReport") && document.getElementById("printReport").addEventListener("click", doPrint);

// Bar chart
async function loadBarChart() {
  const result = await apiFetch("/api/chart/weekly", { headers: authHeaders });
  if (!result || !result.ok) return;

  const labels = result.data.map(d => {
    const dt = new Date(d.date + "T00:00:00");
    return dt.toLocaleDateString([], { weekday: "short" });
  });
  const counts = result.data.map(d => d.count);

  const canvas = document.getElementById("barChart");
  if (!canvas) return;

  if (barChartInstance) barChartInstance.destroy();
  barChartInstance = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Check-ins", data: counts, backgroundColor: "rgba(59,130,246,0.65)", borderRadius: 6, borderSkipped: false }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "rgba(240,244,255,0.4)", font: { size: 11 } } },
        y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "rgba(240,244,255,0.4)", font: { size: 11 }, stepSize: 1 }, beginAtZero: true }
      }
    }
  });
}

// Donut chart
function loadDonutChart(active, checkedOut) {
  const canvas = document.getElementById("donutChart");
  if (!canvas) return;

  if (donutChartInstance) donutChartInstance.destroy();
  donutChartInstance = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: ["Active", "Checked Out"],
      datasets: [{ data: [active, checkedOut], backgroundColor: ["#22c55e", "#475569"], borderWidth: 0, hoverOffset: 4 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      cutout: "65%"
    }
  });

  const legend = document.getElementById("donutLegend");
  if (legend) {
    legend.innerHTML = `
      <div class="donut-legend-item"><span class="donut-legend-dot" style="background:#22c55e"></span>Active (${active})</div>
      <div class="donut-legend-item"><span class="donut-legend-dot" style="background:#475569"></span>Checked Out (${checkedOut})</div>
    `;
  }
}

// Reports page
async function loadReports() {
  const statsResult = await apiFetch("/api/stats", { headers: authHeaders });
  if (statsResult && statsResult.ok) {
    const s = statsResult.data;
    document.getElementById("avgStay").textContent      = s.avg_stay;
    document.getElementById("busiestDay").textContent   = s.busiest_day;
    document.getElementById("commonPurpose").textContent = s.common_purpose;
    document.getElementById("totalEver").textContent    = s.total;
  }

  const weekResult = await apiFetch("/api/chart/weekly", { headers: authHeaders });
  if (!weekResult || !weekResult.ok) return;

  const labels = weekResult.data.map(d => {
    const dt = new Date(d.date + "T00:00:00");
    return dt.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
  });
  const counts = weekResult.data.map(d => d.count);

  const canvas = document.getElementById("reportLineChart");
  if (!canvas) return;
  if (reportLineChartInstance) reportLineChartInstance.destroy();
  reportLineChartInstance = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Check-ins", data: counts,
        borderColor: "#3b82f6", backgroundColor: "rgba(59,130,246,0.1)",
        fill: true, tension: 0.4, pointBackgroundColor: "#3b82f6", pointRadius: 5
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "rgba(240,244,255,0.4)", font: { size: 11 } } },
        y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "rgba(240,244,255,0.4)", font: { size: 11 }, stepSize: 1 }, beginAtZero: true }
      }
    }
  });
}

// Init
fetchGuests();
setInterval(() => fetchGuests(true), 60000);