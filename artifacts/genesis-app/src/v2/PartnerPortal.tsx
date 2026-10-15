import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getSession, signOut } from "./journey-api";
import type { Account } from "./journey-api";
import { fetchApplicationHistory, fetchApplications, fetchPartnerCatalog } from "./partner-api";
import type { PartnerApplication, PartnerCatalog, PartnerHistory } from "./partner-api";
import { usePLang } from "./partner-i18n";
import type { PDict } from "./partner-i18n";
import PartnerForm from "./PartnerForm";
import "./guided.css";

const base = import.meta.env.BASE_URL;

export function StatusLine({ t, a }: { t: PDict; a: PartnerApplication }) {
  return (
    <p className="gx-help">
      <span className="gx-tag">{t.status}: {a.status}</span> <span className="gx-tag">{t.version}: {a.version}</span>{" "}
      <span className="gx-tag">{t.verification}: {t[a.verification_status]}</span>{" "}
      <span className="gx-tag">{t.agreement}: {t[a.agreement_status]}</span>{" "}
      <span className="gx-tag">{t.integration}: {t[a.integration_status]}</span>
    </p>
  );
}

export function HistoryList({ t, events }: { t: PDict; events: PartnerHistory[] }) {
  if (!events.length) return <p className="gx-help">{t.noEvents}</p>;
  return (
    <ul>{events.map((e, i) => <li key={i}><b>{e.action}</b> - {new Date(e.created_at).toLocaleString()}{e.details?.status ? ` - ${e.details.status}` : ""}{e.details?.version != null ? ` v${e.details.version}` : ""}</li>)}</ul>
  );
}

