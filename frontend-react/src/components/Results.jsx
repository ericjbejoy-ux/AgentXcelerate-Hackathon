import { useEffect, useRef, useState } from "react";
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

function WinnerCard({ selected, orderId, onReplaced }) {
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState("");
  const [asking, setAsking] = useState(false);
  const lastIdRef = useRef(null);

  // Reset transient status whenever a new candidate is shown.
  useEffect(() => {
    const id = selected?.option_id || selected?.source || selected?.strategy_name || null;
    if (id !== lastIdRef.current) {
      lastIdRef.current = id;
      setStatus(null);
      setBusy(false);
      setAsking(false);
      setReason("");
    }
  }, [selected]);

  async function act(action, rejectReason) {
    if (!orderId || busy) return;
    setBusy(true);
    try {
      const data = await api.approve(orderId, action, rejectReason);
      if (data.error) {
        setStatus({ kind: "cancelled", msg: `Error: ${data.error}` });
      } else if (action === "APPROVE") {
        setStatus({ kind: "success", msg: data.message || "Order executed successfully." });
      } else {
        // REJECT: backend returns the next-best alternative.
        if (data.selected_option && data.status === "PENDING_APPROVAL") {
          setStatus({ kind: "cancelled", msg: data.message || "Rejected. Next best shown." });
          onReplaced && onReplaced(data);
        } else {
          setStatus({ kind: "cancelled", msg: data.message || "Order rejected." });
          onReplaced && onReplaced({ selected: null });
        }
      }
    } catch (e) {
      setStatus({ kind: "cancelled", msg: `Error: ${e.message}` });
    } finally {
      setBusy(false);
    }
  }

  if (!selected) {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-6 text-center text-gray-500">
        No feasible alternative remains.
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-[#d7ece9] bg-gradient-to-br from-white via-brand-50/40 to-brand-50/70 p-7 shadow-card animate-fade-up">
      <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-brand-500/5 blur-xl"></div>
      <div className="flex items-center gap-3.5 mb-5">
        <span className="px-3 py-1 rounded-full bg-brand-500 text-white text-[11px] font-bold tracking-wider uppercase">Best Strategy</span>
        <span className="text-4xl font-extrabold text-brand-600 tracking-tight tabular-nums">{(selected.topsis_score || 0).toFixed(4)}</span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <Cell label="Strategy" value={selected.strategy_name || "--"} />
        <Cell label="Source" value={selected.source || selected.warehouse_id || "--"} />
        <Cell label="Lead Time" value={selected.lead_time_days != null ? `${selected.lead_time_days}d` : "--"} />
        <Cell label="Unit Cost" value={selected.unit_cost != null ? `$${selected.unit_cost.toFixed(2)}` : "--"} />
        <Cell label="Total Cost" value={selected.total_cost != null ? `$${selected.total_cost.toFixed(2)}` : "--"} />
        <Cell label="Can Fulfill" value={selected.can_fulfill ? "Yes" : "Partial"} />
      </div>
      {!status && !asking && (
        <div className="flex gap-2.5 mt-5">
          <button onClick={() => act("APPROVE")} disabled={busy}
            className="h-12 px-6 rounded-full bg-brand-500 text-white text-[0.95rem] font-semibold flex items-center gap-2 hover:bg-brand-600 hover:-translate-y-0.5 hover:shadow-lift transition-all duration-200 disabled:opacity-50">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>
            Approve & Execute
          </button>
          <button onClick={() => setAsking(true)} disabled={busy}
            className="h-12 px-6 rounded-full bg-white border border-[#e6e4dd] text-[#697080] text-[0.95rem] font-semibold flex items-center gap-2 hover:bg-red-50 hover:text-red-500 hover:border-red-200 transition-all duration-200 disabled:opacity-50">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path d="M18 6 6 18m12 0L6 6"/></svg>
            Reject & See Next
          </button>
        </div>
      )}
      {!status && asking && (
        <div className="mt-5 space-y-2.5 animate-fade-up">
          <label className="text-xs font-semibold text-gray-600">Why reject? (used to find a more suitable alternative)</label>
          <textarea
            autoFocus
            rows="2"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. too slow, too expensive, wrong warehouse, reliability too low..."
            className="w-full px-3.5 py-2.5 rounded-lg border-[1.5px] border-gray-200 bg-white text-sm font-normal outline-none transition-all duration-200 focus:border-brand-500 focus:ring-[3px] focus:ring-brand-500/10 resize-y"
          />
          <div className="flex gap-2">
            <button onClick={() => act("REJECT", reason)} disabled={busy}
              className="h-9 px-4 rounded-full bg-red-500 text-white text-sm font-semibold hover:bg-red-600 transition-all duration-200 disabled:opacity-50">
              Confirm Reject
            </button>
            <button onClick={() => { setAsking(false); setReason(""); }}
              className="h-9 px-4 rounded-full bg-white border border-gray-200 text-gray-500 text-sm font-semibold hover:bg-gray-50 transition-all duration-200">
              Cancel
            </button>
          </div>
        </div>
      )}
      {status && (
        <div className={`mt-4 px-4 py-2.5 rounded-lg text-sm font-semibold animate-fade-up ${
          status.kind === "success" ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-600"
        }`}>
          {status.msg}
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
  // Strip the leading [intent] tag for a clean headline.
  const m = text.match(/^\[([^\]]+)\]\s*/);
  const intent = m ? m[1] : null;
  const body = m ? text.slice(m[0].length).trim() : text.trim();
  // Split long run-on sentences into readable lines.
  const clean = body
    .split(/\. (?=[A-Z])/)
    .map((s) => s.trim())
    .filter(Boolean)
    .join(". \n");
  return (
    <div className="rounded-2xl border border-[#e6e4dd] bg-white p-6 shadow-card animate-fade-up">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-[11px] font-bold uppercase tracking-widest text-gray-400">AI Reasoning</h3>
        {intent && (
          <span className="px-2 py-0.5 rounded-full bg-brand-100 text-brand-600 text-[10px] font-bold uppercase tracking-wide">{intent.replace(/_/g, " ")}</span>
        )}
      </div>
      <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{clean}</p>
    </div>
  );
}

function CandidatesTable({ candidates }) {
  if (!candidates?.length) return null;
  const shown = candidates.slice(0, 5);
  return (
    <div className="bg-white border border-[#e6e4dd] rounded-2xl overflow-hidden shadow-card animate-fade-up">
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

export default function Results({ selected, candidates, explanation, orderId, onReplace }) {
  return (
    <div className="mt-5 space-y-4">
      <WinnerCard selected={selected} orderId={orderId} onReplaced={onReplace} />
      <Explanation text={explanation} />
      <CandidatesTable candidates={candidates} />
    </div>
  );
}
