import { useMemo, useRef, useState, type ChangeEvent } from "react";
import { Link } from "react-router-dom";
import { TrendChart, type TrendPoint } from "../components/Charts";
import { IconArrow, IconDownload, IconLock, IconUpload } from "../components/Icons";
import { download } from "../lib/exporters";
import { assess } from "../lib/norms";
import { summarize } from "../lib/protocol";
import { buildSampleSession } from "../lib/sampleSession";
import { deleteSession, exportSessionsJson, importSessionsJson, loadSessions, newSessionId, saveSession } from "../lib/storage";
import { formatForce, getStoredUnit, setStoredUnit, type ForceUnit } from "../lib/units";

export default function ResultsPage() {
  const [sessions, setSessions] = useState(loadSessions);
  const [query, setQuery] = useState("");
  const [sourceFilter, setSourceFilter] = useState<"all" | "device" | "simulated">("all");
  const [unit, setUnit] = useState<ForceUnit>(getStoredUnit);
  const [statusMsg, setStatusMsg] = useState<{ kind: "ok" | "bad"; text: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function changeUnit(next: ForceUnit) {
    setUnit(next);
    setStoredUnit(next);
  }

  function remove(id: string) {
    if (!window.confirm("Delete this session from this browser? This cannot be undone.")) return;
    deleteSession(id);
    setSessions(loadSessions());
  }

  function addSample() {
    const sample = { ...buildSampleSession(newSessionId()), created: new Date().toISOString() };
    saveSession(sample);
    setSessions(loadSessions());
    setStatusMsg({ kind: "ok", text: "Added a simulated sample session to this browser." });
  }

  function exportAll() {
    const date = new Date().toISOString().slice(0, 10);
    download(`gripcheck_backup_${date}.json`, exportSessionsJson(), "application/json");
  }

  async function handleImport(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    try {
      const text = await file.text();
      const count = importSessionsJson(text);
      setSessions(loadSessions());
      setStatusMsg({ kind: "ok", text: `Imported ${count} session${count === 1 ? "" : "s"}.` });
    } catch (err) {
      setStatusMsg({ kind: "bad", text: err instanceof Error ? err.message : "Could not read that JSON file." });
    }
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return sessions.filter((s) => {
      if (sourceFilter !== "all" && s.source !== sourceFilter) return false;
      if (!q) return true;
      const hay = `${s.participant.participant_id} ${s.participant.sex} ${s.participant.age} ${s.notes ?? ""}`.toLowerCase();
      return hay.includes(q);
    });
  }, [sessions, query, sourceFilter]);

  const trendPoints = useMemo<TrendPoint[]>(() => {
    const pts: TrendPoint[] = [];
    for (const s of [...filtered].reverse()) {
      try {
        const sum = summarize(s.trials);
        pts.push({
          id: s.id,
          label: new Date(s.created).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
          rightKg: sum.right.metrics.peak_kg,
          leftKg: sum.left.metrics.peak_kg,
          bestKg: sum.overall_peak_kg,
        });
      } catch {
        /* skip damaged entries */
      }
    }
    return pts;
  }, [filtered]);

  return (
    <div className="container">
      <div className="report-head">
        <div>
          <span className="eyebrow">Results</span>
          <h1>Saved sessions</h1>
          <p className="lead" style={{ marginTop: 8 }}>
            Sessions are stored only in this browser. Nothing is uploaded, and clearing the site's data deletes them.
          </p>
        </div>
        <div className="btn-row">
          <div className="pill-tabs" role="group" aria-label="Force display unit">
            {(["kg", "lb"] as ForceUnit[]).map((u) => (
              <button key={u} type="button" className={`pill-tab${unit === u ? " active" : ""}`} onClick={() => changeUnit(u)}>
                {u}
              </button>
            ))}
          </div>
          {sessions.length > 0 && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={exportAll}>
              <IconDownload size={16} /> Export JSON
            </button>
          )}
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => fileRef.current?.click()}>
            <IconUpload size={16} /> Import JSON
          </button>
          <input ref={fileRef} type="file" accept="application/json,.json" hidden onChange={(e) => void handleImport(e)} />
          <Link className="btn btn-primary btn-sm" to="/test">
            New test <IconArrow size={16} />
          </Link>
        </div>
      </div>

      {statusMsg && (
        <div className={`notice ${statusMsg.kind}`} style={{ marginBottom: 16 }}>
          <div>{statusMsg.text}</div>
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="card empty">
          <IconLock size={28} />
          <h2 style={{ fontSize: "1.3rem" }}>No sessions yet</h2>
          <p className="muted">Run a test with the device or simulator, or open the sample report to see how results are analysed.</p>
          <div className="btn-row" style={{ justifyContent: "center" }}>
            <Link className="btn btn-primary" to="/test">
              Start a test <IconArrow />
            </Link>
            <Link className="btn btn-secondary" to="/results/sample-demo">
              View sample report
            </Link>
            <button type="button" className="btn btn-ghost" onClick={addSample}>
              Add sample to history
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 16 }}>
          {trendPoints.length >= 2 && (
            <section className="card box" aria-labelledby="h-trend">
              <div className="box-head">
                <div>
                  <h2 id="h-trend">Progress across sessions</h2>
                  <p className="muted small">Best right and left peak force over time ({trendPoints.length} sessions).</p>
                </div>
                <div className="legend">
                  <span>
                    <i style={{ background: "var(--right)" }} /> Right
                  </span>
                  <span>
                    <i style={{ background: "var(--left)" }} /> Left
                  </span>
                </div>
              </div>
              <TrendChart points={trendPoints} unit={unit} />
            </section>
          )}

          <div className="filter-bar">
            <input
              type="search"
              className="input"
              placeholder="Filter by participant ID, age, sex, or notes…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Filter saved sessions"
            />
            <div className="pill-tabs" role="group" aria-label="Filter by source">
              {(
                [
                  ["all", "All"],
                  ["device", "Device"],
                  ["simulated", "Simulated"],
                ] as const
              ).map(([val, lbl]) => (
                <button
                  key={val}
                  type="button"
                  className={`pill-tab${sourceFilter === val ? " active" : ""}`}
                  onClick={() => setSourceFilter(val)}
                >
                  {lbl}
                </button>
              ))}
            </div>
            <Link className="btn btn-ghost btn-sm" to="/results/sample-demo">
              Sample report
            </Link>
          </div>

          {filtered.length === 0 ? (
            <div className="card empty">
              <p className="muted">No saved sessions match that filter.</p>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  setQuery("");
                  setSourceFilter("all");
                }}
              >
                Clear filters
              </button>
            </div>
          ) : (
            <div className="session-list">
              {filtered.map((s) => {
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
                        {s.notes ? ` · ${s.notes.slice(0, 48)}${s.notes.length > 48 ? "…" : ""}` : ""}
                      </span>
                    </div>
                    <div className="hide-sm">
                      <div className="k">Best grip</div>
                      <div className="v">{Number.isFinite(best) ? `${formatForce(best, unit)} ${unit}` : "–"}</div>
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
      )}
    </div>
  );
}
