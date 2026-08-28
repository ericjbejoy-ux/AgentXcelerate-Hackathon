import { useEffect, useState } from "react";
import { api } from "../api/client";

function StatusBadge({ status }) {
  if (status === "EXECUTED") return <span className="inline-flex px-2 py-0.5 rounded-full bg-green-50 text-green-600 text-[11px] font-semibold">Executed</span>;
  if (status === "REJECTED") return <span className="inline-flex px-2 py-0.5 rounded-full bg-red-50 text-red-500 text-[11px] font-semibold">Rejected</span>;
  return <span className="inline-flex px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 text-[11px] font-semibold">Pending</span>;
}

export default function History() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.orders().then(setOrders).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="flex-1 p-7">
      <div className="bg-white border border-gray-200/80 rounded-2xl p-7 shadow-sm w-full">
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-1.5">Order History</h2>
          <p className="text-sm text-gray-500">Previously submitted fulfillment requests.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-gray-100">
                {["Order ID", "Status", "Approval", "Customer", "Part", "Created"].map((h) => (
                  <th key={h} className="px-3.5 py-2.5 text-left text-[11px] font-bold uppercase tracking-wider text-gray-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {!orders && !error && <tr><td colSpan={6} className="p-4 text-sm text-gray-400">Loading...</td></tr>}
              {error && <tr><td colSpan={6} className="p-4 text-sm text-red-500">{error}</td></tr>}
              {orders && !orders.length && <tr><td colSpan={6} className="p-4 text-sm text-gray-400">No orders yet.</td></tr>}
              {orders?.map((o) => (
                <tr key={o.order_id} className="animate-row-in">
                  <td className="px-3.5 py-2.5"><code>{o.order_id}</code></td>
                  <td className="px-3.5 py-2.5"><StatusBadge status={o.status} /></td>
                  <td className="px-3.5 py-2.5">{o.approval_status || "--"}</td>
                  <td className="px-3.5 py-2.5">{o.customer_id || "--"}</td>
                  <td className="px-3.5 py-2.5">{o.part_id || "--"}</td>
                  <td className="px-3.5 py-2.5 text-gray-500" style={{ fontSize: "0.8rem" }}>
                    {o.created_at ? new Date(o.created_at).toLocaleString() : "--"}
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
