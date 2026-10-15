import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./journey-api";
import type { ExecutionContext } from "./documents-api";
import * as O from "./orchestrator-api";
import type { OrchestratorView, BusinessAction } from "./orchestrator-api";
import "./orchestrator.css";

const TERMINAL = ["COMPLETED_VERIFIED", "CANCELLED", "CANCELED", "FAILED"];
const OUTCOMES = [["ACCEPTED", "Synthetic test: accepted"], ["REJECTED", "Synthetic test: rejected"], ["CORRECTION_REQUIRED", "Synthetic test: correction required"]];
const DECISIONS = [["REVIEWED", "Reviewed"], ["NOT_APPLICABLE", "Not applicable"], ["NEEDS_PROFESSIONAL_REVIEW", "Needs professional review"]];
const REVIEWED_STATES = DECISIONS.map((d) => d[0]);
const newKey = () => crypto.randomUUID();
const when = (s: string) => { const d = new Date(s); return isNaN(d.getTime()) ? s : d.toLocaleString("en-US"); };
const label = (a: BusinessAction, view: OrchestratorView) => {
  if (a.status === "COMPLETED_VERIFIED" && (a.key === "sign" || a.key === "submit")) return "COMPLETED_VERIFIED (TEST_ONLY)";
  void view; return a.status;
};
const money = (c: number) => "$" + (c / 100).toLocaleString("en-US", { minimumFractionDigits: 2 });

