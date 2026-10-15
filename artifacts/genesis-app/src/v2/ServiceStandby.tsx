import { useEffect, useState } from "react";
import { checkPublicNotices, loadConnections } from "./documents-api";
import type { ConnectionReadiness, PublicNotices } from "./documents-api";

export default function ServiceStandby({ projectId }: { projectId: string }) {
  const [data, setData] = useState<ConnectionReadiness | null>(null);
  const [result, setResult] = useState<PublicNotices | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let alive = true;
    loadConnections(projectId).then(x => { if (alive) setData(x); }).catch(() => { if (alive) setError("Could not load connection readiness."); });
    return () => { alive = false; };
  }, [projectId]);
  const check = async () => {
    if (busy) return;
    setBusy(true); setError("");
    try { setResult(await checkPublicNotices(projectId)); }
    catch { setError("Public check failed. No service was activated."); }
    finally { setBusy(false); }
  };
  return <details className="px" data-testid="service-standby">
    <summary>External services — standby and no-cost public information</summary>
    <p className="gx-help">Connection setup can be coordinated, but each provider must pass its own checks. Paid services remain inactive. This is not a claim that all adapters are implemented.</p>
    {error && <p role="alert" className="gx-err">{error}</p>}
    {data && <><p>{data.notice}</p><ul>{data.connections.map(x => <li key={x.key}>
      <b>{x.name}</b><p className="gx-help">{x.status} · {x.cost}</p><p>{x.next_dependency}</p>
    </li>)}</ul></>}
    <button type="button" className="gx-btn sec" disabled={busy} onClick={() => void check()} data-testid="public-feed-check">
      {busy ? "Checking official source..." : "Check public Federal Register feed"}
    </button>
    <p className="gx-help">Read-only fixed cleaning query; no customer or project information is sent.</p>
    {result && <div role="status"><b>{result.status}</b><p>{result.notice}</p>
      <small>Checked: {new Date(result.checked_at).toLocaleString()}</small>
      <ul>{result.notices.map(n => <li key={n.document_number}><a href={n.url} target="_blank" rel="noopener noreferrer">{n.title}</a> — {n.publication_date}, {n.document_number}</li>)}</ul>
    </div>}
  </details>;
}
