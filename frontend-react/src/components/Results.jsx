import { useState } from "react";
import { api } from "../api/client";

function ScoreBar({ value }) {
  const pct = Math.min((value || 0) * 500, 100);
  return (
    <div className="inline-flex items-center gap-1.5">
      <div className="score-bar"><div className="score-bar__fill" style={{ width: `${pct}%` }}></div></div>
      <span style={{ fontSize: "0.78rem", color: "#999" }}>{(value || 0).toFixed(4)}</span>
    </div>
  );
}

function WinnerCard({ selected, orderId, onDone }) {
  const [status, setStatus] = useState(null);

  async function act(action) {
    if (!orderId) return;
    try {
      const data = await api.approve(orderId, action);
      if (!data.error) {
        setStatus({ kind: action === "APPROVE" ? "success" : "cancelled", msg: data.message || (action === "APPROVE" ? "Order executed successfully." : "Order rejected.") });
      } else {
        setStatus({ kind: "cancelled", msg: `Error: ${data.error}` });
      }
    } catch (e) {
      setStatus({ kind: "cancelled", msg: `Error: ${e.message}` });
    }
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-brand-100 bg-gradient-to-br from-white via-blue-50/30 to-blue-50/60 p-6 animate-fade-up">
      <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-brand-500/5 blur-xl"></div>
      <div className="flex items-center gap-3.5 mb-5">
        <span className="px-3 py-1 rounded-full bg-brand-500 text-white text-[11px] font-bold tracking-wider uppercase">Best Strategy</span>
        <span className="text-3xl font-extrabold text-brand-500 tracking-tight">{(selected.topsis_score || 0).toFixed(4)}</span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <Cell label="Strategy" value={selected.strategy_name || "--"} />
        <Cell label="Source" value={selected.source || selected.warehouse_id || "--"} />
        <Cell label="Lead Time" value={selected.lead_time_days != null ? `${selected.lead_time_days}d` : "--"} />
        <Cell label="Unit Cost" value={selected.unit_cost != null ? `$${selected.unit_cost.toFixed(2)}` : "--"} />
        <Cell label="Total Cost" value={selected.total_cost != null ? `$${selected.total_cost.toFixed(2)}` : "--"} />
        <Cell label="Can Fulfill" value={selected.can_fulfill ? "Yes" : "Partial"} />
      </div>
      {!status && (
        <div className="flex gap-2.5 mt-5">
          <button onClick={() => act("APPROVE")}
            className="h-10 px-5 rounded-full bg-brand-500 text-white text-sm font-semibold flex items-center gap-1.5 hover:bg-brand-600 hover:-translate-y-0.5 hover:shadow-md hover:shadow-brand-500/20 transition-all duration-200">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>
            Approve & Execute
          </button>
          <button onClick={() => act("REJECT")}
            className="h-10 px-5 rounded-full bg-white border border-gray-200 text-gray-500 text-sm font-semibold flex items-center gap-1.5 hover:bg-red-50 hover:text-red-500 hover:border-red-200 transition-all duration-200">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path d="M18 6 6 18m12 0L6 6"/></svg>
            Reject
          </button>
        </div>
      )}
      {status && (
        <div className={`mt-4 px-4 py-2.5 rounded-lg text-sm font-semibold animate-fade-up ${
          status.kind === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"
        }`}>
          {status.msg}
        </div>
      )}
      {onDone && (
        <div className="mt-4">
          <button onClick={onDone} className="text-xs font-semibold text-brand-500 hover:underline">New Order →</button>
        </div>
      )}
    </div>
  );
}

function Cell({ label, value }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">{label}</span>
      <span className="text-sm font-semibold">{value}</span>
    </div>
  );
}

function Explanation({ text }) {
  if (!text) return null;
  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-5 animate-fade-up">
      <h3 className="text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-2">AI Reasoning</h3>
      <p className="text-sm text-gray-600 leading-relaxed">{text}</p>
    </div>
  );
}

function CandidatesTable({ candidates }) {
  if (!candidates?.length) return null;
  const shown = candidates.slice(0, 5);
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden shadow-sm animate-fade-up">
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-gray-100">
        <h3 className="text-[11px] font-bold uppercase tracking-widest text-gray-400">All Candidates</h3>
        <span className="text-xs text-gray-400 font-medium">{candidates.length} total</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-gray-100">
              {["#", "Strategy", "Source", "Cost", "Lead", "Reliability", "Score"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-[11px] font-bold uppercase tracking-wider text-gray-400">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.map((c, i) => (
              <tr key={i} className={`animate-row-in ${i === 0 ? "row--winner" : ""}`}>
                <td className="px-4 py-2.5">{i === 0 ? "🥇" : i + 1}</td>
                <td className="px-4 py-2.5 font-medium">{c.strategy_name || "--"}</td>
                <td className="px-4 py-2.5">{c.source || c.warehouse_id || "--"}</td>
                <td className="px-4 py-2.5">${(c.total_cost || 0).toLocaleString()}</td>
                <td className="px-4 py-2.5">{c.lead_time_days ?? "--"}d</td>
                <td className="px-4 py-2.5">{((c.reliability_score || 0) * 100).toFixed(0)}%</td>
                <td className="px-4 py-2.5"><ScoreBar value={c.topsis_score} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function Results({ selected, candidates, explanation, orderId }) {
  const [key, setKey] = useState(0);
  return (
    <div key={key} className="mt-5 space-y-4">
      <WinnerCard selected={selected} orderId={orderId} onDone={() => setKey((k) => k + 1)} />
      <Explanation text={explanation} />
      <CandidatesTable candidates={candidates} />
    </div>
  );
}
