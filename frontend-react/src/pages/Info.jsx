const pipeline = [
  { title: "Order Submitted", desc: "You submit a part request with quantity, priority, and delivery location." },
  { title: "Candidate Generation", desc: "The Demand Agent scans all warehouses for stock and queries 3 external suppliers for availability and pricing." },
  { title: "Distance Calculation", desc: "Your GPS location (or selected city) is geocoded. Great-circle distance to each warehouse is computed and converted to transit time, which adjusts the lead time for each warehouse candidate." },
  { title: "TOPSIS Ranking", desc: "Each candidate is scored on three criteria — cost, lead time (now including distance), and reliability — weighted by your order priority. The TOPSIS algorithm ranks them from best to worst." },
  { title: "AI Explanation", desc: "A Groq-hosted LLM (Qwen 3.8B) generates a plain-English explanation of why the top-ranked option was selected." },
  { title: "Approval & Execution", desc: "You review the recommendation and approve or reject it. Approved orders either deduct warehouse stock or place a supplier order via the mock logistics API." },
];

const weights = [
  { priority: "Critical", cost: "10%", lead: "60%", rel: "30%" },
  { priority: "High", cost: "20%", lead: "50%", rel: "30%" },
  { priority: "Medium", cost: "35%", lead: "35%", rel: "30%" },
  { priority: "Low", cost: "55%", lead: "15%", rel: "30%" },
];

const architectures = [
  { name: "Orchestrator", desc: "Receives orders, coordinates agents" },
  { name: "Demand Agent", desc: "Scans warehouses & suppliers for candidates" },
  { name: "Geo Routing", desc: "Computes distances, adjusts lead times" },
  { name: "TOPSIS Ranking", desc: "Multi-criteria decision scoring" },
];

const datasources = [
  { title: "20 Spare Parts", desc: "Across 4 categories: Hydraulics, Electronic, Fasteners, Filters" },
  { title: "15 Warehouses", desc: "Across Indian cities with geocoded coordinates" },
  { title: "300 Inventory Records", desc: "20 parts x 15 warehouses with stock levels" },
  { title: "6,000 Sales Transactions", desc: "Historical buyer/seller data for demand signals" },
  { title: "3 Mock Suppliers", desc: "Primary, Express, and Alt Region with dynamic pricing" },
  { title: "17 CSV Datasets", desc: "Categories, parts, demand, inventory, orders, evaluations" },
];

function Section({ title, children }) {
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-6 shadow-sm">
      <h3 className="text-sm font-bold text-gray-900 mb-3">{title}</h3>
      {children}
    </div>
  );
}

export default function Info() {
  return (
    <div className="flex-1 p-7">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">System Information</h2>
          <p className="text-sm text-gray-500">How AutoSCM works under the hood.</p>
        </div>

        <Section title="Architecture">
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            AutoSCM is an autonomous supply chain orchestration system. It uses a multi-agent pipeline to process spare parts fulfillment requests in real-time, ranking options across warehouse inventory and external suppliers.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {architectures.map((a) => (
              <div key={a.name} className="bg-gray-50 rounded-xl p-3 text-center">
                <div className="text-xs font-bold text-brand-500 mb-1">{a.name}</div>
                <div className="text-[11px] text-gray-500">{a.desc}</div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Order Pipeline">
          <div className="space-y-3">
            {pipeline.map((p, i) => (
              <div key={p.title} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center">{i + 1}</span>
                <div>
                  <div className="text-sm font-semibold text-gray-900">{p.title}</div>
                  <div className="text-xs text-gray-500">{p.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="TOPSIS Criteria & Weights">
          <p className="text-xs text-gray-500 mb-3">Weights change based on order priority. Higher priority orders favor speed; lower priority orders favor cost.</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-100">
                  {["Priority", "Cost Weight", "Lead Time Weight", "Reliability Weight"].map((h) => (
                    <th key={h} className="px-3 py-2 text-left text-[11px] font-bold uppercase tracking-wider text-gray-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {weights.map((w) => (
                  <tr key={w.priority} className="border-b border-gray-50">
                    <td className="px-3 py-2 font-semibold text-gray-900">{w.priority}</td>
                    <td className="px-3 py-2">{w.cost}</td>
                    <td className="px-3 py-2 font-semibold text-brand-500">{w.lead}</td>
                    <td className="px-3 py-2">{w.rel}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section title="Tech Stack">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Backend</div>
              <ul className="space-y-1.5 text-gray-600">
                <li>FastAPI (Python)</li>
                <li>SQLite (inventory, sales, orders)</li>
                <li>Nominatim / OpenStreetMap (geocoding)</li>
                <li>Haversine formula (distance calc)</li>
                <li>TOPSIS multi-criteria ranking</li>
                <li>Groq LLM — Qwen 3.8B (explanations)</li>
              </ul>
            </div>
            <div>
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Frontend</div>
              <ul className="space-y-1.5 text-gray-600">
                <li>React (Vite)</li>
                <li>Tailwind CSS</li>
                <li>Browser Geolocation API (GPS)</li>
                <li>Component-based pages</li>
                <li>localStorage (demo auth)</li>
              </ul>
            </div>
          </div>
        </Section>

        <Section title="Data Sources">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            {datasources.map((d) => (
              <div key={d.title} className="bg-gray-50 rounded-xl p-3">
                <div className="font-semibold text-gray-900">{d.title}</div>
                <div className="text-xs text-gray-500">{d.desc}</div>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </div>
  );
}
