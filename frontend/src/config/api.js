// frontend/src/config/api.js
const isLocalhost = Boolean(
  typeof window !== "undefined" &&
  (window.location.hostname === "localhost" ||
   window.location.hostname === "127.0.0.1" ||
   window.location.hostname === "[::1]" ||
   window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/))
);

const envApiUrl =
  process.env.REACT_APP_API_BASE_URL ||
  process.env.REACT_APP_API_URL ||
  process.env.VITE_API_BASE_URL;

export const API_BASE_URL = envApiUrl
  ? envApiUrl.trim().replace(/\/+$/, "")
  : (isLocalhost ? `http://${(typeof window !== "undefined" && window.location.hostname) || "localhost"}:8000` : "");

export const getCaseFileDownloadUrl = (caseId) => `${API_BASE_URL}/reports/${caseId}/case-file/download`;
export const getSummaryDownloadUrl = (caseId) => `${API_BASE_URL}/reports/${caseId}/summary/download`;
export const generateCaseFile = (caseId) => fetch(`${API_BASE_URL}/api/cases/${caseId}/generate`, { method: "POST" }).then(r => r.json());
