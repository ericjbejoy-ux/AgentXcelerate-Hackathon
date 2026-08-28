import { useEffect, useState } from "react";

const MSG = "Welcome to Autonomous SCM";

export default function WelcomeScreen({ onContinue }) {
  const [text, setText] = useState("Welcome!");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let i = 0;
    const tick = () => {
      if (i < MSG.length) {
        setText(MSG.slice(0, i + 1));
        i++;
        setTimeout(tick, i < 9 ? 95 : 62);
      } else {
        setReady(true);
      }
    };
    const t = setTimeout(tick, 700);
    return () => clearTimeout(t);
  }, []);

  return (
    <section
      className="fixed inset-0 z-50 grid place-items-center px-6"
      style={{
        background: "linear-gradient(135deg, rgba(49,92,218,0.1), transparent 48%), repeating-linear-gradient(135deg, transparent 0 22px, rgba(17,17,17,0.035) 22px 24px), #f4f4f2",
      }}
    >
      <div className="text-center max-w-xl animate-fade-up">
        <span className="inline-flex items-center px-4 py-1.5 rounded-full border border-gray-200 bg-white/90 text-xs font-semibold tracking-widest uppercase text-gray-500 mb-4">
          Autonomous Supply Chain Mesh
        </span>
        <h1 className="text-5xl md:text-7xl font-extrabold text-gray-400 mb-5 min-h-[1.2em]">{text}</h1>
        <p className="text-gray-500 leading-relaxed mb-9">
          AI-powered orchestration for spare parts discovery, optimization, and fulfillment.
        </p>
        {ready && (
          <button type="button" onClick={onContinue}
            className="inline-flex items-center gap-2 px-9 py-3.5 rounded-full bg-brand-500 text-white font-semibold text-base shadow-lg shadow-brand-500/25 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-brand-500/30 transition-all duration-200 animate-fade-up">
            Continue to Login
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M5 12h14m-7-7 7 7-7 7"/></svg>
          </button>
        )}
      </div>
    </section>
  );
}
