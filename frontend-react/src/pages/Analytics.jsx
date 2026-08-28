import { useEffect, useState } from "react";
import { api } from "../api/client";

function StatCard({ label, value, extra, tone }) {
  const tones = { green: "text-green-600", red: "text-red-500", amber: "text-amber-500", default: "text-brand-600" };
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-5 shadow-sm">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-1.5">{label}</div>
      <div className={`text-3xl font-extrabold ${tones[tone] || tones.default} tracking-tight`}>{value}</div>
      {extra && <div className="text-xs text-gray-400 mt-1">{extra}</div>}
    </div>
  );
}

function Distribution({ data, color }) {
  const entries = Object.entries(data || {});
  if (!entries.length) return <p className="text-sm text-gray-400">No data yet.</p>;
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div className="space-y-3">
      {entries.map(([key, val]) => {
        const pct = Math.round((val / max) * 100);
        return (
          <div key={key}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700 truncate">{key}</span>
              <span className="text-sm font-semibold text-gray-500">{val}</span>
            </div>
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
              <div className="h-full rounded-full transition-all duration-600" style={{ width: `${pct}%`, background: color }}></div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Card({ title, children, scroll }) {
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-6 shadow-sm">
      <h3 className="text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-4">{title}</h3>
      <div className={scroll ? "space-y-3 max-h-[300px] overflow-y-auto" : "space-y-3"}>{children}</div>
    </div>
  );
}

const STATUS_BADGE = {
  EXECUTED: "bg-green-50 text-green-600",
  REJECTED: "bg-red-50 text-red-500",
  PENDING_APPROVAL: "bg-amber-50 text-amber-600",
};

export default function Analytics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.analytics().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="flex-1 p-7">
        <p className="text-sm text-red-500">Failed to load: {error}</p>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex-1 p-7">
        <p className="text-sm text-gray-400">Loading analytics...</p>
      </div>
    );
  }

  const s = data.summary || {};
  const recent = data.recent_orders || [];

  return (
    <div className="flex-1 p-7">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">Analytics Dashboard</h2>
          <p className="text-sm text-gray-500">Real-time insights from your fulfillment operations.</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Orders" value={s.total_orders ?? 0} />
          <StatCard label="Executed" value={s.executed ?? 0} extra={`${s.execution_rate ?? 0}% execution rate`} tone="green" />
          <StatCard label="Pending" value={s.pending ?? 0} tone="amber" />
          <StatCard label="Avg Cost" value={`$${(s.avg_cost ?? 0).toFixed(2)}`} extra={`${s.avg_lead_time ?? 0}d avg lead`} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card title="Orders by Priority"><Distribution data={data.by_priority} color="#315cda" /></Card>
          <Card title="Orders by Category"><Distribution data={data.by_category} color="#7c3aed" /></Card>
          <Card title="Fulfillment Strategy"><Distribution data={data.by_strategy} color="#0891b2" /></Card>
          <Card title="Warehouse Stock Distribution" scroll>
            {Object.entries(data.warehouse_utilization || {}).map(([name, v]) => {
              const onHand = v.on_hand || 0;
              const max = Math.max(...Object.values(data.warehouse_utilization).map((x) => x.on_hand || 0), 1);
              const pct = Math.round((onHand / max) * 100);
              return (
                <div key={name}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-700 truncate">{name}</span>
                    <span className="text-xs text-gray-400">{onHand.toLocaleString()} on hand</span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-600" style={{ width: `${pct}%`, background: "#16a34a" }}></div>
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5">{(v.reserved || 0).toLocaleString()} reserved · {(v.available || 0).toLocaleString()} available</div>
                </div>
              );
            })}
          </Card>
        </div>

        <div className="bg-white border border-gray-200/80 rounded-2xl p-6 shadow-sm">
          <h3 className="text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-4">Recent Orders</h3>
          {!recent.length && <p className="text-sm text-gray-400">No recent orders.</p>}
          {recent.map((o) => (
            <div key={o.order_id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <div className="flex items-center gap-3 min-w-0">
                <code className="text-xs text-gray-500">{o.order_id}</code>
                <span className="text-sm text-gray-700 truncate">{o.part_id || "--"}</span>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="text-[11px] text-gray-400">{o.priority || "--"}</span>
                <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold ${STATUS_BADGE[o.status] || "bg-gray-100 text-gray-500"}`}>
                  {o.status || "--"}
                </span>
                <span className="text-[11px] text-gray-400 hidden md:inline">{o.created_at ? new Date(o.created_at).toLocaleString() : "--"}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
