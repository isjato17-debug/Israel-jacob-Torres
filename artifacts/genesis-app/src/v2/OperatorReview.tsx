import { useEffect, useRef, useState } from "react";
import { ApiError } from "./journey-api";
import { REVIEW_ACTIONS, fetchOperatorHistory, reviewApplication } from "./partner-api";
import type { OperatorApplication, PartnerHistory, PartnerReviewAction } from "./partner-api";
import type { PDict } from "./partner-i18n";

const NEEDS_REF: PartnerReviewAction[] = ["verify", "record_agreement", "record_integration"];
const NEEDS_NOTE: PartnerReviewAction[] = ["request_information", "reject", "suspend"];
const ACTIONS: Record<string, PartnerReviewAction[]> = {
  APPLICATION: ["begin_review", "suspend", "reject"],
  UNDER_REVIEW: ["request_information", "verify", "suspend", "reject"],
  VERIFICATION_REQUIRED: ["request_information", "verify", "suspend", "reject"],
  VERIFIED: ["await_agreement", "suspend", "reject"],
  AGREEMENT_PENDING: ["record_agreement", "approve", "suspend", "reject"],
  APPROVED: ["begin_integration", "suspend", "reject"],
  INTEGRATION_TESTING: ["record_integration", "suspend", "reject"],
  ACTIVE: ["suspend"], SUSPENDED: ["reopen"], REJECTED: ["reopen"],
};

interface Props { t: PDict; app: OperatorApplication; onUpdated: (a: OperatorApplication) => void; onDenied: () => void; onRefresh: () => Promise<boolean> }

