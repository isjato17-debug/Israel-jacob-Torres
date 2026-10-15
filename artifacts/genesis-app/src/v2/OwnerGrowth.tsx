import { useCallback, useEffect, useRef, useState } from "react";
import "./owner.css";
import { ApiError, getSession, signOut } from "./journey-api";
import type { Account } from "./journey-api";
import { fetchCampaigns, getOwnerAccess, reviewCampaign } from "./owner-api";
import type { Campaign, CampaignList, OwnerAccess, ReviewAction } from "./owner-api";
import { useLang } from "./owner-i18n";
import type { Dict, Lang } from "./owner-i18n";
import { formatUsd } from "./owner-money";
import OwnerEditor from "./OwnerEditor";
import OwnerCampaignCard from "./OwnerCampaignCard";

const BASE = import.meta.env.BASE_URL;
type Phase = "loading" | "out" | "denied" | "config" | "error" | "ready";
const msg = (e: unknown) => (e instanceof Error ? e.message : String(e));

function Notice({ title, body, children, testid }: { title: string; body?: string; children?: React.ReactNode; testid?: string }) {
  return <section className="ow-card" role="alert" data-testid={testid}><h2>{title}</h2>{body && <p>{body}</p>}{children}</section>;
}

function Capabilities({ t, caps }: { t: Dict; caps: CampaignList["capabilities"] }) {
  const rows: [string, boolean][] = [[t.cPlan, caps.planning], [t.cReview, caps.internal_review], [t.cAi, false], [t.cPub, false], [t.cSpend, false], [t.cAnalytics, false]];
  return (
    <section className="ow-card" aria-labelledby="ow-caps" style={{ marginTop: 0 }}>
      <h2 id="ow-caps">{t.caps}</h2>
      {rows.map(([n, on]) => <div className="ow-cap" key={n}><span>{n}</span><b>{on ? t.available : t.unavailable}</b></div>)}
    </section>
  );
}

