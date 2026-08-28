import { useState } from "react";

const pipeline = [
  { 
    title: "Order Submitted", 
    desc: "You submit a part request with quantity, priority, and delivery location.",
    icon: "📝"
  },
  { 
    title: "Candidate Generation", 
    desc: "The Demand Agent scans all warehouses for stock and queries 3 external suppliers for availability and pricing.",
    icon: "🔍"
  },
  { 
    title: "Distance Calculation", 
    desc: "Your GPS location (or selected city) is geocoded. Great-circle distance to each warehouse is computed and converted to transit time, which adjusts the lead time for each warehouse candidate.",
    icon: "📍"
  },
  { 
    title: "TOPSIS Ranking", 
    desc: "Each candidate is scored on three criteria — cost, lead time (now including distance), and reliability — weighted by your order priority. The TOPSIS algorithm ranks them from best to worst.",
    icon: "📊"
  },
  { 
    title: "AI Explanation", 
    desc: "A Groq-hosted LLM (Qwen 3.8B) generates a plain-English explanation of why the top-ranked option was selected.",
    icon: "💡"
  },
  { 
    title: "Approval & Execution", 
    desc: "You review the recommendation and approve or reject it. Approved orders either deduct warehouse stock or place a supplier order via the mock logistics API.",
    icon: "✅"
  }
];

const weights = [
  { priority: "Critical", cost: "10%", lead: "60%", rel: "30%" },
  { priority: "High", cost: "20%", lead: "50%", rel: "30%" },
  { priority: "Medium", cost: "35%", lead: "35%", rel: "30%" },
  { priority: "Low", cost: "55%", lead: "15%", rel: "30%" }
];

const architectures = [
  { name: "Orchestrator", desc: "Receives orders, coordinates agents", icon: "⚙️" },
  { name: "Demand Agent", desc: "Scans warehouses & suppliers for candidates", icon: "🏭" },
  { name: "Geo Routing", desc: "Computes distances, adjusts lead times", icon: "🗺️" },
  { name: "TOPSIS Ranking", desc: "Multi-criteria decision scoring", icon: "📈" },
  { name: "Decision Agent", desc: "Interprets your instructions and makes the final choice", icon: "🧠" },
  { name: "Explanation Agent", desc: "Generates human-readable reasoning for the choice", icon: "🗣️" }
];

const datasources = [
  { 
    title: "20 Spare Parts", 
    desc: "Across 4 categories: Hydraulics, Electronic, Fasteners, Filters",
    icon: "🔧"
  },
  { 
    title: "15 Warehouses", 
    desc: "Across Indian cities with geocoded coordinates",
    icon: "🏢"
  },
  { 
    title: "300 Inventory Records", 
    desc: "20 parts x 15 warehouses with stock levels",
    icon: "📦"
  },
  { 
    title: "6,000 Sales Transactions", 
    desc: "Historical buyer/seller data for demand signals",
    icon: "💰"
  },
  { 
    title: "3 Mock Suppliers", 
    desc: "Primary, Express, and Alt Region with dynamic pricing",
    icon: "🚚"
  },
  { 
    title: "17 CSV Datasets", 
    desc: "Categories, parts, demand, inventory, orders, evaluations",
    icon: "📄"
  }
];

const techStack = [
  {
    category: "Backend",
    items: [
      "FastAPI (Python)",
      "SQLite (inventory, sales, orders)",
      "Nominatim / OpenStreetMap (geocoding)",
      "Haversine formula (distance calc)",
      "TOPSIS multi-criteria ranking",
      "Groq LLM — Qwen 3.8B (explanations)"
    ]
  },
  {
    category: "Frontend",
    items: [
      "React (Vite)",
      "Tailwind CSS",
      "Browser Geolocation API (GPS)",
      "Component-based pages",
      "localStorage (demo auth)"
    ]
  }
];

function Section({ title, icon, children }) {
  return (
    <section className="mb-10">
      <div className="flex items-center gap-4 mb-6">
        <span className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center text-[1.25rem]">
          {icon}
        </span>
        <h3 className="text-2xl font-bold text-gray-900">{title}</h3>
      </div>
      {children}
    </section>
  );
}

function StatCard({ title, value, icon, color = "brand" }) {
  return (
    <div className="bg-white border border-[#e6e4dd] rounded-2xl p-6 shadow-card hover:shadow-lift transition-all duration-200">
      <div className="flex items-center gap-4 mb-4">
        <div className={`w-10 h-10 rounded-xl bg-${color}-50 flex items-center justify-center`}>
          {icon}
        </div>
        <div>
          <p className="text-[0.95rem] font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 tracking-tight tabular-nums">{value}</p>
        </div>
      </div>
    </div>
  );
}

