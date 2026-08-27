import React, { useState } from 'react';
import axios from 'axios';

export default function App() {
  const [formData, setFormData] = useState({
    order_id: 'ORD-2026-99',
    customer_id: 'CUST-402',
    part_id: 'BRK-7702-X',
    requested_qty: 20,
    max_lead_time_days: 3,
    priority: 'CRITICAL'
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/v1/process-order', formData);
      setResult(res.data);
    } catch (err) {
      alert("Error connecting to FastAPI backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="flex items-center justify-between border-b border-slate-800 pb-5 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-indigo-400">
            📦 Autonomous SCM Multi-Agent Mesh
          </h1>
          <p className="text-slate-400 text-sm">Digital Nexus AI — Decision Engine</p>
        </div>
        <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-semibold rounded-full border border-emerald-500/20">
          Backend Online
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h2 className="text-lg font-semibold text-slate-200 mb-4">Order Parameters</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-400">Order ID</label>
              <input type="text" value={formData.order_id} onChange={e => setFormData({...formData, order_id: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm mt-1 text-slate-100" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">Part SKU</label>
              <input type="text" value={formData.part_id} onChange={e => setFormData({...formData, part_id: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm mt-1 text-slate-100" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-400">Quantity</label>
                <input type="number" value={formData.requested_qty} onChange={e => setFormData({...formData, requested_qty: parseInt(e.target.value)})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm mt-1 text-slate-100" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-400">Max Days</label>
                <input type="number" value={formData.max_lead_time_days} onChange={e => setFormData({...formData, max_lead_time_days: parseInt(e.target.value)})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm mt-1 text-slate-100" />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">Priority Level</label>
              <select value={formData.priority} onChange={e => setFormData({...formData, priority: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm mt-1 text-slate-100">
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
            <button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-500 font-semibold py-2.5 rounded text-sm transition mt-4">
              {loading ? "Agent Mesh Processing..." : "Dispatch to Agent Mesh"}
            </button>
          </form>
        </div>

        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <h2 className="text-lg font-semibold text-slate-200 mb-4">Dynamic Strategy & TOPSIS Output</h2>
          {result ? (
            <div className="space-y-6">
              <div className="p-4 bg-indigo-950/40 border border-indigo-800/50 rounded-lg">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Top Recommendation</span>
                <h3 className="text-xl font-bold mt-1 text-slate-100">{result.selected_option.strategy_name}</h3>
                <p className="text-slate-400 text-sm mt-1">{result.selected_option.source}</p>
              </div>

              <div className="grid grid-cols-4 gap-4">
                <div className="bg-slate-950 p-4 rounded border border-slate-800">
                  <span className="text-xs text-slate-500">Total Cost</span>
                  <p className="text-lg font-bold text-slate-200">${result.selected_option.total_cost}</p>
                </div>
                <div className="bg-slate-950 p-4 rounded border border-slate-800">
                  <span className="text-xs text-slate-500">Lead Time</span>
                  <p className="text-lg font-bold text-slate-200">{result.selected_option.lead_time_days} Days</p>
                </div>
                <div className="bg-slate-950 p-4 rounded border border-slate-800">
                  <span className="text-xs text-slate-500">TOPSIS Score</span>
                  <p className="text-lg font-bold text-emerald-400">{result.selected_option.topsis_score}</p>
                </div>
                <div className="bg-slate-950 p-4 rounded border border-slate-800">
                  <span className="text-xs text-slate-500">Reallocated</span>
                  <p className="text-sm font-bold text-amber-400 truncate">{result.selected_option.reallocated_from_order || "None"}</p>
                </div>
              </div>

              <div className="bg-slate-950 p-4 rounded border border-slate-800">
                <h4 className="text-xs font-semibold text-slate-400 mb-2">Groq LPU Reasoning Output</h4>
                <p className="text-sm text-slate-300 leading-relaxed">{result.explanation}</p>
              </div>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-800 rounded">
              <p className="text-sm">Submit an order request to activate the agent mesh.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}