export default function BusinessOrchestrator({ projectId, execution, docDirty = false, onProjectChange }: { projectId: string; execution: ExecutionContext; docDirty?: boolean; onProjectChange?: () => void | Promise<void> }) {
  const [view, setView] = useState<OrchestratorView | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(""); const [kind, setKind] = useState<"" | "401" | "409" | "x">("");
  const [note, setNote] = useState("");
  const [stratOk, setStratOk] = useState(false);
  const [name, setName] = useState(""); const [pw, setPw] = useState("");
  const [reviewed, setReviewed] = useState(false); const [consent, setConsent] = useState(false);
  const [outcome, setOutcome] = useState("ACCEPTED"); const [authOk, setAuthOk] = useState(false);
  const [revoke, setRevoke] = useState<{ id: string; ok: boolean } | null>(null);
  const [cancel, setCancel] = useState<{ key: string; ok: boolean } | null>(null);
  const [rev, setRev] = useState<Record<string, { ok: boolean; d: string }>>({});
  const epoch = useRef(0); const alive = useRef(true);
  const signKey = useRef(newKey()); const authKey = useRef(newKey());
  const wfVersion = execution.workflow?.version ?? 0;

  useEffect(() => { alive.current = true; return () => { alive.current = false; epoch.current++; }; }, []);
  useEffect(() => { setPw(""); setView(null); setLoading(true); setRevoke(null); setCancel(null); }, [projectId]);

  const fail = (e: unknown) => {
    setNote("");
    if (e instanceof ApiError && e.status === 401) { setKind("401"); setErr("Your session has expired. Sign in again; what you typed stays on this page except your password."); }
    else if (e instanceof ApiError && e.status === 409) { setKind("409"); setErr("This changed elsewhere. Reload the latest version, then repeat your action. Nothing was replayed automatically."); }
    else { setKind("x"); setErr(e instanceof Error ? e.message : "Something went wrong."); }
  };
  const load = useCallback(async (quiet = false) => {
    const ep = ++epoch.current; if (!quiet) setLoading(true); setErr(""); setKind("");
    try { const v = await O.loadOrchestrator(projectId); if (ep === epoch.current && alive.current) setView(v); }
    catch (e) { if (ep === epoch.current && alive.current) fail(e); }
    finally { if (ep === epoch.current && alive.current) setLoading(false); }
  }, [projectId]);
  useEffect(() => { void load(); }, [load, wfVersion]);
  useEffect(() => {
    const f = () => { if (document.visibilityState === "visible" && !busy) void load(true); };
    window.addEventListener("focus", f); document.addEventListener("visibilitychange", f);
    return () => { window.removeEventListener("focus", f); document.removeEventListener("visibilitychange", f); };
  }, [load, busy]);

  const mut = async (fn: () => Promise<OrchestratorView>, ok = "Updated.", after?: () => void) => {
    if (busy) return; const ep = ++epoch.current; setBusy(true); setErr(""); setKind(""); setNote("");
    try { const v = await fn(); if (ep !== epoch.current || !alive.current) return; setView(v); setNote(ok); after?.(); await onProjectChange?.(); }
    catch (e) { if (alive.current) fail(e); }
    finally { setPw(""); if (alive.current) setBusy(false); }
  };

  const errBox = err && <div role="alert" data-testid="orchestrator-error"><p className="gx-err">{err}</p>
    {kind !== "401" && <button type="button" className="gx-btn sec" data-testid="orchestrator-reload" onClick={() => void load()}>Reload latest</button>}</div>;
  if (loading && !view) return <section className="gx-card px bo" aria-busy="true"><div className="gx-skel" role="status" aria-label="Loading business orchestrator" /></section>;
  if (!view) return <section className="gx-card px bo" data-testid="business-orchestrator"><h3>Business orchestrator</h3>{errBox}</section>;

  const acts = view.actions, node = (k: string) => acts.find((a) => a.key === k);
  const signN = node("sign"), subN = node("submit"), stratN = node("strategy");
  const wf = execution.workflow, doc = wf?.latest_document ?? null;
  const signReady = !!signN && signN.status === "AWAITING_CUSTOMER_APPROVAL" && !!doc?.approval && wf?.status === "READY_FOR_SIGNATURE" && !docDirty;
  const nameOk = name.trim().length >= 2 && pw.length > 0 && reviewed && consent;
  const doSign = () => {
    if (!signN || !doc || !nameOk) return;
    void mut(() => O.testSign(projectId, { expected_version: signN.version, document_id: doc.id, content_hash: doc.content_hash, typed_name: name.trim(), password: pw, request_key: signKey.current, disclosure_version: view.signing.disclosure_version, reviewed: true, consent: true }),
      "Test signature recorded. This is not a legal executed signature.", () => { signKey.current = newKey(); setName(""); setReviewed(false); setConsent(false); });
  };
  const validSig = doc ? view.signatures.find((s) => !s.revoked && s.integrity_verified && s.document_id === doc.id && s.document_hash === doc.content_hash) : undefined;
  const lastSub = view.submissions[0];
  const subActive = lastSub && validSig && lastSub.signature_id === validSig.id && ["AUTHORIZED", "AWAITING_EXTERNAL_RESULT"].includes(lastSub.status);
  const subOpen = !!subN && ["AWAITING_CUSTOMER_APPROVAL", "FAILED", "CORRECTION_REQUIRED", "CANCELLED"].includes(subN.status) && subN.blocked_by.length === 0;
  const canAuthorize = !!validSig && !!subN && subOpen && !subActive && !docDirty;
  const strat = view.strategy;

  return (
    <section className="gx-card px bo" aria-labelledby="bo-h" data-testid="business-orchestrator">
      <h3 id="bo-h">Business orchestrator</h3>
      <p className="gx-help">Controlled work inside this project. Signing and submission here are test-only simulations: nothing is legally signed, filed with an agency, or paid.</p>
      {errBox}
      <p className="gx-ok" role="status">{note}</p>

      {!view.initialized ? <div>
        <p>The orchestrator has not been started for this project. Starting creates the action list; it does not file or send anything.</p>
        <div className="gx-row"><button type="button" className="gx-btn" disabled={busy} data-testid="orchestrator-start" onClick={() => void mut(() => O.startOrchestrator(projectId), "Orchestrator started.")}>{busy ? "Starting..." : "Start orchestrator"}</button></div>
      </div> : <>
        <p className="gx-help">Scope: {view.scope}</p>

        <h4 style={{ marginTop: 20 }}>Strategy</h4>
        <p>Recommended: <b>{strat.recommended}</b>. Selected: <b>{strat.selected || "none yet"}</b>. <span className="gx-tag">{strat.classification}</span></p>
        <p>{strat.reason}</p>
        {strat.comparisons.map((c) => <details key={c.key} data-testid={`strategy-option-${c.key}`}><summary>{c.name}{c.key === strat.selected ? " (selected)" : ""}{c.key === strat.recommended ? " (recommended)" : ""}</summary>
          <p>Funding gap: {money(c.funding_gap_cents)}</p>
          {([["Advantages", c.advantages], ["Disadvantages", c.disadvantages], ["Assumptions", c.assumptions], ["Risks", c.risks]] as [string, string[]][]).map(([t, l]) => l.length > 0 && <div key={t}><b>{t}</b><ul>{l.map((x, i) => <li key={i}>{x}</li>)}</ul></div>)}</details>)}
        {strat.evidence_gaps.length > 0 && <div><b>Evidence gaps</b><ul data-testid="strategy-gaps">{strat.evidence_gaps.map((x, i) => <li key={i}>{x}</li>)}</ul></div>}
        {strat.mitigation.length > 0 && <div><b>Mitigation</b><ul>{strat.mitigation.map((x, i) => <li key={i}>{x}</li>)}</ul></div>}
        {stratN && !TERMINAL.includes(stratN.status) && <>
          <label className="gx-check"><input type="checkbox" checked={stratOk} onChange={(e) => setStratOk(e.target.checked)} data-testid="strategy-confirm" /><span>I compared the options and confirm the retained selected plan. This does not overwrite my project plan.</span></label>
          <div className="gx-row"><button type="button" className="gx-btn" disabled={busy || !stratOk} data-testid="strategy-accept" onClick={() => void mut(() => O.acceptStrategy(projectId, stratN.version), "Strategy confirmed.", () => setStratOk(false))}>Confirm selected plan</button></div></>}

        <h4 style={{ marginTop: 20 }}>Actions</h4>
        {view.next_actions.length > 0 && <p data-testid="orchestrator-next"><b>Next:</b> {view.next_actions.join("; ")}</p>}
        {acts.map((a) => {
          const cancellable = (a.key === "sign" || a.key === "submit") && !TERMINAL.includes(a.status);
          return <div className="bo-item" key={a.key} data-testid={`action-${a.key}`}>
            <b>{a.title}</b> <span className="gx-badge" data-testid={`action-status-${a.key}`}>{label(a, view)}</span>
            <p className="gx-help">{a.subsystem}. Attempts: {a.attempts}. v{a.version}{a.deadline ? `. Deadline ${a.deadline}` : ""}{a.completed_at ? `. Completed ${when(a.completed_at)}` : ""}</p>
            {a.dependencies.length > 0 && <p className="gx-help">Depends on: {a.dependencies.join(", ")}</p>}
            {a.blocked_by.length > 0 && <p className="gx-warn">Blocked by: {a.blocked_by.join(", ")}</p>}
            {a.evidence.length > 0 && <ul>{a.evidence.map((e, i) => <li key={i}><span className="gx-tag">{e.type}</span>{e.summary} <span className="gx-help">Source: {e.provenance}</span></li>)}</ul>}
            {cancellable && (cancel?.key === a.key ? <div>
              <label className="gx-check"><input type="checkbox" checked={cancel.ok} onChange={(e) => setCancel({ key: a.key, ok: e.target.checked })} data-testid={`cancel-confirm-${a.key}`} /><span>Cancel this test action. Nothing external is affected.</span></label>
              <div className="gx-row"><button type="button" className="gx-btn" disabled={busy || !cancel.ok} data-testid={`cancel-action-${a.key}`} onClick={() => void mut(() => O.cancelBusinessAction(projectId, a.key, a.version), "Action cancelled.", () => setCancel(null))}>Confirm cancel</button>
                <button type="button" className="gx-btn sec" onClick={() => setCancel(null)}>Keep action</button></div></div>
              : <div className="gx-row"><button type="button" className="gx-btn sec" disabled={busy} data-testid={`cancel-start-${a.key}`} onClick={() => setCancel({ key: a.key, ok: false })}>Cancel {a.key} action</button></div>)}
          </div>;
        })}

        <h4 style={{ marginTop: 20 }}>Test signature</h4>
        <p className="gx-warn">A typed test signature is NOT a legal executed signature. Passkeys: {view.signing.passkeys}. Method: {view.signing.method}.</p>
        <details open><summary>Disclosure (version {view.signing.disclosure_version})</summary><div className="bo-disc" data-testid="test-sign-disclosure">{view.signing.disclosure}</div></details>
        {signReady && doc ? <div>
          <p className="gx-help">Document hash <code data-testid="test-sign-hash">{doc.content_hash}</code></p>
          <label className="gx-field" htmlFor="bo-name">Typed full name<input id="bo-name" className="bo-in" type="text" autoComplete="off" value={name} onChange={(e) => setName(e.target.value)} data-testid="test-sign-name" /></label>
          <label className="gx-field" htmlFor="bo-pw">Account password<input id="bo-pw" className="bo-in" type="password" autoComplete="current-password" value={pw} onChange={(e) => setPw(e.target.value)} data-testid="test-sign-password" /></label>
          <label className="gx-check"><input type="checkbox" checked={reviewed} onChange={(e) => setReviewed(e.target.checked)} data-testid="test-sign-reviewed" /><span>I reviewed this exact document and its hash.</span></label>
          <label className="gx-check"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} data-testid="test-sign-consent" /><span>I consent to record a typed TEST signature under the disclosure above.</span></label>
          <div className="gx-row"><button type="button" className="gx-btn" disabled={busy || !nameOk} data-testid="test-sign-submit" onClick={doSign}>{busy ? "Recording..." : "Record test signature"}</button></div>
        </div> : <p className="gx-help" data-testid="test-sign-unavailable">Test signing is available when the sign action awaits your approval, the latest document has your exact approval, and there are no unsaved edits.</p>}

        <h4 style={{ marginTop: 20 }}>Test-signed history</h4>
        {view.signatures.length === 0 ? <p className="gx-help">No test signatures yet.</p> : view.signatures.map((s) => <div className="bo-item" key={s.id} data-testid={`signature-${s.id}`}>
          <b>{s.typed_name}</b> <span className="gx-tag">{s.revoked ? "revoked" : "active"}</span> <span className="gx-tag">{s.integrity_verified ? "hash integrity verified" : "integrity NOT verified"}</span>
          <p className="gx-help">{when(s.created_at)}. Document hash <code>{s.document_hash}</code>. Artifact hash <code>{s.artifact_hash}</code></p>
          <div className="gx-row"><a className="gx-btn sec" href={O.signedDownloadUrl(projectId, s.id)} data-testid={`test-sign-download-${s.id}`}>Download test-signed copy</a>
            {!s.revoked && revoke?.id !== s.id && <button type="button" className="gx-btn sec" disabled={busy} data-testid={`signature-revoke-${s.id}`} onClick={() => setRevoke({ id: s.id, ok: false })}>Revoke</button>}</div>
          {revoke?.id === s.id && <div>
            <label className="gx-check"><input type="checkbox" checked={revoke.ok} onChange={(e) => setRevoke({ id: s.id, ok: e.target.checked })} data-testid={`signature-revoke-confirm-${s.id}`} /><span>Revoke this test signature. History is kept.</span></label>
            <div className="gx-row"><button type="button" className="gx-btn" disabled={busy || !revoke.ok} data-testid={`signature-revoke-go-${s.id}`} onClick={() => void mut(() => O.withdrawTestSignature(projectId, s.id), "Test signature revoked.", () => setRevoke(null))}>Confirm revoke</button>
              <button type="button" className="gx-btn sec" onClick={() => setRevoke(null)}>Keep</button></div></div>}
        </div>)}

        <h4 style={{ marginTop: 20 }}>Synthetic submission test</h4>
        <p className="gx-warn">This is a simulation with a synthetic receipt. No agency receives anything and no agency acceptance is claimed.</p>
        {validSig ? <p className="gx-help">Signature used: {validSig.typed_name}, {when(validSig.created_at)} (latest non-revoked, hash-verified, matches the latest document).</p> : <p className="gx-help">A non-revoked, integrity-verified test signature on the latest document is required.</p>}
        {canAuthorize && validSig && <>
          <label className="gx-field" htmlFor="bo-outcome">Synthetic test scenario<select id="bo-outcome" className="bo-in" value={outcome} onChange={(e) => setOutcome(e.target.value)} data-testid="submission-outcome">{OUTCOMES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
          <label className="gx-check"><input type="checkbox" checked={authOk} onChange={(e) => setAuthOk(e.target.checked)} data-testid="submission-consent" /><span>I authorize this synthetic test submission using the signature above. It sends nothing to any agency.</span></label>
          <div className="gx-row"><button type="button" className="gx-btn" disabled={busy || !authOk} data-testid="submission-authorize" onClick={() => void mut(() => O.authorizeTestSubmission(projectId, subN!.version, validSig.id, outcome, authKey.current), "Test submission authorized.", () => { authKey.current = newKey(); setAuthOk(false); })}>Authorize test submission</button></div></>}
        {subActive && lastSub?.status === "AUTHORIZED" && subN?.status === "AUTHORIZED" && <div className="gx-row"><button type="button" className="gx-btn" disabled={busy} data-testid="submission-dispatch" onClick={() => void mut(() => O.dispatchTestSubmission(projectId, subN.version), "Test dispatch complete.")}>Dispatch test submission</button></div>}
        {subActive && lastSub?.status === "AWAITING_EXTERNAL_RESULT" && subN?.status === "AWAITING_EXTERNAL_RESULT" && <div className="gx-row"><button type="button" className="gx-btn" disabled={busy} data-testid="submission-verify" onClick={() => void mut(() => O.verifyTestSubmission(projectId, subN.version), "Synthetic result verified.")}>Verify synthetic result</button></div>}
        {view.submissions.map((s) => <div className="bo-item" key={s.id} data-testid={`submission-${s.id}`}>
          <span className="gx-badge">{s.status}</span> <span className="gx-tag">SYNTHETIC TEST</span> <span className="gx-tag">Scenario: {s.outcome}</span>
          <p className="gx-help">Package hash <code>{s.package_hash}</code></p>
          {Object.keys(s.result).length > 0 && <dl>{Object.entries(s.result).map(([k, v]) => <div key={k}><dt>{k.replace(/_/g, " ")}</dt><dd>{typeof v === "object" ? JSON.stringify(v) : String(v)}</dd></div>)}</dl>}
        </div>)}

        <h4 style={{ marginTop: 20 }}>Regulatory sources</h4>
        <p className="gx-help">Collects official public sources with fixed queries, only when you ask. No automatic law updates and no deadlines are invented. Independent of the document workflow.</p>
        <div className="gx-row"><button type="button" className="gx-btn" disabled={busy} data-testid="regulatory-collect" onClick={() => void mut(() => O.collectRegulatorySources(projectId), "Collection finished.")}>{busy ? "Working..." : "Collect official sources"}</button></div>
        {view.collection && <div data-testid="regulatory-collection"><p>Collection: <b>{view.collection.status}</b>. New items: {view.collection.added}.</p>
          {view.collection.errors.length > 0 ? <ul className="gx-err">{view.collection.errors.map((x, i) => <li key={i}>{x}</li>)}</ul> : view.collection.added === 0 && <p className="gx-help">No errors and nothing new found.</p>}</div>}
        {view.changes.length === 0 && <p className="gx-help">No regulatory changes recorded.</p>}
        {view.changes.map((c) => {
          const st = rev[c.id] ?? { ok: false, d: "REVIEWED" }; const done = REVIEWED_STATES.includes(c.review_status);
          return <div className="bo-item" key={c.id} data-testid={`change-${c.id}`}>
            <b>{c.title}</b> <span className="gx-tag">{c.change_type}</span> <span className="gx-tag">{c.legal_status}</span>
            <p className="gx-help">Official source: <a href={c.source_url} target="_blank" rel="noopener noreferrer">{c.source_url}</a><br />Checked {when(c.checked_at)}. Effective {c.effective_date ?? "not stated"}. {c.previous_revision_id ? "Revision of an earlier observation." : "First observation."}<br />Hash <code>{c.content_hash}</code></p>
            <p>Review status: <b>{c.review_status}</b></p>
            {typeof c.facts.impact === "string" && <p>{c.facts.impact}</p>}
            {typeof c.facts.excerpt === "string" && <details><summary>Collected official-source excerpt</summary><p>{c.facts.excerpt}</p></details>}
            {!done && <>
              <label className="gx-field" htmlFor={`bo-d-${c.id}`}>Decision<select id={`bo-d-${c.id}`} className="bo-in" value={st.d} onChange={(e) => setRev((r) => ({ ...r, [c.id]: { ...st, d: e.target.value } }))} data-testid={`regulatory-decision-${c.id}`}>{DECISIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
              <label className="gx-check"><input type="checkbox" checked={st.ok} onChange={(e) => setRev((r) => ({ ...r, [c.id]: { ...st, ok: e.target.checked } }))} data-testid={`regulatory-confirm-${c.id}`} /><span>I confirm this decision. It records my review evidence only, not legal certification.</span></label>
              <div className="gx-row"><button type="button" className="gx-btn" disabled={busy || !st.ok} data-testid={`regulatory-review-${c.id}`} onClick={() => void mut(() => O.reviewRegulatoryChange(projectId, c.id, c.version, st.d), "Review recorded; a compliance review task was created if applicable.")}>Record review</button></div></>}
          </div>;
        })}

        <h4 style={{ marginTop: 20 }}>Registry and government workflows</h4>
        <p className="gx-help">Official references only. B.I.G. has not filled, signed, or submitted any of these.</p>
        {view.registry.map((r) => <div className="bo-item" key={r.key} data-testid={`registry-${r.key}`}><b>{r.title}</b> <span className="gx-tag">{r.category}</span> <span className="gx-tag">{r.status}</span>
          {r.source_url && <p className="gx-help"><a href={r.source_url} target="_blank" rel="noopener noreferrer">{r.source_url}</a></p>}</div>)}
        {view.government_workflows.map((g) => <details key={g.key} data-testid={`govflow-${g.key}`}><summary>{g.title} <span className="gx-tag">{g.status}</span></summary>
          <p>Method: {g.method}. Fee: {g.fee}.</p>
          {g.prerequisites.length > 0 && <ul>{g.prerequisites.map((p, i) => <li key={i}>{p}</li>)}</ul>}
          <p className="gx-help">Official reference: <a href={g.source_url} target="_blank" rel="noopener noreferrer">{g.source_url}</a>. Not filled, signed, or submitted by B.I.G.</p></details>)}
      </>}
    </section>
  );
}
