import { useEffect, useState } from "react";
import { api } from "../api/client";

function ScoreBar({ pct }) {
  return (
    <div className="inline-flex items-center gap-1.5">
      <div className="score-bar"><div className="score-bar__fill" style={{ width: `${Math.min(pct, 100)}%` }}></div></div>
      <span style={{ fontSize: "0.78rem" }}>{pct}%</span>
    </div>
  );
}

export default function Inventory() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.inventory().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="flex-1 p-7">
        <div className="bg-white border border-gray-200/80 rounded-2xl p-7 shadow-sm">
          <p className="text-sm text-red-500">Failed to load: {error}</p>
        </div>
      </div>
    );
  }
  const inv = data?.inventory || [];
  const stats = data?.stats || {};

  return (
    <div className="flex-1 p-7">
      <div className="bg-white border border-gray-200/80 rounded-2xl p-7 shadow-sm w-full">
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-1.5">Live Inventory</h2>
          <p className="text-sm text-gray-500">Real-time warehouse stock across all locations.</p>
        </div>

        <div className="flex gap-4 mb-6 flex-wrap">
          <Stat label="Total SKUs" value={stats.total_skus ?? inv.length} />
          <Stat label="Low Stock" value={stats.low_stock_count ?? 0} warn />
          <Stat label="Critical" value={stats.critical_parts_count ?? 0} crit />
          <Stat label="Value" value={`$${(stats.total_inventory_value_usd ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-gray-100">
                {["SKU", "Description", "Category", "Warehouse", "On Hand", "Reserved", "Available", "Reorder", "Fill %", "Price", "Status"].map((h) => (
                  <th key={h} className="px-3.5 py-2.5 text-left text-[11px] font-bold uppercase tracking-wider text-gray-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {!data && <tr><td colSpan={11} className="p-4 text-sm text-gray-400">Loading inventory...</td></tr>}
              {data && !inv.length && <tr><td colSpan={11} className="p-4 text-sm text-gray-400">No inventory data.</td></tr>}
              {inv.map((item) => (
                <tr key={item.sku + item.warehouse_loc} className={`animate-row-in ${item.needs_reorder ? "row--warn" : ""}`}>
                  <td className="px-3.5 py-2.5"><code style={{ fontSize: "0.8rem" }}>{item.sku}</code></td>
                  <td className="px-3.5 py-2.5">{item.description}</td>
                  <td className="px-3.5 py-2.5">{item.category}</td>
                  <td className="px-3.5 py-2.5">{item.warehouse_loc}</td>
                  <td className="px-3.5 py-2.5">{(item.on_hand_qty ?? 0).toLocaleString()}</td>
                  <td className="px-3.5 py-2.5">{(item.reserved_qty ?? 0).toLocaleString()}</td>
                  <td className="px-3.5 py-2.5 font-semibold">{(item.available_qty ?? 0).toLocaleString()}</td>
                  <td className="px-3.5 py-2.5">{(item.reorder_point ?? 0).toLocaleString()}</td>
                  <td className="px-3.5 py-2.5"><ScoreBar pct={item.stock_pct ?? 0} /></td>
                  <td className="px-3.5 py-2.5">${(item.base_unit_price ?? 0).toFixed(2)}</td>
                  <td className="px-3.5 py-2.5">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold ${item.needs_reorder ? "bg-amber-50 text-amber-600" : "bg-green-50 text-green-600"}`}>
                      {item.needs_reorder ? "Reorder" : "OK"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, warn, crit }) {
  return (
    <div className={`px-4 py-3 rounded-xl border text-center ${crit ? "border-red-200 bg-red-50" : warn ? "border-amber-200 bg-amber-50" : "border-gray-200 bg-gray-50"}`}>
      <div className={`text-2xl font-extrabold ${crit ? "text-red-600" : warn ? "text-amber-600" : "text-gray-900"}`}>{value}</div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">{label}</div>
    </div>
  );
}