export default function PartnerPortal() {
  const [lang, setLang, t] = usePLang();
  const [account, setAccount] = useState<Account | null | undefined>(undefined);
  const [catalog, setCatalog] = useState<PartnerCatalog | null>(null);
  const [apps, setApps] = useState<PartnerApplication[] | null>(null);
  const [err, setErr] = useState("");
  const [denied, setDenied] = useState(false);
  const [editor, setEditor] = useState<{ key: string; base: PartnerApplication | null } | null>(null);
  const [hist, setHist] = useState<Record<string, PartnerHistory[] | "loading" | "error">>({});
  const [out, setOut] = useState(false);
  const epoch = useRef(0);
  const owner = useRef<string | null>(null);
  owner.current = account?.id ?? null;

  const clear = useCallback(() => {
    ++epoch.current; owner.current = null; setAccount(null); setApps(null); setCatalog(null); setEditor(null); setHist({}); setDenied(true);
  }, []);
  const guard = useCallback((e: unknown) => {
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) { clear(); return ""; }
    return e instanceof Error ? e.message : "Error";
  }, [clear]);

  const load = useCallback(async (): Promise<boolean> => {
    const o = owner.current; if (!o) return false;
    const serial = ++epoch.current;
    try {
      const current = await getSession();
      if (serial !== epoch.current || owner.current !== o) return false;
      if (!current || current.id !== o) { clear(); setAccount(current); return false; }
      const r = await fetchApplications();
      if (owner.current !== o || serial !== epoch.current) return false;
      setApps(r.applications); setErr(""); return true;
    } catch (e) { if (owner.current !== o || serial !== epoch.current) return false; const m = guard(e); if (m) setErr(m); return false; }
  }, [clear, guard]);

  const boot = useCallback(() => {
    getSession().then((a) => setAccount(a)).catch((e) => { setAccount(null); setErr(e instanceof Error ? e.message : "Error"); });
  }, []);
  useEffect(boot, [boot]);
  useEffect(() => {
    if (!account) return;
    void load();
    fetchPartnerCatalog().then((c) => { if (owner.current === account.id) setCatalog(c); }).catch((e) => { const m = guard(e); if (m) setErr(m); });
  }, [account, load, guard]);
  useEffect(() => {
    if (!account) return;
    const f = () => { if (document.visibilityState === "visible") void load(); };
    window.addEventListener("focus", f); document.addEventListener("visibilitychange", f);
    return () => { window.removeEventListener("focus", f); document.removeEventListener("visibilitychange", f); };
  }, [account, load]);
  useEffect(() => {
    const el = document.documentElement; const pl = el.lang;
    el.lang = lang; return () => { el.lang = pl; };
  }, [lang]);

  const showHist = async (id: string) => {
    if (hist[id] && hist[id] !== "error") { setHist((h) => { const n = { ...h }; delete n[id]; return n; }); return; }
    setHist((h) => ({ ...h, [id]: "loading" }));
    try { const r = await fetchApplicationHistory(id); setHist((h) => ({ ...h, [id]: r.events })); }
    catch (e) { const m = guard(e); if (m) setHist((h) => ({ ...h, [id]: "error" })); }
  };
  const logout = async () => {
    setOut(true);
    try { await signOut(); clear(); setDenied(false); } catch (e) { const m = guard(e); if (m) setErr(m); } finally { setOut(false); }
  };
  const upsert = (a: PartnerApplication) => {
    ++epoch.current; setHist({});
    setApps((cur) => cur && (cur.some((x) => x.id === a.id) ? cur.map((x) => x.id === a.id ? a : x) : [a, ...cur]));
  };

  let body;
  if (account === undefined) body = <div className="gx-skel" role="status" aria-busy="true" aria-label={t.loading} />;
  else if (!account) body = (
    <section className="gx-card">
      {denied && <p className="gx-warn" role="alert" data-testid="partner-expired">{t.expired}</p>}
      {err && <p className="gx-err" role="alert">{err} <button type="button" className="gx-btn sec" onClick={boot}>{t.retry}</button></p>}
      <p>{t.signIn}</p><a className="gx-btn" href={`${base}next/`} data-testid="link-partner-signin">{t.signInBtn}</a>
    </section>
  );
  else body = (
    <>
      <section className="gx-card"><p>{t.intro}</p><p className="gx-warn">{t.underReview}</p>
        {err && <p className="gx-err" role="alert" data-testid="partner-load-error">{err} <button type="button" className="gx-btn sec" onClick={() => { setErr(""); void load(); }}>{t.retry}</button></p>}
      </section>
      <section className="gx-card" aria-labelledby="pa-h">
        <h2 id="pa-h">{t.yourApps}</h2>
        {!apps && !err && <div className="gx-skel" role="status" aria-busy="true" aria-label={t.loading} />}
        {apps && apps.length === 0 && <p className="gx-help" data-testid="partner-empty">{t.none}</p>}
        {apps?.map((a) => {
          const h = hist[a.id];
          return (
            <article className="gx-step" key={a.id} data-testid={`partner-app-${a.id}`}>
              <b className="serif">{a.details.business_name}</b> <span className="gx-tag">{t.selfReported}</span>
              <p className="gx-help">{t.cat[a.details.category]} · {a.details.coverage.join(", ")}</p>
              <StatusLine t={t} a={a} />
              {a.review_note && <p><b>{t.note}:</b> {a.review_note}</p>}
              <div className="gx-row">
                <button type="button" className="gx-btn sec" data-testid={`partner-edit-${a.id}`} onClick={() => setEditor({ key: `${a.id}`, base: a })}>{t.edit}</button>
                <button type="button" className="gx-btn sec" aria-expanded={!!h && h !== "error"} onClick={() => void showHist(a.id)}>{h && h !== "error" ? t.hide : t.history}</button>
              </div>
              {h === "loading" && <p className="gx-help" role="status">{t.loading}</p>}
              {h === "error" && <p className="gx-err" role="alert">{t.refreshFail}</p>}
              {Array.isArray(h) && <HistoryList t={t} events={h} />}
            </article>
          );
        })}
        {!editor && <div className="gx-row"><button type="button" className="gx-btn" data-testid="partner-new" onClick={() => setEditor({ key: `n${Date.now()}`, base: null })}>{t.newApp}</button></div>}
      </section>
      {editor && <PartnerForm key={editor.key} t={t} catalog={catalog} base={editor.base} latest={editor.base ? apps?.find((x) => x.id === editor.base!.id) ?? null : null}
        onSaved={(a) => { upsert(a); setEditor((cur) => cur && { ...cur, base: a }); }} onClose={() => setEditor(null)} onDenied={clear} onRefresh={load} />}
      {catalog && (
        <section className="gx-card">
          <h2>{t.refs}</h2><p className="gx-help">{t.refsNote}</p>
          <ul>{catalog.official_resources.map((r, i) => <li key={r.id ?? i}><a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a></li>)}</ul>
          <h3>{t.juris}</h3><p className="gx-help">{t.jurisNote}</p>
          <ul>{catalog.jurisdictions.map((j) => <li key={j.code}><a href={j.reference_url} target="_blank" rel="noopener noreferrer">{j.name}</a></li>)}</ul>
        </section>
      )}
    </>
  );

  return (
    <div className="gx" lang={lang} data-testid="partner-root">
      <div className="gx-wrap">
        <header className="gx-top">
          <span className="gx-brand">{t.title} <small className="gx-help">{t.eyebrow}</small></span>
          <div className="gx-tools">
            <label>{t.lang}<select value={lang} onChange={(e) => setLang(e.target.value as "en" | "es")} data-testid="partner-lang"><option value="en">English</option><option value="es">Español</option></select></label>
            <a className="gx-btn sec" href={`${base}next/`}>{t.back}</a>
            {account && <button type="button" className="gx-btn sec" disabled={out} onClick={() => void logout()} data-testid="partner-logout">{t.logout}</button>}
          </div>
        </header>
        <main><h1 className="serif">{t.title}</h1><p className="gx-warn" role="note" data-testid="partner-lang-note">{t.langNote}</p>{body}</main>
      </div>
    </div>
  );
}
