import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./journey-api";
import { approveDocument, documentDownloadUrl, generateDocument, loadExecution, saveDocument, savePassport, startDocument } from "./documents-api";
import type { DocumentRecord, ExecutionContext, FormField } from "./documents-api";
import "./execution.css";
import ServiceStandby from "./ServiceStandby";
import BusinessOrchestrator from "./BusinessOrchestrator";

type Draft = Record<string, string>;
const PASS = [["business_name", "Business name"], ["representative_name", "Representative name"], ["business_email", "Business email"], ["municipality", "Municipality"]] as const;
export function centsOf(v: string): number | null {
  const m = /^\$?(\d{1,7})(?:\.(\d{1,2}))?$/.exec(v.trim());
  if (!m) return null;
  const c = Number(m[1]) * 100 + Number((m[2] ?? "").padEnd(2, "0") || "0");
  return c <= 100_000_000 ? c : null;
}
const dollars = (c: number) => { const w = Math.floor(c / 100), r = c % 100; return `${w}.${String(r).padStart(2, "0")}`; };
const toDraft = (ctx: ExecutionContext): Draft => {
  const d: Draft = {};
  for (const f of ctx.template.fields) {
    const v = ctx.workflow?.fields[f.key];
    d[f.key] = v == null ? "" : f.type === "money" && typeof v === "number" ? dollars(v) : String(v);
  }
  return d;
};
const fin = (k: string, v: number | null) => v == null ? "n/a" : /cents/.test(k) ? "$" + (v / 100).toLocaleString("en-US", { minimumFractionDigits: 2 }) : String(v);

