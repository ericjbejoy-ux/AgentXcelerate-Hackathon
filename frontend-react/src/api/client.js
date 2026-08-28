// API + static data module for AutoSCM React frontend.

export const API_BASE = ""; // proxied to backend by Vite dev server

export const STORAGE_KEYS = { users: "ax_users", currentUser: "ax_current_user" };

export const partCatalog = {
  Hydraulics: [
    { name: "Hydraulic Pump", id: "HYD-1001" },
    { name: "Hydraulic Cylinder", id: "HYD-1002" },
    { name: "Hydraulic Hose", id: "HYD-1003" },
    { name: "Hydraulic Valve", id: "HYD-1004" },
    { name: "Pressure Relief Valve", id: "HYD-1005" },
  ],
  Electronic: [
    { name: "Control Module", id: "ELE-2001" },
    { name: "Electronic Sensor", id: "ELE-2002" },
    { name: "Relay Module", id: "ELE-2003" },
    { name: "Ignition Controller", id: "ELE-2004" },
    { name: "Voltage Regulator", id: "ELE-2005" },
  ],
  Fasteners: [
    { name: "Hex Bolt Set", id: "FAS-3001" },
    { name: "Lock Nut Set", id: "FAS-3002" },
    { name: "Mounting Screw Set", id: "FAS-3003" },
    { name: "Threaded Rod", id: "FAS-3004" },
    { name: "Retaining Ring Set", id: "FAS-3005" },
  ],
  Filters: [
    { name: "Hydraulic Filter", id: "FIL-4001" },
    { name: "Oil Filter", id: "FIL-4002" },
    { name: "Air Filter", id: "FIL-4003" },
    { name: "Fuel Filter", id: "FIL-4004" },
    { name: "Return Line Filter", id: "FIL-4005" },
  ],
};

export const warehouseCities = [
  "Hyderabad", "Kolkata", "Mumbai", "New Delhi", "Chennai", "Pune", "Bengaluru",
  "Jaipur", "Ahmedabad", "Bhubaneswar", "Guwahati", "Lucknow", "Nagpur",
  "Coimbatore", "Indore",
];

export const demoUsers = [
  { role: "Buyer", name: "Arjun Mehta", email: "buyer@demo.com", password: "buyer123", company: "Mumbai Industrial Corp", customerId: "CUST-101" },
  { role: "Seller", name: "Priya Sharma", email: "seller@demo.com", password: "seller123", company: "Hyderabad Parts Supply", customerId: "CUST-SELLER-001" },
];

// ── auth helpers ───────────────────────────────────────────
export function seedUsers() {
  if (!localStorage.getItem(STORAGE_KEYS.users)) {
    localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(demoUsers));
  }
}
export function getUsers() { return JSON.parse(localStorage.getItem(STORAGE_KEYS.users) || "[]"); }
export function saveUsers(u) { localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(u)); }
export function getCurrentUser() { return JSON.parse(localStorage.getItem(STORAGE_KEYS.currentUser) || "null"); }
export function saveCurrentUser(u) { localStorage.setItem(STORAGE_KEYS.currentUser, JSON.stringify(u)); }
export function clearCurrentUser() { localStorage.removeItem(STORAGE_KEYS.currentUser); }

// ── pipeline steps ─────────────────────────────────────────
export const PIPELINE_STEPS = [
  { id: "step-orchestrator", agent: "Orchestrator", desc: "Receiving order..." },
  { id: "step-demand", agent: "DemandAgent", desc: "Scanning warehouses & suppliers..." },
  { id: "step-georoute", agent: "GeoRouting", desc: "Resolving location & computing distances..." },
  { id: "step-ranking", agent: "RankingEngine", desc: "Multi-criteria scoring..." },
  { id: "step-explanation", agent: "ExplanationAgent", desc: "Generating reasoning via LLM..." },
];

export const EVENT_TO_STEP = {
  ORDER_RECEIVED: 0,
  CANDIDATES_GENERATED: 1,
  GEO_ROUTE_COMPLETED: 2,
  TOPSIS_COMPLETED: 3,
  EXPLANATION_GENERATED: 4,
};

// ── API helpers ────────────────────────────────────────────
async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  async health() {
    const res = await fetch(`${API_BASE}/api/v1/health`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  },
  async processOrder(payload) {
    const res = await fetch(`${API_BASE}/api/v1/process-order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handle(res);
  },
  async inventory() {
    return handle(await fetch(`${API_BASE}/api/v1/inventory`));
  },
  async orders() {
    return handle(await fetch(`${API_BASE}/orders`));
  },
  async analytics() {
    return handle(await fetch(`${API_BASE}/api/v1/analytics`));
  },
  async approve(orderId, action, notes = "") {
    const res = await fetch(`${API_BASE}/approve-execution`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: orderId, action, notes }),
    });
    return res.json();
  },
};
