import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../api/client";

const NAV_TABS = [
  { key: "order", label: "New Order" },
  { key: "analytics", label: "Analytics" },
  { key: "inventory", label: "Inventory" },
  { key: "history", label: "History" },
  { key: "info", label: "Info" },
];

export default function Layout({ view, onNavigate, children }) {
  const { user, logout } = useAuth();
  const [online, setOnline] = useState(null);

  useEffect(() => {
    let alive = true;
    api.health().then((ok) => { if (alive) setOnline(ok); })
      .catch(() => { if (alive) setOnline(false); });
    return () => { alive = false; };
  }, []);

  return (
    <main className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-40 flex items-center justify-between px-7 py-3 bg-white border-b border-gray-200/80 backdrop-blur-sm">
        <div className="flex items-center gap-8">
          <button onClick={() => onNavigate("order")} className="flex items-center gap-2.5 font-bold text-lg">
            <svg className="text-brand-500" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/></svg>
            AutoSCM
          </button>
          <nav className="flex gap-1">
            {NAV_TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => onNavigate(t.key)}
                className={`px-[18px] py-2 rounded-full text-[0.85rem] font-medium transition-all duration-200 ${
                  view === t.key
                    ? "bg-[#e8edfb] text-[#315cda] font-semibold"
                    : "text-[#6b6b6b] hover:bg-[#fafaf9] hover:text-[#1a1a1a]"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <div className={`status-pill ${online ? "status-pill--online" : "status-pill--offline"}`}>
            <span className="w-2 h-2 rounded-full bg-current animate-pulse"></span>
            <span className="text-xs font-semibold tracking-wide">{online === null ? "CHECKING" : online ? "ONLINE" : "OFFLINE"}</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-gray-200 bg-white text-sm font-medium">
            <span className="w-7 h-7 rounded-full bg-brand-50 text-brand-500 flex items-center justify-center text-xs font-bold">
              {user?.name?.[0] || "?"}
            </span>
            <span>{user?.name || "Guest"}</span>
          </div>
          <button onClick={logout} title="Logout"
            className="w-9 h-9 rounded-full border border-gray-200 bg-white flex items-center justify-center text-gray-400 hover:bg-red-50 hover:text-red-500 hover:border-red-300 transition-all duration-150">
            <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      </header>
      <div className="flex-1">{children}</div>
    </main>
  );
}
