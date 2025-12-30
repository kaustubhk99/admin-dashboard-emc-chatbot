// ===============================
// BASIC CONFIG
// ===============================
const API_BASE = "http://localhost:8000";
const token = localStorage.getItem("access_token");

// ===============================
// TAB HANDLING
// ===============================
function showTab(tabId) {
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach(tab => tab.classList.add("hidden"));

  const activeTab = document.getElementById(tabId);
  if (activeTab) {
    activeTab.classList.remove("hidden");
  }
}

// Default tab
document.addEventListener("DOMContentLoaded", () => {
  showTab("dashboard");
});

// ===============================
// LOGOUT
// ===============================
function logout() {
  localStorage.removeItem("access_token");
  alert("Logged out");
  location.reload();
}

// ===============================
// UPLOAD FOLDER
// ===============================
async function uploadPDF() {
  const input = document.getElementById("pdfInput");
  const files = input.files;
  const status = document.getElementById("uploadStatus");

  if (!token) {
    alert("Not authenticated");
    return;
  }

  if (!files || files.length === 0) {
    alert("Please select a folder with PDFs");
    return;
  }

  const formData = new FormData();

  for (const file of files) {
    formData.append("files", file, file.webkitRelativePath);
  }

  status.innerText = "Uploading...";

  try {
    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    if (!res.ok) {
      status.innerText = "Upload failed";
      return;
    }

    const data = await res.json();
    status.innerText = `Upload successful (Job ID: ${data.job_id})`;

  } catch (err) {
    console.error(err);
    status.innerText = "Upload error";
  }
}