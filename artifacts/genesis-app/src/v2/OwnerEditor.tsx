import { useEffect, useRef, useState } from "react";
import { ApiError } from "./journey-api";
import { createCampaign, fetchCampaigns, updateCampaign } from "./owner-api";
import type { Campaign, CampaignInput } from "./owner-api";
import type { Dict } from "./owner-i18n";
import { centsToInput, parseDollars } from "./owner-money";

interface Props {
  t: Dict;
  base: Campaign | null;
  onSaved: (c: Campaign) => void;
  onClose: () => void;
  onUnauthorized: () => void;
}
const channels = ["website", "email", "social", "referral"] as const;

export default function OwnerEditor({ t, base: initial, onSaved, onClose, onUnauthorized }: Props) {
  const [base, setBase] = useState<Campaign | null>(initial);
  const [title, setTitle] = useState(initial?.title ?? "");
  const [objective, setObjective] = useState(initial?.objective ?? "");
  const [audience, setAudience] = useState(initial?.audience ?? "");
  const [channel, setChannel] = useState<CampaignInput["channel"]>(initial?.channel ?? "website");
  const [content, setContent] = useState(initial?.content ?? "");
  const [budget, setBudget] = useState(initial ? centsToInput(initial.planned_budget_cents) : "");
  const [ack, setAck] = useState(false);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [serverErr, setServerErr] = useState("");
  const [conflict, setConflict] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const alive = useRef(true);
  const headRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => { alive.current = true; headRef.current?.focus(); return () => { alive.current = false; }; }, []);

  const needsAck = !!base && base.status !== "DRAFT";

  const validate = () => {
    const e: Record<string, string> = {};
    const tt = title.trim().length, to = objective.trim().length, ta = audience.trim().length;
    if (!tt) e["campaign-title"] = t.reqTitle; else if (tt < 3 || tt > 160) e["campaign-title"] = t.lenTitle;
    if (!to) e["campaign-objective"] = t.reqObjective; else if (to < 5 || to > 1200) e["campaign-objective"] = t.lenObjective;
    if (!ta) e["campaign-audience"] = t.reqAudience; else if (ta < 3 || ta > 500) e["campaign-audience"] = t.lenAudience;
    if (content.trim().length > 6000) e["campaign-content"] = t.lenContent;
    const p = parseDollars(budget);
    if ("error" in p) e["campaign-budget"] = p.error === "req" ? t.budgetReq : p.error === "max" ? t.budgetMax : t.budgetBad;
    if (needsAck && !ack) e["campaign-ack"] = t.needConfirm;
    setErrs(e);
    const first = Object.keys(e)[0];
    if (first) document.querySelector<HTMLElement>(`[data-testid="${first}"]`)?.focus();
    return { ok: !first, cents: "cents" in p ? p.cents : 0 };
  };

  const submit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (busy) return;
    const v = validate();
    if (!v.ok) return;
    const input: CampaignInput = { title: title.trim(), objective: objective.trim(), audience: audience.trim(), channel, content, planned_budget_cents: v.cents };
    setBusy(true); setServerErr(""); setConflict(false); setDone(false);
    try {
      const saved = base ? await updateCampaign(base, input) : await createCampaign(input);
      if (!alive.current) return;
      setBase(saved); setAck(false); setDone(true);
      onSaved(saved);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) { onUnauthorized(); return; }
      if (!alive.current) return;
      if (err instanceof ApiError && err.status === 409) setConflict(true);
      setServerErr(err instanceof Error ? err.message : String(err));
    } finally { if (alive.current) setBusy(false); }
  };

  const rebase = async () => {
    if (!base) return;
    setBusy(true);
    try {
      const list = await fetchCampaigns();
      if (!alive.current) return;
      const latest = list.campaigns.find((c) => c.id === base.id);
      if (!latest) { setServerErr(t.conflictGone); return; }
      setBase(latest); setConflict(false); setServerErr("");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) { onUnauthorized(); return; }
      if (alive.current) setServerErr(err instanceof Error ? err.message : String(err));
    } finally { if (alive.current) setBusy(false); }
  };

  const fe = (id: string) => errs[id] ? <p className="ow-err" id={`${id}-err`} role="alert">{errs[id]}</p> : null;
  const ia = (id: string) => ({ "aria-invalid": !!errs[id], "aria-describedby": errs[id] ? `${id}-err` : undefined });

  return (
    <form className="ow-card" onSubmit={submit} noValidate aria-labelledby="ow-ed-h" data-testid="campaign-editor">
      <h2 id="ow-ed-h" ref={headRef} tabIndex={-1}>{base ? `${t.editing}: ${base.title}` : t.creating}</h2>
      <p className="ow-help">{t.reviewNote}</p>
      {needsAck && (
        <div className="ow-warn" role="note">
          <p style={{ margin: 0 }}>{t.resetWarn}</p>
          <label className="ow-check"><input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} data-testid="campaign-ack" {...ia("campaign-ack")} /><span>{t.resetConfirm}</span></label>
          {fe("campaign-ack")}
        </div>
      )}
      <label htmlFor="f-title">{t.fTitle}</label>
      <input id="f-title" type="text" maxLength={160} value={title} onChange={(e) => setTitle(e.target.value)} data-testid="campaign-title" {...ia("campaign-title")} />
      {fe("campaign-title")}
      <label htmlFor="f-obj">{t.fObjective}</label>
      <input id="f-obj" type="text" value={objective} onChange={(e) => setObjective(e.target.value)} data-testid="campaign-objective" {...ia("campaign-objective")} />
      {fe("campaign-objective")}
      <label htmlFor="f-aud">{t.fAudience}</label>
      <input id="f-aud" type="text" value={audience} onChange={(e) => setAudience(e.target.value)} data-testid="campaign-audience" {...ia("campaign-audience")} />
      {fe("campaign-audience")}
      <label htmlFor="f-ch">{t.fChannel}</label>
      <select id="f-ch" value={channel} onChange={(e) => setChannel(e.target.value as CampaignInput["channel"])} data-testid="campaign-channel">
        {channels.map((c) => <option key={c} value={c}>{t[c]}</option>)}
      </select>
      <label htmlFor="f-content">{t.fContent}<span className="ow-help">{t.hContent}</span></label>
      <textarea id="f-content" value={content} onChange={(e) => setContent(e.target.value)} data-testid="campaign-content" {...ia("campaign-content")} />
      {fe("campaign-content")}
      <label htmlFor="f-budget">{t.fBudget}<span className="ow-help" id="f-budget-h">{t.hBudget}</span></label>
      <input id="f-budget" type="text" inputMode="decimal" value={budget} onChange={(e) => setBudget(e.target.value)} data-testid="campaign-budget"
        aria-invalid={!!errs["campaign-budget"]} aria-describedby={`f-budget-h${errs["campaign-budget"] ? " campaign-budget-err" : ""}`} />
      {fe("campaign-budget")}
      {serverErr && <div role="alert" data-testid="campaign-error"><p className="ow-err">{serverErr}</p>
        {conflict && <div className="ow-warn"><b>{t.conflictTitle}</b><p style={{ margin: "4px 0 0" }}>{t.conflictBody}</p>
          <div className="ow-row"><button type="button" className="ow-btn sec" onClick={rebase} disabled={busy} data-testid="campaign-rebase">{t.rebase}</button></div></div>}
      </div>}
      {done && <p className="ow-note" role="status" data-testid="campaign-saved">{t.saved}</p>}
      <div className="ow-row" style={{ marginTop: 18 }}>
        <button type="submit" className="ow-btn" disabled={busy} data-testid="campaign-save">{busy ? t.saving : t.save}</button>
        <button type="button" className="ow-btn sec" onClick={onClose} disabled={busy} data-testid="campaign-close">{t.cancel}</button>
      </div>
    </form>
  );
}
