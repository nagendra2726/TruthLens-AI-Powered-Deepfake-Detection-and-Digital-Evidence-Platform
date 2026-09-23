// frontend/src/config/api.js
const isLocalhost = Boolean(
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "[::1]" ||
  window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/)
);

export const API_BASE_URL =
  process.env.REACT_APP_API_URL ||
  (isLocalhost ? `http://${window.location.hostname || "localhost"}:8000` : "/api");

export const getCaseFileDownloadUrl = (caseId) => `${API_BASE_URL}/reports/${caseId}/case-file/download`;
export const getSummaryDownloadUrl = (caseId) => `${API_BASE_URL}/reports/${caseId}/summary/download`;
export const generateCaseFile = (caseId) => fetch(`${API_BASE_URL}/api/cases/${caseId}/generate`, { method: "POST" }).then(r => r.json());
