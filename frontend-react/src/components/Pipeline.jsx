import { useEffect, useRef, useState } from "react";
import { PIPELINE_STEPS, EVENT_TO_STEP } from "../api/client";

export default function Pipeline({ events = [], onComplete, error }) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const [descs, setDescs] = useState(PIPELINE_STEPS.map((s) => s.desc));
  const [done, setDone] = useState(false);
  const timersRef = useRef([]);

  useEffect(() => {
    // Clear any previous timers.
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];

    const eventToStep = EVENT_TO_STEP;
    const seen = new Set();
    const unique = (events || []).filter((e) => {
      if (eventToStep[e.event_type] === undefined) return false;
      if (seen.has(e.event_type)) return false;
      seen.add(e.event_type);
      return true;
    });

    setDescs(PIPELINE_STEPS.map((s) => s.desc));
    setActiveIndex(-1);
    setDone(false);

    if (unique.length === 0) {
      // No steps to show: if we already have a result, finish immediately.
      if (onComplete) {
        const t = setTimeout(() => onComplete(), 120);
        timersRef.current.push(t);
      }
      return;
    }

    let i = 0;
    const advance = () => {
      if (i >= unique.length) {
        setActiveIndex(PIPELINE_STEPS.length);
        setDone(true);
        const t = setTimeout(() => onComplete && onComplete(), 300);
        timersRef.current.push(t);
        return;
      }
      const ev = unique[i];
      const idx = eventToStep[ev.event_type];
      const desc = ev.data?.message || ev.event_type.replace(/_/g, " ").toLowerCase();
      setDescs((prev) => prev.map((d, k) => (k === idx ? desc : d)));
      // Functional update so we never read a stale value.
      setActiveIndex((prev) => Math.max(prev, idx));
      i += 1;
      const t = setTimeout(advance, 500);
      timersRef.current.push(t);
    };

    const t = setTimeout(advance, 300);
    timersRef.current.push(t);

    return () => timersRef.current.forEach(clearTimeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events]);

  return (
    <section className="flex-1 min-w-0 animate-slide-right">
      <div className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden shadow-sm">
        {PIPELINE_STEPS.map((s, index) => {
          const cls =
            error && index === PIPELINE_STEPS.length - 1
              ? "is-error"
              : index < activeIndex
              ? "is-done"
              : index === activeIndex && !done
              ? "is-active"
              : "";
          return (
            <div key={s.id} className={`pipeline-step ${cls}`}>
              <div className="step-dot"></div>
              <div className="flex flex-col gap-0.5">
                <span className="text-sm font-semibold text-gray-900">{s.agent}</span>
                <span className="step-desc text-xs text-gray-400">{descs[index]}</span>
              </div>
              <div className="step-bar"><div className="step-fill"></div></div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
