import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// 注入 API Key
export function setApiKey(key) {
  api.defaults.headers.common["X-API-Key"] = key;
}

export function getApiKey() {
  return api.defaults.headers.common["X-API-Key"] || "";
}

// ── Dashboard ───────────────────────────────────────────────
export async function fetchDashboardSummary() {
  const res = await api.get("/api/v1/dashboard/summary");
  return res.data;
}

export async function fetchDashboardTickets() {
  const res = await api.get("/api/v1/dashboard/tickets");
  return res.data;
}

export async function fetchDashboardConfig() {
  const res = await api.get("/api/v1/dashboard/config");
  return res.data;
}

// ── Chat ────────────────────────────────────────────────────
export async function sendChat(payload) {
  const res = await api.post("/api/v1/chat", payload);
  return res.data;
}

// ── Ingest ──────────────────────────────────────────────────
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/api/v1/ingest/documents", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// ── Feedback ────────────────────────────────────────────────
export async function sendRecommendationFeedback(armIdx, contextVec, reward) {
  const res = await api.post("/api/v1/feedback/recommendation", {
    arm_idx: armIdx,
    context_vec: contextVec,
    reward,
  });
  return res.data;
}

// ── Tenants (Admin) ─────────────────────────────────────────
export async function createTenant(name, domainId = "game_ops") {
  const res = await api.post("/api/v1/tenants/", { name, domain_id: domainId });
  return res.data;
}

export async function listTenants() {
  const res = await api.get("/api/v1/tenants/");
  return res.data;
}

// ── WebSocket ───────────────────────────────────────────────
export function createWebSocket(apiKey) {
  const wsBase = API_BASE.replace("http", "ws");
  return new WebSocket(`${wsBase}/api/v1/ws?token=${apiKey}`);
}

export default api;
