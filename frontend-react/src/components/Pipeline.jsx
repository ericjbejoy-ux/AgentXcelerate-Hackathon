import { useEffect, useState } from "react";
import { PIPELINE_STEPS, EVENT_TO_STEP } from "../api/client";

export default function Pipeline({ events = [], onComplete, error }) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const [descs, setDescs] = useState(PIPELINE_STEPS.map((s) => s.desc));
  const [done, setDone] = useState(false);

  useEffect(() => {
    const eventToStep = EVENT_TO_STEP;
    const keyEvents = events.filter((e) => eventToStep[e.event_type] !== undefined);
    const seen = new Set();
    const unique = keyEvents.filter((e) => {
      if (seen.has(e.event_type)) return false;
      seen.add(e.event_type);
      return true;
    });

    let i = 0;
    const reset = PIPELINE_STEPS.map((s) => s.desc);
    setDescs(reset);
    setActiveIndex(0);
    setDone(false);

    const step = () => {
      if (i >= unique.length) {
        setActiveIndex(PIPELINE_STEPS.length);
        setDone(true);
        setTimeout(() => onComplete && onComplete(), 400);
        return;
      }
      const ev = unique[i];
      const idx = eventToStep[ev.event_type];
      const desc = ev.data?.message || ev.event_type.replace(/_/g, " ").toLowerCase();
      setDescs((prev) => prev.map((d, k) => (k === idx ? desc : d)));
      setActiveIndex(Math.max(activeIndex, idx + 1));
      setTimeout(() => {
        i++;
        setTimeout(step, 200);
      }, 600);
    };
    const t = setTimeout(step, 500);
    return () => clearTimeout(t);
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
