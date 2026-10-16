import { useEffect, useState } from "react";
import { call } from "./journey-api";

interface Proposal {
  id: string; status: string; classification: string; provider: string; model: string;
  proposal_hash: string; context_hash: string; integrity_verified: boolean; error_code: string | null;
  live_reasoning_quality: string; attempts: number; usage: Record<string, unknown>;
  proposal: { summary: string; strategies: { key: string; title: string; reasoning: string }[];
    recommended_strategy: string; tasks: { tool: string; reason: string }[]; risks: string[] } | null;
}
interface History { records: Proposal[]; paid_ai_enabled: false; }

export default function IntelligencePanel({ projectId, onApplied }: { projectId: string; onApplied: () => void }) {
  const [records, setRecords] = useState<Proposal[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const root = `/v2/projects/${projectId}/intelligence`;
  useEffect(() => {
    let live = true;
    setRecords([]); setError("");
    call<History>(root).then((v) => { if (live) setRecords(v.records); })
      .catch((e: unknown) => { if (live) setError(e instanceof Error ? e.message : "Could not load proposal history"); });
    return () => { live = false; };
  }, [root]);
  const act = async (id?: string) => {
    setBusy(true); setError("");
    try {
      const record = await call<Proposal>(id ? `${root}/proposals/${id}/apply` : `${root}/proposals`,
        "POST", id ? {} : { request_key: crypto.randomUUID() });
      setRecords((old) => [record, ...old.filter((r) => r.id !== record.id)].slice(0, 20));
      if (id) onApplied();
    } catch (e) { setError(e instanceof Error ? e.message : "Proposal request failed safely"); }
    finally { setBusy(false); }
  };
  return <section className="bo-item" data-testid="intelligence-panel">
    <h4>Intelligence integration test</h4>
    <p className="gx-help">MOCK / TEST OUTPUT — not genuine AI. Paid AI and external spending are off.
      Live reasoning quality is unverified. Your saved choices and approval gates remain authoritative.</p>
    <button type="button" className="gx-btn sec" disabled={busy} data-testid="intelligence-propose"
      onClick={() => void act()}>{busy ? "Working…" : "Test a structured mock proposal"}</button>
    {error && <p className="gx-warn" role="alert">{error}</p>}
    {records.map((r, index) => <details key={r.id} open={index === 0} data-testid="intelligence-record">
      <summary>Review mock proposal: {r.classification} — {r.status}</summary>
      <p className="gx-help">Provider: {r.provider}; model: {r.model}; attempts: {r.attempts}.
        Integrity: {r.integrity_verified ? "verified" : "not verified"}. Live quality: {r.live_reasoning_quality}.</p>
      <p className="gx-help">Proposal hash: <code>{r.proposal_hash || "No validated output"}</code></p>
      {r.error_code && <p className="gx-warn">{r.error_code}. Existing deterministic tools remain available.</p>}
      {r.proposal && <><p>{r.proposal.summary}</p>
        {r.proposal.strategies.map((s) => <p key={s.key}><b>{s.title}</b>
          {s.key === r.proposal!.recommended_strategy ? " (mock recommendation)" : ""}: {s.reasoning}</p>)}
        <ul>{r.proposal.tasks.map((t) => <li key={t.tool}>{t.tool}: {t.reason}</li>)}</ul>
        <p className="gx-help">Three itemized financial plans are deterministically validated against saved context.
          Applying this proposal does not select a different strategy/plan, approve a document, sign, pay or submit.</p>
        <button type="button" className="gx-btn sec" data-testid="intelligence-apply"
          disabled={busy || r.status !== "VALIDATED" || !r.integrity_verified}
          onClick={() => void act(r.id)}>{r.status === "APPLIED" ? "Applied — saved" : "Apply supported preparation proposals"}</button>
      </>}
    </details>)}
  </section>;
}