export default function OwnerGrowth() {
  const [lang, setLang, t] = useLang();
  const [phase, setPhase] = useState<Phase>("loading");
  const [account, setAccount] = useState<Account | null>(null);
  const [access, setAccess] = useState<OwnerAccess | null>(null);
  const [list, setList] = useState<CampaignList | null>(null);
  const [err, setErr] = useState("");
  const [refreshErr, setRefreshErr] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [editor, setEditor] = useState<{ key: string; base: Campaign | null } | null>(null);
  const [busyId, setBusyId] = useState("");
  const [actErr, setActErr] = useState<Record<string, string>>({});
  const [copyMsg, setCopyMsg] = useState("");
  const [logoutErr, setLogoutErr] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const [endedNote, setEndedNote] = useState("");
  const epoch = useRef(0);
  const accountId = useRef<string | null>(null);

  const clearPrivate = useCallback(() => {
    epoch.current++; accountId.current = null;
    setAccount(null); setAccess(null); setList(null); setEditor(null); setActErr({}); setRefreshErr("");
  }, []);
  const unauthorized = useCallback(() => { clearPrivate(); setEndedNote(t.sessionEnded); setPhase("out"); }, [clearPrivate, t.sessionEnded]);
  const unauthRef = useRef(unauthorized); unauthRef.current = unauthorized;

  const load = useCallback(async () => {
    const my = ++epoch.current;
    setPhase("loading"); setErr("");
    try {
      const acct = await getSession();
      if (my !== epoch.current) return;
      if (!acct) { clearPrivate(); setPhase("out"); return; }
      if (accountId.current && accountId.current !== acct.id) { setList(null); setEditor(null); }
      accountId.current = acct.id; setAccount(acct);
      const acc = await getOwnerAccess();
      if (my !== epoch.current) return;
      setAccess(acc);
      if (!acc.owner_access) { setList(null); setPhase(acc.configuration_required ? "config" : "denied"); return; }
      const data = await fetchCampaigns();
      if (my !== epoch.current) return;
      setList(data); setPhase("ready");
    } catch (e) {
      if (my !== epoch.current) return;
      if (e instanceof ApiError && e.status === 401) { unauthRef.current(); return; }
      if (e instanceof ApiError && e.status === 403) { setList(null); setPhase("denied"); return; }
      setErr(msg(e)); setPhase("error");
    }
  }, [clearPrivate]);

  const refresh = useCallback(async () => {
    const my = epoch.current;
    setRefreshing(true);
    try {
      const data = await fetchCampaigns();
      if (my !== epoch.current) return;
      setList(data); setRefreshErr("");
    } catch (e) {
      if (my !== epoch.current) return;
      if (e instanceof ApiError && e.status === 401) { unauthRef.current(); return; }
      if (e instanceof ApiError && e.status === 403) { clearPrivate(); setPhase("denied"); return; }
      setRefreshErr(msg(e));
    } finally { if (my === epoch.current) setRefreshing(false); }
  }, [clearPrivate]);

  useEffect(() => { void load(); return () => { epoch.current++; }; }, [load]);
  useEffect(() => {
    const onFocus = () => { if (document.visibilityState === "visible" && accountId.current) void refresh(); };
    window.addEventListener("focus", onFocus); document.addEventListener("visibilitychange", onFocus);
    return () => { window.removeEventListener("focus", onFocus); document.removeEventListener("visibilitychange", onFocus); };
  }, [refresh]);

  const upsert = (c: Campaign) => { void refresh(); setList((l) => l ? { ...l, campaigns: l.campaigns.some((x) => x.id === c.id) ? l.campaigns.map((x) => x.id === c.id ? c : x) : [c, ...l.campaigns] } : l); };

  const act = async (c: Campaign, a: ReviewAction, confirm = false) => {
    const my = epoch.current;
    setBusyId(c.id); setActErr((m) => ({ ...m, [c.id]: "" }));
    try {
      await reviewCampaign(c, a, confirm);
      if (my !== epoch.current) return;
      await refresh();
    } catch (e) {
      if (my !== epoch.current) return;
      if (e instanceof ApiError && e.status === 401) { unauthRef.current(); return; }
      setActErr((m) => ({ ...m, [c.id]: msg(e) }));
    } finally { if (my === epoch.current) setBusyId(""); }
  };

  const logout = async () => {
    setLoggingOut(true); setLogoutErr("");
    try { await signOut(); clearPrivate(); setEndedNote(t.signedOut); setPhase("out"); }
    catch (e) { setLogoutErr(msg(e)); }
    finally { setLoggingOut(false); }
  };

  const copy = async () => {
    try { await navigator.clipboard.writeText(access?.account_id ?? ""); setCopyMsg(t.copied); }
    catch { setCopyMsg(t.copyFail); }
  };

  const links = (
    <div className="ow-row">
      <a className="ow-btn" href={`${BASE}next/`} data-testid="owner-signin">{t.signin}</a>
      <a className="ow-btn sec" href={BASE} data-testid="owner-workspace">{t.workspace}</a>
    </div>
  );

  let body: React.ReactNode = null;
  if (phase === "loading") body = <div role="status" aria-live="polite" data-testid="owner-loading"><p>{t.loading}</p><div className="ow-skel" /><div className="ow-skel" /></div>;
  else if (phase === "out") body = <Notice testid="owner-signin-required" title={t.signinTitle} body={endedNote || t.signinBody}>{links}</Notice>;
  else if (phase === "error") body = <Notice testid="owner-error" title={t.errorTitle} body={err}><div className="ow-row"><button className="ow-btn" onClick={() => void load()} data-testid="owner-retry">{t.retry}</button></div></Notice>;
  else if (phase === "config" || phase === "denied") body = (
    <Notice testid={phase === "config" ? "owner-config" : "owner-denied"} title={phase === "config" ? t.configTitle : t.deniedTitle} body={phase === "config" ? t.configBody : t.deniedBody}>
      {access?.account_id && <><p style={{ marginBottom: 4 }}><b>{t.yourId}</b></p>
        <div className="ow-id" data-testid="owner-account-id">{access.account_id}</div>
        <div className="ow-row"><button className="ow-btn" onClick={copy} data-testid="owner-copy-id">{t.copy}</button>
          <span role="status" data-testid="owner-copy-status">{copyMsg}</span></div></>}
      <div className="ow-row"><a className="ow-btn sec" href={BASE}>{t.workspace}</a></div>
    </Notice>
  );
  else if (list) body = <Console t={t} lang={lang} list={list} refreshing={refreshing} refreshErr={refreshErr} editor={editor} busyId={busyId} actErr={actErr}
    onRefresh={() => void refresh()} onNew={() => setEditor({ key: `n${Date.now()}`, base: null })}
    onEdit={(c) => setEditor({ key: `${c.id}`, base: c })} onClose={() => setEditor(null)} onSaved={upsert} onUnauthorized={unauthorized} onAction={act} />;

  const signedIn = account && (phase === "ready" || phase === "denied" || phase === "config");
  return (
    <div className="ow" data-testid="owner-console">
      <div className="ow-wrap">
        <header className="ow-top">
          <div><div className="ow-eyebrow">Genesis OS - {t.private}</div><h1>{t.title}</h1></div>
          <div className="ow-row">
            <label style={{ margin: 0 }} className="ow-row">{t.lang}
              <select className="ow-lang" value={lang} onChange={(e) => setLang(e.target.value as Lang)} data-testid="owner-lang">
                <option value="en">English</option><option value="es">Espanol</option></select></label>
            {signedIn && <button className="ow-btn sec" onClick={logout} disabled={loggingOut} data-testid="owner-logout">{loggingOut ? t.loggingOut : t.logout}</button>}
          </div>
        </header>
        {logoutErr && <p className="ow-err" role="alert" data-testid="owner-logout-error">{t.logoutFail}{logoutErr}</p>}
        <main>{body}</main>
      </div>
    </div>
  );
}

