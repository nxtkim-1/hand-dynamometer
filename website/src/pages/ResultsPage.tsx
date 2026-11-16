import { useState } from "react";
import { Link } from "react-router-dom";
import { IconArrow, IconLock } from "../components/Icons";
import { assess } from "../lib/norms";
import { summarize } from "../lib/protocol";
import { deleteSession, loadSessions } from "../lib/storage";

export default function ResultsPage() {
  const [sessions, setSessions] = useState(loadSessions);

  function remove(id: string) {
    if (!window.confirm("Delete this session from this browser? This cannot be undone.")) return;
    deleteSession(id);
    setSessions(loadSessions());
  }

  return (
    <div className="container">
      <div className="page-head">
        <span className="eyebrow">Results</span>
        <h1>Saved sessions</h1>
        <p className="lead" style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
          Sessions are stored only in this browser. Nothing is uploaded, and clearing the site's data deletes them.
        </p>
      </div>

      {sessions.length === 0 ? (
        <div className="card empty">
          <IconLock size={28} />
          <h2 style={{ fontSize: "1.3rem" }}>No sessions yet</h2>
          <p className="muted">Run a test with the device, or with simulated squeezes, and the report will appear here.</p>
          <Link className="btn btn-primary" to="/test">
            Start a test <IconArrow />
          </Link>
        </div>
      ) : (
        <div className="session-list">
          {sessions.map((s) => {
            let best = NaN;
            let pct = NaN;
            try {
              const sum = summarize(s.trials);
              best = sum.overall_peak_kg;
              pct = assess(best, s.participant.age, s.participant.sex).percentile;
            } catch {
              /* a damaged entry still gets listed, so it can be deleted */
            }
            const when = new Date(s.created).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
            return (
              <div key={s.id} className="card session-row">
                <div style={{ display: "grid", gap: 4, minWidth: 0 }}>
                  <Link to={`/results/${s.id}`} style={{ fontWeight: 600, textDecoration: "none" }}>
                    {s.participant.participant_id ? `Participant ${s.participant.participant_id}` : "Grip test"}
                  </Link>
                  <span className="muted small">
                    {when} · {s.participant.sex}, {s.participant.age} y
                  </span>
                </div>
                <div className="hide-sm">
                  <div className="k">Best grip</div>
                  <div className="v">{Number.isFinite(best) ? `${best.toFixed(1)} kg` : "–"}</div>
                </div>
                <div className="hide-md hide-sm">
                  <div className="k">Percentile</div>
                  <div className="v">{Number.isFinite(pct) ? `~${pct.toFixed(0)}` : "–"}</div>
                </div>
                <div className="hide-sm">
                  <span className={`tag ${s.source === "device" ? "accent" : ""}`}>{s.source === "device" ? "Device" : "Simulated"}</span>
                </div>
                <div className="btn-row" style={{ justifyContent: "flex-end" }}>
                  <Link className="btn btn-secondary btn-sm" to={`/results/${s.id}`}>
                    Open
                  </Link>
                  <button className="btn btn-danger btn-sm" onClick={() => remove(s.id)} aria-label={`Delete session from ${when}`}>
                    Delete
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
