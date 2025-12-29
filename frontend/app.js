const token = localStorage.getItem("access_token");

if (!token) {
  window.location.href = "login.html";
}

function parseJwt(token) {
  const base64Payload = token.split('.')[1];
  const payload = atob(base64Payload);
  return JSON.parse(payload);
}

const user = parseJwt(token);

// Populate profile
document.getElementById("profileEmail").innerText = user.email;
document.getElementById("profileName").innerText = "Admin";
document.getElementById("avatar").innerText =
  user.email.charAt(0).toUpperCase();

const API_BASE = "http://localhost:8000";
let uploadChart;

function showTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden'));
  document.getElementById(tabId).classList.remove('hidden');

  if (tabId === 'dashboard') loadDashboardMetrics();
  if (tabId === 'documents') loadDocuments();
}

async function uploadPDF() {
  const file = document.getElementById("pdfInput").files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  await fetch(`${API_BASE}/upload`, {
    headers: {
    "Authorization": `Bearer ${token}`
    },
    method: "POST",
    body: formData
  });

  loadDashboardMetrics();
}

async function loadDocuments() {
  const res = await fetch(`${API_BASE}/documents`, {
    headers: {
    "Authorization": `Bearer ${token}`
    }});
  const docs = await res.json();

  const table = document.getElementById("pdfTable");
  table.innerHTML = "";

  docs.forEach(d => {
    table.innerHTML += `
      <tr>
        <td>${d.filename}</td>
        <td>${d.status}</td>
        <td>${d.uploaded_at}</td>
        <td>${d.uploaded_by_email}</td>
      </tr>
    `;
  });
}

async function loadDashboardMetrics() {
  const res = await fetch(`${API_BASE}/metrics`,{
    headers: {
    "Authorization": `Bearer ${token}`
    }
  });
  const data = await res.json();

  document.getElementById("totalPdfs").innerText = data.total;
  document.getElementById("processedPdfs").innerText = data.processed;
  document.getElementById("failedPdfs").innerText = data.failed;

  renderChart(data.daily_uploads);
}

function renderChart(dailyData) {
  const ctx = document.getElementById('uploadChart');

  if (uploadChart) uploadChart.destroy();

  uploadChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: dailyData.map(d => d.date),
      datasets: [{
        label: 'PDF Uploads',
        data: dailyData.map(d => d.count)
      }]
    }
  });
}
function logout() {
  // 1. Remove JWT
  localStorage.removeItem("access_token");

  // 2. Redirect to login page
  window.location.href = "login.html";
}



// Default view
showTab('dashboard');
