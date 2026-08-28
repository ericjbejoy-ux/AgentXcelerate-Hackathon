import { useMemo, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { api, partCatalog, warehouseCities } from "../api/client";
import Pipeline from "../components/Pipeline";
import Results from "../components/Results";

const inputCls = "input-field";

const fields = [
  { id: "category", validate: (v) => v.trim() !== "", msg: "Select a category." },
  { id: "partName", validate: (v) => v.trim() !== "", msg: "Select a part." },
  { id: "requestedQuantity", validate: (v) => Number.isInteger(Number(v)) && Number(v) > 0, msg: "Must be a positive whole number." },
  { id: "leadTime", validate: (v) => Number.isInteger(Number(v)) && Number(v) > 0, msg: "Must be a positive whole number." },
  { id: "priorityLevel", validate: (v) => ["Low", "Medium", "High", "Critical"].includes(v), msg: "Select a priority." },
];

export default function NewOrder() {
  const { user } = useAuth();
  const [form, setForm] = useState({
    category: "", partName: "", requestedQuantity: "", leadTime: "",
    priorityLevel: "", specialInstructions: "",
  });
  const [errors, setErrors] = useState({});
  const [city, setCity] = useState("");
  const [lat, setLat] = useState(null);
  const [lon, setLon] = useState(null);
  const [gps, setGps] = useState({ text: "Use GPS", status: "", tone: "text-gray-400" });
  const [phase, setPhase] = useState("idle"); // idle | processing | done | error
  const [events, setEvents] = useState([]);
  const [result, setResult] = useState(null);
  const [orderId, setOrderId] = useState(null);

  const parts = useMemo(() => partCatalog[form.category] || [], [form.category]);
  const customerId = user?.customerId || "CUST-GUEST-0001";

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    setErrors((e) => ({ ...e, [field]: "" }));
  }

  function validate() {
    const errs = {};
    let ok = true;
    for (const f of fields) {
      if (f.id === "partName") {
        if (!f.validate(form[f.id])) { errs[f.id] = f.msg; ok = false; }
      } else if (!f.validate(form[f.id])) {
        errs[f.id] = f.msg; ok = false;
      }
    }
    setErrors(errs);
    return ok;
  }

  function acquireGPS() {
    if (!navigator.geolocation) {
      setGps({ text: "Use GPS", status: "GPS not supported — select a city below.", tone: "text-amber-600" });
      return;
    }
    setGps({ text: "Locating...", status: "Requesting location access...", tone: "text-gray-400" });
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude);
        setLon(pos.coords.longitude);
        setCity("");
        setGps({
          text: "GPS Locked",
          status: `Location: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`,
          tone: "text-green-600",
        });
      },
      () => {
        setGps({ text: "Use GPS", status: "GPS unavailable — select your city from the dropdown.", tone: "text-amber-600" });
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
    );
  }

  function selectCity(c) {
    setCity(c);
    if (c) {
      setLat(null); setLon(null);
      setGps({ text: "Use GPS", status: `City selected: ${c}`, tone: "text-green-600" });
    }
  }

  async function submit(e) {
    e.preventDefault();
    if (!validate()) return;
    setPhase("processing");
    setEvents([]);
    setResult(null);

    const payload = {
      customer_id: customerId,
      part_id: parts.find((p) => p.name === form.partName)?.id,
      requested_qty: Number(form.requestedQuantity),
      max_lead_time_days: Number(form.leadTime),
      priority: form.priorityLevel,
      notes: form.specialInstructions.trim() || "None provided",
      latitude: lat,
      longitude: lon,
      user_location_city: city || null,
    };

    try {
      const data = await api.processOrder(payload);
      if (data.status !== "success") throw new Error(data.detail || "Unknown error");
      setOrderId(data.order_id || null);
      setEvents(data.agent_events || []);
      setResult({
        selected: data.selected_option || {},
        candidates: data.all_candidates || [],
        explanation: data.explanation || "",
      });
    } catch (err) {
      setPhase("error");
      setResult(null);
      console.error(err);
    }
  }

  const errorFor = (id) => <span className="text-xs text-red-500 min-h-[1.2em]">{errors[id] || ""}</span>;

  return (
    <div id="orderView" className="flex-1 p-7">
      <div className="flex gap-7 items-start justify-center min-h-[calc(100vh-120px)] max-w-6xl mx-auto">
        {/* Form */}
        <section className="w-full max-w-[560px] bg-white border border-[#e6e4dd] rounded-2xl p-9 shadow-card">
          <div className="mb-8">
            <h2 className="text-2xl font-bold tracking-tight mb-2 text-[#12161f]">Fulfillment Request</h2>
            <p className="text-[0.95rem] text-[#697080] leading-relaxed">Select a category and part. The AI mesh will find the optimal strategy.</p>
          </div>
          <form onSubmit={submit} noValidate>
            <input type="hidden" value={customerId} readOnly />
            <div className="grid grid-cols-2 gap-5">
              <div className="field flex flex-col gap-1.5">
                <label htmlFor="category" className="text-xs font-semibold text-gray-700">Category</label>
                <select id="category" value={form.category}
                  onChange={(e) => { set("category", e.target.value); set("partName", ""); }}
                  className={`input-field ${errors.category ? "input-error" : ""} ${inputCls}`}>
                  <option value="">Select category</option>
                  {Object.keys(partCatalog).map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
                {errorFor("category")}
              </div>
              <div className="field flex flex-col gap-1.5">
                <label htmlFor="partName" className="text-xs font-semibold text-gray-700">Part Name</label>
                <select id="partName" value={form.partName} disabled={!parts.length}
                  onChange={(e) => set("partName", e.target.value)}
                  className={`input-field ${errors.partName ? "input-error" : ""} ${inputCls} disabled:opacity-50 disabled:cursor-not-allowed`}>
                  <option value="">{parts.length ? "Select part name" : "Select category first"}</option>
                  {parts.map((p) => <option key={p.id} value={p.name}>{p.name}</option>)}
                </select>
                {errorFor("partName")}
              </div>
              <div className="field flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-700">Part ID</label>
                <input value={parts.find((p) => p.name === form.partName)?.id || ""} readOnly placeholder="Auto-filled"
                  className="h-11 px-3.5 rounded-lg border-[1.5px] border-gray-200 bg-gray-50 text-gray-400 text-sm cursor-default outline-none" />
              </div>
              <div className="field flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-700">Quantity</label>
                <input type="number" min="1" step="1" placeholder="e.g. 25" value={form.requestedQuantity}
                  onChange={(e) => set("requestedQuantity", e.target.value)}
                  className={`input-field ${errors.requestedQuantity ? "input-error" : ""} ${inputCls}`} />
                {errorFor("requestedQuantity")}
              </div>
              <div className="field flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-700">Max Lead Time <span className="text-gray-400 font-normal">(days)</span></label>
                <input type="number" min="1" step="1" placeholder="e.g. 7" value={form.leadTime}
                  onChange={(e) => set("leadTime", e.target.value)}
                  className={`input-field ${errors.leadTime ? "input-error" : ""} ${inputCls}`} />
                {errorFor("leadTime")}
              </div>
              <div className="field flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-700">Priority</label>
                <select value={form.priorityLevel} onChange={(e) => set("priorityLevel", e.target.value)}
                  className={`input-field ${errors.priorityLevel ? "input-error" : ""} ${inputCls}`}>
                  <option value="">Select priority</option>
                  {["Low", "Medium", "High", "Critical"].map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
                {errorFor("priorityLevel")}
              </div>
              <div className="field col-span-full flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-700">Delivery Location</label>
                <div className="flex gap-2">
                  <button type="button" onClick={acquireGPS}
                    className="h-11 px-4 rounded-lg border-[1.5px] border-gray-200 bg-white text-sm font-medium text-brand-500 hover:bg-brand-50 transition-all duration-200 flex items-center gap-1.5 flex-shrink-0">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/><circle cx="12" cy="12" r="4"/></svg>
                    {gps.text}
                  </button>
                  <select value={city} onChange={(e) => selectCity(e.target.value)} className={`${inputCls} flex-1`}>
                    <option value="">Or select your city</option>
                    {warehouseCities.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <span className={`text-xs min-h-[1.2em] ${gps.tone}`}>{gps.status}</span>
              </div>
              <div className="field col-span-full flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-700">Special Instructions <span className="text-gray-400 font-normal">(optional)</span></label>
                <textarea rows="2" placeholder="Preferences, exclusions, or constraints..." value={form.specialInstructions}
                  onChange={(e) => set("specialInstructions", e.target.value)}
                  className="min-h-[70px] px-3.5 py-2.5 rounded-lg border-[1.5px] border-gray-200 bg-white text-sm font-normal outline-none transition-all duration-200 focus:border-brand-500 focus:ring-[3px] focus:ring-brand-500/10 resize-y" />
              </div>
            </div>
            <div className="mt-6">
              <button type="submit" disabled={phase === "processing"}
                className="w-full h-[52px] rounded-full bg-brand-500 text-white font-semibold text-[0.95rem] flex items-center justify-center gap-2.5 hover:bg-brand-600 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed">
                <span>{phase === "processing" ? "Analyzing..." : "Run AI Analysis"}</span>
                {phase === "processing" && <span className="w-[18px] h-[18px] border-[2.5px] border-white/30 border-t-white rounded-full animate-spin"></span>}
              </button>
            </div>
          </form>
        </section>

        {/* Pipeline / Results */}
        {phase !== "idle" && (
          <div className="flex-1 min-w-0">
            <Pipeline
              events={events}
              error={phase === "error"}
              onComplete={() => { if (result) setPhase("done"); }}
            />
            {result && phase === "done" && (
              <Results
                selected={result.selected}
                candidates={result.candidates}
                explanation={result.explanation}
                orderId={orderId}
                onReplace={(data) => {
                  // Reject returned a new alternative: swap the whole result.
                  if (!data || !data.selected_option) {
                    setResult({ selected: null, candidates: [], explanation: "No feasible alternative remains." });
                    return;
                  }
                  setResult({
                    selected: data.selected_option,
                    candidates: data.all_candidates || [],
                    explanation: data.explanation || "",
                  });
                }}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
