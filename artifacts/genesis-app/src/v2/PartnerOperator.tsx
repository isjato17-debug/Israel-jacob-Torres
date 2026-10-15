import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getSession, signOut } from "./journey-api";
import type { Account } from "./journey-api";
import { getOwnerAccess } from "./owner-api";
import type { OwnerAccess } from "./owner-api";
import { fetchOperatorPartners } from "./partner-api";
import type { OperatorApplication } from "./partner-api";
import { usePLang } from "./partner-i18n";
import OperatorReview from "./OperatorReview";
import PromotionsPanel from "./PromotionsPanel";
import "./owner.css";

const base = import.meta.env.BASE_URL;

export default function PartnerOperator() {
  const [lang, setLang, t] = usePLang();
  const [account, setAccount] = useState<Account | null | undefined>(undefined);
  const [access, setAccess] = useState<OwnerAccess | null>(null);
  const [apps, setApps] = useState<OperatorApplication[] | null>(null);
  const [err, setErr] = useState("");
  const [cleared, setCleared] = useState(false);
  const [copied, setCopied] = useState("");
  const epoch = useRef(0);
  const owner = useRef<string | null>(null);
  owner.current = account?.id ?? null;

  const clear = useCallback(() => { ++epoch.current; owner.current = null; setAccount(null); setAccess(null); setApps(null); setCleared(true); }, []);
  const guard = useCallback((e: unknown) => {
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) { clear(); return ""; }
    return e instanceof Error ? e.message : "Error";
  }, [clear]);

  const loadApps = useCallback(async (): Promise<boolean> => {
    const o = owner.current; if (!o) return false;
    const serial = ++epoch.current;
    try {
      const current = await getSession();
      if (serial !== epoch.current || owner.current !== o) return false;
      if (!current || current.id !== o) { clear(); setAccount(current); return false; }
      const r = await fetchOperatorPartners();
      if (owner.current !== o || serial !== epoch.current) return false;
      setApps(r.applications); setErr(""); return true;
    } catch (e) { if (owner.current !== o || serial !== epoch.current) return false; const m = guard(e); if (m) setErr(m); return false; }
  }, [clear, guard]);
  const boot = useCallback(() => {
    getSession().then(setAccount).catch((e) => { setAccount(null); setErr(e instanceof Error ? e.message : "Error"); });
  }, []);
  useEffect(boot, [boot]);
  useEffect(() => {
    if (!account) return;
    let dead = false;
    getOwnerAccess().then((a) => {
      if (dead || a.account_id !== account.id) return;
      setAccess(a); if (a.owner_access) void loadApps();
    }).catch((e) => { if (!dead) { const m = guard(e); if (m) setErr(m); } });
    return () => { dead = true; };
  }, [account, loadApps, guard]);
  useEffect(() => {
    if (!access?.owner_access) return;
    const f = () => { if (document.visibilityState === "visible") void loadApps(); };
    window.addEventListener("focus", f); document.addEventListener("visibilitychange", f);
    return () => { window.removeEventListener("focus", f); document.removeEventListener("visibilitychange", f); };
  }, [access, loadApps]);
  useEffect(() => { const el = document.documentElement; const pl = el.lang; el.lang = lang; return () => { el.lang = pl; }; }, [lang]);

  const copy = async () => {
    try { await navigator.clipboard.writeText(access?.account_id ?? ""); setCopied(t.copied); } catch { setCopied(access?.account_id ?? ""); }
  };
  const logout = async () => { try { await signOut(); clear(); setCleared(false); } catch (e) { const m = guard(e); if (m) setErr(m); } };
  const upd = (a: OperatorApplication) => { ++epoch.current; setApps((c) => c?.map((x) => x.id === a.id ? a : x) ?? c); };

  let body;
  if (account === undefined) body = <p className="ow-help" role="status">{t.loading}</p>;
  else if (!account) body = (
    <section className="ow-card">
      {cleared && <p className="ow-warn" role="alert">{t.expired}</p>}
      {err && <p className="ow-err" role="alert">{err} <button type="button" className="ow-btn sec" onClick={boot}>{t.retry}</button></p>}
      <p>{t.signIn}</p><a className="ow-btn" href={`${base}next/`}>{t.signInBtn}</a>
    </section>
  );
  else if (!access) body = err ? <p className="ow-err" role="alert">{err} <button type="button" className="ow-btn sec" onClick={boot}>{t.retry}</button></p> : <p className="ow-help" role="status">{t.loading}</p>;
  else if (!access.owner_access) body = (
    <section className="ow-card"><p role="alert">{access.configuration_required ? t.config : t.denied}</p>
      <p><b>{t.yourId}</b></p><div className="ow-id">{access.account_id}</div>
      <div className="ow-row"><button type="button" className="ow-btn sec" onClick={() => void copy()}>{t.copyId}</button><span role="status">{copied}</span></div></section>
  );
  else body = (
    <>
      <p className="ow-help">{t.externalOff}</p>
      {err && <p className="ow-err" role="alert" data-testid="operator-error">{err} <button type="button" className="ow-btn sec" onClick={() => { setErr(""); void loadApps(); }}>{t.retry}</button></p>}
      <h2 style={{ marginTop: 18 }}>{t.opApps}</h2>
      {!apps && !err && <p className="ow-help" role="status">{t.loading}</p>}
      {apps && apps.length === 0 && <p className="ow-card" data-testid="operator-empty">{t.noOpApps}</p>}
      {apps?.map((a) => <OperatorReview key={a.id} t={t} app={a} onUpdated={upd} onDenied={clear} onRefresh={loadApps} />)}
      {apps && <PromotionsPanel t={t} apps={apps} onDenied={clear} />}
    </>
  );

  return (
    <div className="ow" lang={lang} data-testid="partner-operator">
      <div className="ow-wrap">
        <header className="ow-top">
          <div><div className="ow-eyebrow">{t.eyebrow}</div><h1>{t.opTitle}</h1></div>
          <div className="ow-row">
            <label style={{ margin: 0 }} className="ow-row">{t.lang}
              <select className="ow-lang" value={lang} onChange={(e) => setLang(e.target.value as "en" | "es")}><option value="en">English</option><option value="es">Español</option></select></label>
            <a className="ow-btn sec" href={`${base}next/owner/`}>{t.ownerBack}</a>
            {account && <button type="button" className="ow-btn sec" onClick={() => void logout()}>{t.logout}</button>}
          </div>
        </header>
        <p className="ow-warn" role="note">{t.langNote}</p>
        <main>{body}</main>
      </div>
    </div>
  );
}