interface ConsoleProps {
  t: Dict; lang: Lang; list: CampaignList; refreshing: boolean; refreshErr: string;
  editor: { key: string; base: Campaign | null } | null; busyId: string; actErr: Record<string, string>;
  onRefresh: () => void; onNew: () => void; onEdit: (c: Campaign) => void; onClose: () => void;
  onSaved: (c: Campaign) => void; onUnauthorized: () => void;
  onAction: (c: Campaign, a: ReviewAction, confirm?: boolean) => Promise<void>;
}

function Console(p: ConsoleProps) {
  const { t, lang, list } = p;
  return (
    <>
      <div className="ow-grid two" style={{ marginTop: 18 }}>
        <section className="ow-card" aria-labelledby="ow-ov" style={{ marginTop: 0 }} data-testid="owner-overview">
          <h2 id="ow-ov">{t.overview}</h2>
          <div className="ow-grid two">
            <div><div className="ow-help">{t.count}</div><div className="ow-big" data-testid="owner-campaign-count">{list.overview.campaign_count}</div></div>
            <div><div className="ow-help">{t.planned}</div><div className="ow-big" data-testid="owner-planned-budget">{formatUsd(list.overview.planned_budget_cents, lang)}</div></div>
          </div>
          <p className="ow-note" data-testid="owner-no-verified">{t.noVerified}</p>
          <p className="ow-help">{t.reviewNote}</p>
        </section>
        <Capabilities t={t} caps={list.capabilities} />
      </div>
      <div className="ow-row" style={{ marginTop: 24, justifyContent: "space-between" }}>
        <h2>{t.campaigns}</h2>
        <div className="ow-row" style={{ marginTop: 0 }}>
          <button className="ow-btn sec" onClick={p.onRefresh} disabled={p.refreshing} data-testid="campaign-refresh">{p.refreshing ? t.refreshing : t.refresh}</button>
          <button className="ow-btn" onClick={p.onNew} data-testid="campaign-new">{t.newCampaign}</button>
        </div>
      </div>
      {p.refreshErr && <p className="ow-err" role="alert">{t.refreshFail}{p.refreshErr}</p>}
      {p.editor && <OwnerEditor key={p.editor.key} t={t} base={p.editor.base} onSaved={p.onSaved} onClose={p.onClose} onUnauthorized={p.onUnauthorized} />}
      {list.campaigns.length === 0 && !p.editor && (
        <section className="ow-card" data-testid="campaign-empty"><h3>{t.emptyTitle}</h3><p>{t.emptyBody}</p>
          <button className="ow-btn" onClick={p.onNew}>{t.newCampaign}</button></section>
      )}
      {list.campaigns.map((c) => (
        <OwnerCampaignCard key={c.id} t={t} lang={lang} c={c} busy={p.busyId === c.id} error={p.actErr[c.id] ?? ""} onEdit={p.onEdit} onAction={p.onAction} />
      ))}
    </>
  );
}