export default function ProjectExecution({ projectId, onProjectChange }: { projectId: string; onProjectChange?: () => void | Promise<void> }) {
  const [ctx, setCtx] = useState<ExecutionContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(""); const [kind, setKind] = useState<"" | "401" | "409" | "x">("");
  const [pass, setPass] = useState<Draft>({}); const [consent, setConsent] = useState(false);
  const [draft, setDraft] = useState<Draft>({}); const [dirty, setDirty] = useState(false);
  const [review, setReview] = useState(false); const [busy, setBusy] = useState(false);
  const [fe, setFe] = useState<Record<string, string>>({}); const [note, setNote] = useState("");
  const epoch = useRef(0); const alive = useRef(true);
  const cbRef = useRef(onProjectChange); cbRef.current = onProjectChange;
  useEffect(() => { alive.current = true; return () => { alive.current = false; epoch.current++; }; }, []);

  const adopt = useCallback((c: ExecutionContext, resetDraft = true) => {
    setCtx(c); setPass({ ...c.passport.fields });
    if (resetDraft) { setDraft(toDraft(c)); setDirty(false); }
    setReview(false); setFe({});
  }, []);
  const fail = (e: unknown) => {
    setNote("");
    if (e instanceof ApiError && e.status === 401) { setKind("401"); setErr("Your session has expired. Sign in again; unsaved entries stay on this page."); }
    else if (e instanceof ApiError && e.status === 409) { setKind("409"); setErr("This document changed elsewhere. Reload the latest version, then repeat your action. Nothing was replayed."); }
    else { setKind("x"); setErr(e instanceof Error ? e.message : "Something went wrong."); }
  };
  const load = useCallback(async () => {
    const ep = ++epoch.current; setLoading(true); setErr(""); setKind("");
    try { const c = await loadExecution(projectId); if (ep !== epoch.current || !alive.current) return; adopt(c); }
    catch (e) { if (ep === epoch.current && alive.current) fail(e); }
    finally { if (ep === epoch.current && alive.current) setLoading(false); }
  }, [projectId, adopt]);
  useEffect(() => { void load(); }, [load]);

  const run = async (fn: () => Promise<ExecutionContext>, keepDraft = false, refreshParent = false) => {
    if (busy) return; const ep = epoch.current; setBusy(true); setErr(""); setKind(""); setNote("");
    try {
      const c = await fn(); if (ep !== epoch.current || !alive.current) return;
      adopt(c, !keepDraft); setNote("Saved.");
      if (refreshParent) await cbRef.current?.();
    } catch (e) { if (ep === epoch.current && alive.current) fail(e); }
    finally { if (ep === epoch.current && alive.current) setBusy(false); }
  };

  const errBox = err && <div role="alert" data-testid="execution-error"><p className="gx-err">{err}</p>
    {kind !== "401" && <button type="button" className="gx-btn sec" data-testid="execution-reload" onClick={() => void load()}>Reload latest</button>}</div>;
  if (loading && !ctx) return <section className="gx-card px" aria-busy="true"><div className="gx-skel" role="status" aria-label="Loading" /></section>;
  if (!ctx) return <section className="gx-card px" data-testid="project-execution"><h3>Project execution</h3>{errBox}</section>;

  const wf = ctx.workflow, a = ctx.assistant, doc: DocumentRecord | null = wf?.latest_document ?? null;
  const passMissing = PASS.some(([k]) => k !== "business_email" && !(pass[k] ?? "").trim());
  const savePass = () => {
    const v: Record<string, string> = {};
    if (!consent) v.consent = "Confirm that saving and reuse is authorized.";
    for (const [k, l] of PASS) if (k !== "business_email" && !(pass[k] ?? "").trim()) v[k] = `${l} is required.`;
    setFe(v); if (Object.keys(v).length) return;
    const f: Record<string, string> = {}; for (const [k] of PASS) f[k] = (pass[k] ?? "").trim();
    void run(() => savePassport(projectId, ctx.passport.version, f), true);
  };
  const setF = (f: FormField, v: string) => { setDraft((d) => ({ ...d, [f.key]: v })); setDirty(true); setFe((x) => ({ ...x, [f.key]: "" })); };
  const saveDoc = () => {
    if (!wf) return; const out: Record<string, string | number | null> = {}; const v: Record<string, string> = {};
    for (const f of ctx.template.fields) {
      const s = (draft[f.key] ?? "").trim();
       if (!s) { out[f.key] = f.type === "money" ? null : ""; continue; }
       if (f.type === "money") { const c = centsOf(s); if (c === null || c <= 0) { v[f.key] = "Enter a positive dollar amount up to 1,000,000 with up to two decimals."; continue; } out[f.key] = c; }
      else if (f.max_length && s.length > f.max_length) v[f.key] = `Use at most ${f.max_length} characters.`;
      else out[f.key] = s;
    }
    setFe(v); if (Object.keys(v).length) return;
    void run(() => saveDocument(projectId, wf.version, out), false, false);
  };
  const stage = !ctx.supported ? "" : !wf ? "Save your Business Passport, then start the Cleaning Service Agreement." : dirty ? "Save your corrections." : wf.missing.length ? "Complete the missing fields, then save." : wf.status === "DRAFT" ? "Generate the agreement from your saved fields." : wf.status === "GENERATED" ? "Review the agreement, then confirm approval." : "Approved. Download it; signature blocks are blank for you to sign by hand.";

  return (
    <section className="gx-card px" aria-labelledby="px-h" data-testid="project-execution">
      <h3 id="px-h">Project execution</h3>
      <p className="gx-help">Deterministic checklist logic from your saved project, not AI. Documents are written in English only. Nothing is sent, filed, signed or paid for you.</p>
      {errBox}
      <p className="gx-ok" role="status">{note}</p>
      <div className="px-next" data-testid="execution-next">Next: {a.next_action ? `${a.next_action}. ` : ""}{stage}</div>
      <p style={{ marginTop: 12 }}>{a.summary}</p>
      {a.reasons.length > 0 && <ul>{a.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>}
      {Object.keys(a.financials).length > 0 && <dl>{Object.entries(a.financials).map(([k, v]) => <div key={k}><dt>{k.replace(/_/g, " ")}</dt><dd>{fin(k, v)}</dd></div>)}</dl>}
      <details style={{ marginTop: 12 }}><summary style={{ minHeight: 44, cursor: "pointer" }}>Executive Board positions</summary>
        {Object.entries(a.board.agents).map(([k, v]) => <p key={k}><b>{k}</b>: {v.position}. <span className="gx-help">{v.reason}</span></p>)}</details>
      <details><summary style={{ minHeight: 44, cursor: "pointer" }}>Founder DNA assessment: {a.founder_dna.status}</summary>
        {a.founder_dna.assessment ? <dl>{Object.entries(a.founder_dna.assessment).map(([k, v]) => <div key={k}><dt>{k.replace(/_/g, " ")}</dt><dd>{String(v)}</dd></div>)}</dl> : <p className="gx-help">No assessment saved.</p>}</details>

      {!ctx.supported && <p className="gx-warn" data-testid="execution-unsupported">This business type is not supported yet. The only available template is the Cleaning Service Agreement; no document can be prepared for this project.</p>}

      {ctx.supported && <>
        <h3 style={{ marginTop: 20 }}>Business Passport</h3>
        <p className="gx-help">Contact details you type yourself. They are not a verified identity.</p>
        <div className="px-grid">{PASS.map(([k, l]) => <label className="gx-field" key={k} htmlFor={`pp-${k}`}>{l}
          <input id={`pp-${k}`} className="px-in" type={k === "business_email" ? "email" : "text"} value={pass[k] ?? ""} aria-invalid={!!fe[k]} data-testid={`passport-${k}`}
            onChange={(e) => { setPass((p) => ({ ...p, [k]: e.target.value })); setFe((x) => ({ ...x, [k]: "" })); }} />
          {fe[k] && <span className="gx-err" role="alert">{fe[k]}</span>}</label>)}</div>
        <label className="gx-check"><input type="checkbox" checked={consent} onChange={(e) => { setConsent(e.target.checked); setFe((x) => ({ ...x, consent: "" })); }} data-testid="passport-consent" /><span>I authorize B.I.G. to save these details and reuse them in my documents.</span></label>
        {fe.consent && <p className="gx-err" role="alert">{fe.consent}</p>}
        <div className="gx-row"><button type="button" className="gx-btn" disabled={busy} data-testid="passport-save" onClick={savePass}>{busy ? "Saving..." : "Save passport"}</button>
          {!wf && <button type="button" className="gx-btn" disabled={busy || passMissing || ctx.passport.version < 1} data-testid="document-start" onClick={() => void run(() => startDocument(projectId), false, false)}>Start {ctx.template.title}</button>}</div>
        {!wf && (passMissing || ctx.passport.version < 1) && <p className="gx-help">Save a complete passport to enable starting the document.</p>}
      </>}

      {ctx.supported && wf && <>
        <h3 style={{ marginTop: 24 }}>{ctx.template.title}</h3>
        <p className="gx-help">{ctx.template.notice}</p>
        <p><span className="gx-badge" data-testid="document-status">{wf.status === "READY_FOR_SIGNATURE" ? "READY FOR SIGNATURE (customer approval recorded)" : wf.status}</span> <span className="gx-help">v{wf.version}</span></p>
        {wf.missing.length > 0 && <p className="gx-warn" data-testid="document-missing">Missing required: {wf.missing.join(", ")}</p>}
        <div className="px-grid">{ctx.template.fields.map((f) => {
          const id = `pd-${f.key}`, v = draft[f.key] ?? "";
          return <label className="gx-field" key={f.key} htmlFor={id}>{f.label}{f.required ? " (required)" : ""}{f.type === "money" ? " in dollars" : ""}
            {f.type === "textarea" ? <textarea id={id} className="px-in" value={v} maxLength={f.max_length} aria-invalid={!!fe[f.key]} data-testid={`field-${f.key}`} onChange={(e) => setF(f, e.target.value)} />
              : <input id={id} className="px-in" type={f.type === "date" ? "date" : "text"} inputMode={f.type === "money" ? "decimal" : undefined} value={v} maxLength={f.max_length} aria-invalid={!!fe[f.key]} data-testid={`field-${f.key}`} onChange={(e) => setF(f, e.target.value)} />}
            {fe[f.key] && <span className="gx-err" role="alert">{fe[f.key]}</span>}</label>;
        })}</div>
        {dirty && <p className="gx-warn">Unsaved changes. Save before generating.{wf.status !== "DRAFT" ? " Saving changes will invalidate the current approval; history is kept." : ""}</p>}
        <div className="gx-row">
          <button type="button" className="gx-btn" disabled={busy || !dirty} data-testid="document-save" onClick={saveDoc}>Save fields</button>
          <button type="button" className="gx-btn" disabled={busy || dirty || wf.missing.length > 0 || wf.status === "READY_FOR_SIGNATURE"} data-testid="document-generate" onClick={() => void run(() => generateDocument(projectId, wf.version), false, true)}>Generate agreement</button>
        </div>

        {doc && <section aria-labelledby="px-doc" data-testid="document-preview">
           <h4 id="px-doc" style={{ marginTop: 20 }}>{wf.status === "DRAFT" ? "Previous document — saved corrections require regeneration" : "Current document"}, revision {doc.revision}</h4>
          <p className="gx-help">Hash <code>{doc.content_hash}</code></p>
          {doc.sections.map((s, i) => <div key={i}><h5>{s.heading}</h5><pre>{s.body}</pre></div>)}
          <div className="gx-row"><a className="gx-btn sec" href={documentDownloadUrl(projectId, doc.id)} download={doc.filename} data-testid="document-download">Download printable .html</a></div>
          {wf.status === "GENERATED" && !dirty && <>
            <label className="gx-check"><input type="checkbox" checked={review} onChange={(e) => setReview(e.target.checked)} data-testid="approval-confirm" /><span>I reviewed this exact document (revision {doc.revision}) and approve it. This records my approval only; it is not an e-signature or a submission.</span></label>
            <div className="gx-row"><button type="button" className="gx-btn" disabled={busy || !review} data-testid="document-approve" onClick={() => void run(() => approveDocument(projectId, wf.version, doc), false, true)}>Approve this document</button></div></>}
          {wf.status === "READY_FOR_SIGNATURE" && <p className="gx-ok">Approval recorded. Signature blocks are blank for you to sign by hand. Editing any field will invalidate this approval.</p>}
        </section>}
        {wf.documents.length > 0 && <section data-testid="document-history"><h4 style={{ marginTop: 20 }}>Revision history</h4>
           <ol>{[...wf.documents].reverse().map((d) => <li key={d.id}><b>Revision {d.revision}</b> {d.id === doc?.id ? <span className="gx-tag">{wf.status === "DRAFT" ? "superseded by saved corrections" : "current"}</span> : <span className="gx-tag">superseded</span>}
            <span className="gx-help">{new Date(d.created_at).toLocaleString("en-US")}. {d.approval ? `Approved ${new Date(d.approval.approved_at).toLocaleString("en-US")} (${d.approval.purpose})` : "Not approved"}</span><code>{d.content_hash}</code>
            {" "}<a href={documentDownloadUrl(projectId, d.id)} download={d.filename}>Download</a></li>)}</ol></section>}
      </>}
       <BusinessOrchestrator key={`bo-${projectId}`} projectId={projectId} execution={ctx} docDirty={dirty} onProjectChange={onProjectChange} />
       <ServiceStandby key={projectId} projectId={projectId} />
    </section>
  );
}
