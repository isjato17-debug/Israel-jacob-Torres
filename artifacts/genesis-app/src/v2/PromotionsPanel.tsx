import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "./journey-api";
import { createPromotion, fetchPromotions, reviewPromotion } from "./partner-api";
import type { OperatorApplication, Promotion } from "./partner-api";
import type { PDict } from "./partner-i18n";

export default function PromotionsPanel({ t, apps, onDenied }: { t: PDict; apps: OperatorApplication[]; onDenied: () => void }) {
  const [list, setList] = useState<Promotion[] | null>(null);
  const [err, setErr] = useState("");
  const [formErr, setFormErr] = useState("");
  const [partner, setPartner] = useState("");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [perm, setPerm] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState("");
  const alive = useRef(true);
  const epoch = useRef(0);
  const den = useRef(onDenied); den.current = onDenied;
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);

  const fail = (x: unknown): string => {
    if (x instanceof ApiError && (x.status === 401 || x.status === 403)) { den.current(); return ""; }
    return x instanceof Error ? x.message : "Error";
  };
  const load = async () => {
    const serial = ++epoch.current;
    try { const r = await fetchPromotions(); if (alive.current && serial === epoch.current) { setList(r.promotions); setErr(""); } }
    catch (x) { if (serial !== epoch.current || !alive.current) return; const m = fail(x); if (m) setErr(m); }
  };
  useEffect(() => {
    void load();
    const f = () => { if (document.visibilityState === "visible") void load(); };
    window.addEventListener("focus", f); document.addEventListener("visibilitychange", f);
    return () => { window.removeEventListener("focus", f); document.removeEventListener("visibilitychange", f); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    const tl = title.trim().length, cl = content.trim().length;
    if (!partner) return setFormErr(t.vPartner);
    if (tl < 3 || tl > 160) return setFormErr(t.vPTitle);
    if (cl < 5 || cl > 6000) return setFormErr(t.vPContent);
    if (perm.trim().length > 500) return setFormErr(t.vPPerm);
    if (!consent) return setFormErr(t.needConsent);
    ++epoch.current; setBusy("create"); setFormErr("");
    try {
      const p = await createPromotion({ partner_id: partner, title: title.trim(), content: content.trim(), partner_permission_reference: perm.trim() });
      if (!alive.current) return;
      setList((c) => [p, ...(c ?? [])]); setTitle(""); setContent(""); setPerm(""); setConsent(false);
    } catch (x) { const m = fail(x); if (alive.current && m) setFormErr(`${t.saveErr} ${m}`); }
    finally { if (alive.current) setBusy(""); }
  };
  const act = async (p: Promotion, a: "approve" | "archive") => {
    ++epoch.current; setBusy(p.id); setErr("");
    try {
      const u = await reviewPromotion(p, a);
      if (alive.current) setList((c) => c?.map((x) => x.id === u.id ? u : x) ?? c);
    } catch (x) {
      const m = fail(x);
      if (alive.current && m) { setErr(x instanceof ApiError && x.status === 409 ? t.conflict : m); void load(); }
    } finally { if (alive.current) setBusy(""); }
  };
  const nameOf = (id: string) => apps.find((a) => a.id === id)?.details.business_name ?? id;

  return (
    <section className="ow-card" aria-labelledby="pp-h" data-testid="partner-promotions">
      <h2 id="pp-h">{t.promos}</h2><p className="ow-help">{t.promosNote}</p>
      {err && <p className="ow-err" role="alert">{err} <button type="button" className="ow-btn sec" onClick={() => void load()}>{t.retry}</button></p>}
      <form onSubmit={create} noValidate>
        <label htmlFor="pp-partner">{t.partner}</label>
        <select id="pp-partner" value={partner} onChange={(e) => setPartner(e.target.value)}><option value="">-</option>
          {apps.map((a) => <option key={a.id} value={a.id}>{a.details.business_name}</option>)}</select>
        <label htmlFor="pp-title">{t.pTitle}</label><input id="pp-title" maxLength={160} value={title} onChange={(e) => setTitle(e.target.value)} />
        <label htmlFor="pp-content">{t.pContent}</label><textarea id="pp-content" maxLength={6000} value={content} onChange={(e) => setContent(e.target.value)} />
        <label htmlFor="pp-perm">{t.pPerm}</label><input id="pp-perm" maxLength={500} value={perm} onChange={(e) => setPerm(e.target.value)} />
        <label className="ow-check"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} /><span>{t.pConsent}</span></label>
        <div aria-live="assertive">{formErr && <p className="ow-err" role="alert">{formErr}</p>}</div>
        <div className="ow-row"><button type="submit" className="ow-btn" disabled={!!busy} data-testid="promotion-create">{busy === "create" ? t.saving : t.createDraft}</button></div>
      </form>
      {!list && !err && <p className="ow-help" role="status">{t.loading}</p>}
      {list && list.length === 0 && <p className="ow-help">{t.noPromos}</p>}
      {list?.map((p) => (
        <article className="ow-card" key={p.id} data-testid={`promotion-${p.id}`}>
          <h3>{p.title}</h3><p className="ow-help">{nameOf(p.partner_id)} · {p.status} · v{p.version}</p>
          <p>{p.content}</p>
          <p className="ow-help">{t.pPerm}: {p.partner_permission_reference || "-"}</p>
          <p className="ow-help">{t.attribution}: {p.attribution_code}. {t.verifiedPerf}</p>
          <div className="ow-row">
            {p.status === "DRAFT" && <button type="button" className="ow-btn" disabled={busy === p.id} onClick={() => void act(p, "approve")}>{t.approve}</button>}
            {p.status !== "ARCHIVED" && <button type="button" className="ow-btn sec" disabled={busy === p.id} onClick={() => void act(p, "archive")}>{t.archive}</button>}
          </div>
        </article>
      ))}
    </section>
  );
}