function PipelineStep({ step, index }) {
  return (
    <div key={index} className="flex items-start gap-5 py-4">
      <div className="flex-shrink-0 w-11 h-11 rounded-xl bg-brand-50 text-white text-[1rem] font-medium flex items-center justify-center">
        {index + 1}
      </div>
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-[1rem]">{step.icon}</span>
          <h4 className="font-semibold text-gray-900">{step.title}</h4>
        </div>
        <p className="text-[0.95rem] text-gray-600 leading-relaxed">{step.desc}</p>
      </div>
    </div>
  );
}

export default function Info() {
  return (
    <div className="flex-1 p-10">
      <div className="max-w-6xl mx-auto space-y-12">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 letter-spacing-tight">
            System Architecture
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            How AutoSCM works under the hood - from order submission to execution
          </p>
        </header>

        {/* Stats Overview */}
        <section className="mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-5">System Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard title="Part Types" value="20" icon="🔧" color="brand" />
            <StatCard title="Warehouses" value="15" icon="🏢" color="brand" />
            <StatCard title="Inventory Records" value="300" icon="📦" color="brand" />
            <StatCard title="Sales History" value="6K+" icon="💰" color="brand" />
          </div>
        </section>

        {/* Architecture */}
        <Section title="System Architecture" icon="🏗️">
          <p className="text-[0.95rem] text-gray-600 leading-relaxed mb-5">
            AutoSCM is an autonomous supply chain orchestration system that uses a 
            multi-agent pipeline to process spare parts fulfillment requests in real-time, 
            ranking options across warehouse inventory and external suppliers.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {architectures.map((arch) => (
              <div key={arch.name} className="bg-white border border-[#e6e4dd] rounded-2xl p-5 shadow-card hover:shadow-lift transition-all duration-200 flex flex-col">
                <div className="flex items-center gap-4 mb-3">
                  <div className={`w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center`}>
                    {arch.icon}
                  </div>
                  <h4 className="font-semibold text-gray-900">{arch.name}</h4>
                </div>
                <p className="text-[0.95rem] text-gray-600 leading-relaxed flex-1">{arch.desc}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* Order Pipeline */}
        <Section title="Order Processing Pipeline" icon="⚡">
          <div className="space-y-5">
            {pipeline.map((step, index) => (
              <PipelineStep step={step} index={index} />
            ))}
          </div>
        </Section>

        {/* Decision Criteria */}
        <Section title="Decision Criteria & Weights" icon="⚖️">
          <p className="text-[0.95rem] text-gray-600 leading-relaxed mb-5">
            Weights dynamically adjust based on order priority - higher priority favors 
            speed and reliability, while lower priority emphasizes cost savings.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-[0.95rem]">
              <thead>
                <tr className="border-b border-[#e6e4dd]">
                  {[ "Priority", "Cost Weight", "Lead Time Weight", "Reliability Weight" ].map((h) => (
                    <th key={h} className="px-5 py-4 text-left text-[0.95rem] font-medium uppercase tracking-wider text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {weights.map((w, index) => (
                  <tr key={index} className={`border-t border-[#e6e4dd] ${index === 0 ? 'border-t-0' : ''}`}>
                    <td className="px-5 py-4 font-medium text-gray-900">{w.priority}</td>
                    <td className="px-5 py-4">{w.cost}</td>
                    <td className="px-5 py-4 font-semibold text-brand-600">{w.lead}</td>
                    <td className="px-5 py-4 font-semibold text-brand-600">{w.rel}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        {/* Tech Stack */}
        <Section title="Technology Stack" icon="💻">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {techStack.map((stack) => (
              <div key={stack.category} className="space-y-5">
                <h3 className="text-2xl font-bold text-gray-900 mb-3">{stack.category}</h3>
                <ul className="space-y-2 text-[0.95rem] text-gray-600">
                  {stack.items.map((item, index) => (
                    <li key={index} className="flex items-start gap-4">
                      <span className="flex-shrink-0 text-[0.85rem]">•</span>
                      <span className="ml-3">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Section>

        {/* Data Sources */}
        <Section title="Data Sources" icon="📊">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {datasources.map((data) => (
              <div key={data.title} className="bg-white border border-[#e6e4dd] rounded-2xl p-5 shadow-card hover:shadow-lift transition-all duration-200">
                <div className="flex items-center gap-4 mb-3">
                  <div className={`w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center`}>
                    {data.icon}
                  </div>
                  <h4 className="font-semibold text-gray-900">{data.title}</h4>
                </div>
                <p className="text-[0.95rem] text-gray-600 leading-relaxed">{data.desc}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* Footer */}
        <footer className="mt-12 pt-8 border-t border-[#e6e4dd] text-center text-[0.95rem] text-gray-500">
          <p>
            Built for the AgentXcelerate Hackathon • 
            <span className="font-semibold">Autonomous Supply Chain Orchestration</span>
          </p>
          <p className="mt-2">
            <span className="text-[0.85rem]">Last updated: {new Date().toLocaleDateString()}</span>
          </p>
        </footer>
      </div>
    </div>
  );
}