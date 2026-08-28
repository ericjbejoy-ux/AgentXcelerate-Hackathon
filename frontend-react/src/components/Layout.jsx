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
      <header className="sticky top-0 z-40 flex items-center justify-between px-8 py-4 bg-white/90 border-b border-[#e6e4dd] backdrop-blur-md">
        <div className="flex items-center gap-10">
          <button onClick={() => onNavigate("order")} className="flex items-center gap-3 font-bold text-[1.25rem] tracking-tight text-[#12161f]">
            <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/></svg>
            </span>
            AutoSCM
          </button>
          <nav className="flex gap-1.5">
            {NAV_TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => onNavigate(t.key)}
                className={`px-5 py-2.5 rounded-full text-[0.9rem] font-medium transition-all duration-200 ${
                  view === t.key
                    ? "bg-brand-50 text-brand-600 font-semibold shadow-[inset_0_0_0_1px_rgba(13,148,136,0.15)]"
                    : "text-[#697080] hover:bg-[#f4f3ef] hover:text-[#12161f]"
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
          <div className="flex items-center gap-2.5 px-4 py-2 rounded-full border border-[#e6e4dd] bg-white text-sm font-medium text-[#3c4250]">
            <span className="w-8 h-8 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center text-sm font-bold">
              {user?.name?.[0] || "?"}
            </span>
            <span>{user?.name || "Guest"}</span>
          </div>
          <button onClick={logout} title="Logout"
            className="w-10 h-10 rounded-full border border-[#e6e4dd] bg-white flex items-center justify-center text-[#697080] hover:bg-red-50 hover:text-red-500 hover:border-red-200 transition-all duration-150">
            <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      </header>
      <div className="flex-1">{children}</div>
    </main>
  );
}