export default function OperatorReview({ t, app, onUpdated, onDenied, onRefresh }: Props) {
  const [action, setAction] = useState<PartnerReviewAction>("begin_review");
  const [reference, setReference] = useState("");
  const [note, setNote] = useState("");
  const [ok, setOk] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [stale, setStale] = useState(false);
  const [busy, setBusy] = useState(false);
  const [hist, setHist] = useState<PartnerHistory[] | null>(null);
  const alive = useRef(true);
  const den = useRef(onDenied); den.current = onDenied;
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const d = app.details, r = app.review;
  const available = (ACTIONS[app.status] ?? []).filter((a) =>
    a !== "approve" || (r.valid && !!r.agreement_reference));
  useEffect(() => {
    setAction((ACTIONS[app.status] ?? ["begin_review"])[0]);
    setOk(false); setHist(null);
  }, [app.status, app.version]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy || stale) return;
    if (action === "activate") { setErr(t.activateBlock); return; }
    if (NEEDS_REF.includes(action) && reference.trim().length < 5) { setErr(t.needRef); return; }
    if (NEEDS_NOTE.includes(action) && note.trim().length < 5) { setErr(t.needNote); return; }
    if (!ok) { setErr(t.needConfirm); return; }
    setBusy(true); setErr(""); setMsg("");
    try {
      const u = await reviewApplication(app, action, reference.trim(), note.trim());
      if (!alive.current) return;
      setOk(false); setReference(""); setNote(""); setHist(null); setMsg(t.actionDone); onUpdated(u);
    } catch (x) {
      if (!alive.current) return;
      if (x instanceof ApiError && (x.status === 401 || x.status === 403)) { den.current(); return; }
      if (x instanceof ApiError && x.status === 409) { setStale(true); setErr(t.conflict); } else setErr(x instanceof Error ? x.message : "Error");
    } finally { if (alive.current) setBusy(false); }
  };
  const refresh = async () => {
    setBusy(true); const good = await onRefresh();
    if (!alive.current) return; setBusy(false);
    if (good) { setStale(false); setErr(""); } else setErr(t.refreshFail);
  };
  const loadHist = async () => {
    if (hist) { setHist(null); return; }
    try { const h = await fetchOperatorHistory(app.id); if (alive.current) setHist(h.events); }
    catch (x) { if (x instanceof ApiError && (x.status === 401 || x.status === 403)) den.current(); else if (alive.current) setErr(t.refreshFail); }
  };
  const id = `rv-${app.id}`;
  return (
    <article className="ow-card" data-testid={`operator-app-${app.id}`}>
      <h3>{d.business_name} <span className="ow-help">{t.self}</span></h3>
      <p className="ow-help">{t.cat[d.category]} · {d.contact_name} · {d.contact_email} · {d.coverage.join(", ")}</p>
      <p><b>{t.status}:</b> {app.status} · v{app.version} · {t.verification}: {t[app.verification_status]} · {t.agreement}: {t[app.agreement_status]} · {t.integration}: {t[app.integration_status]}</p>
      {!r.valid && <p className="ow-warn" role="alert">{t.invalid}</p>}
      <details><summary>{t.details}</summary>
        <p><b>{t.services}:</b> {d.services}</p>
        {([ "professional_credentials", "license_information", "api_capabilities", "partnership_interests", "pricing_information"] as const).map((k) => d[k] ? <p key={k}><b>{t[k]}:</b> {d[k]}</p> : null)}
      </details>
      <h4>{t.evidence}</h4><p className="ow-help">{t.evNote}</p>
      {r.evidence.length === 0 ? <p className="ow-help">{t.noEvidence}</p> : <ul>{r.evidence.map((v, i) => <li key={i}><b>{v.kind}</b>: {v.reference}{v.note ? ` - ${v.note}` : ""} ({new Date(v.recorded_at).toLocaleString()})</li>)}</ul>}
      {r.agreement_reference && <p><b>{t.agreementRef}:</b> {r.agreement_reference}</p>}
      {r.integration_reference && <p><b>{t.integrationRef}:</b> {r.integration_reference}</p>}
      <p className="ow-help">{t.intNote}</p>
      {app.review_note && <p><b>{t.note}:</b> {app.review_note}</p>}
      <form onSubmit={submit} noValidate>
        <label htmlFor={`${id}-a`}>{t.action}</label>
        <select id={`${id}-a`} value={action} onChange={(e) => { setAction(e.target.value as PartnerReviewAction); setErr(""); }} data-testid={`operator-action-${app.id}`}>
          {REVIEW_ACTIONS.filter((a) => available.includes(a)).map((a) => <option key={a} value={a}>{t.act[a]}</option>)}
        </select>
        {action === "activate" && <p className="ow-help">{t.activateBlock}</p>}
        <label htmlFor={`${id}-r`}>{t.reference}</label>
        <input id={`${id}-r`} type="text" maxLength={500} value={reference} onChange={(e) => setReference(e.target.value)} />
        <label htmlFor={`${id}-n`}>{t.noteLbl}</label>
        <textarea id={`${id}-n`} maxLength={2000} value={note} onChange={(e) => setNote(e.target.value)} />
        <label className="ow-check"><input type="checkbox" checked={ok} onChange={(e) => setOk(e.target.checked)} /><span>{t.confirm}</span></label>
        <div aria-live="assertive">{err && <p className="ow-err" role="alert">{err}</p>}</div>
        {stale && <div className="ow-row"><button type="button" className="ow-btn sec" disabled={busy} onClick={() => void refresh()}>{t.refresh}</button></div>}
        {msg && <p className="ow-note" role="status">{msg}</p>}
        <div className="ow-row" style={{ marginTop: 12 }}>
          <button type="submit" className="ow-btn" disabled={busy || stale || action === "activate"} data-testid={`operator-apply-${app.id}`}>{busy ? t.saving : t.apply}</button>
          <button type="button" className="ow-btn sec" onClick={() => void loadHist()} aria-expanded={!!hist}>{hist ? t.hide : t.history}</button>
        </div>
      </form>
      {hist && (hist.length === 0 ? <p className="ow-help">{t.noEvents}</p> : <ul>{hist.map((e, i) => <li key={i}><b>{e.action}</b> - {new Date(e.created_at).toLocaleString()} - {e.details?.status} v{e.details?.version}</li>)}</ul>)}
    </article>
  );
}
