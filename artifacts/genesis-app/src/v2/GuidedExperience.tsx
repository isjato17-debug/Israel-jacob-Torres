import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { fetchCatalog } from "./api";
import type { Catalog, Stage } from "./api";
import {
  ApiError, fetchJourneys, getSession, savePreferences, saveAnswer, signIn, signOut, startJourney,
} from "./journey-api";
import type { Account, DetailMode, Journey, Language, Question } from "./journey-api";
import { dict } from "./guided-i18n";
import type { Key } from "./guided-i18n";
import "./guided.css";
import OwnerAccessLink from "./OwnerAccessLink";

const ORDER: Question[] = ["state", "entity_type", "ownership_type", "goal"];
const STAGES: Stage[] = ["start", "run", "grow"];
const QKEY: Record<Question, [Key, Key]> = {
  state: ["qState", "hState"], entity_type: ["qEntity", "hEntity"],
  ownership_type: ["qOwner", "hOwner"], goal: ["qGoal", "hGoal"],
};
const VKEY: Record<Question, Key> = { state: "vState", entity_type: "vEntity", ownership_type: "vOwner", goal: "vGoal" };
const base = import.meta.env.BASE_URL;
const pretty = (s: string) => s.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

type SR = { lang: string; continuous: boolean; interimResults: boolean; start(): void; stop(): void; abort(): void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null;
  onerror: (() => void) | null; onend: (() => void) | null };
function recognitionCtor(): (new () => SR) | null {
  const w = window as unknown as { SpeechRecognition?: new () => SR; webkitSpeechRecognition?: new () => SR };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export default function GuidedExperience() {
  const [lang, setLang] = useState<Language>("en");
  const [detail, setDetail] = useState<DetailMode>("simple");
  const t = useCallback((k: Key) => dict[lang][k], [lang]);

  const [account, setAccount] = useState<Account | null | undefined>(undefined);
  const [initErr, setInitErr] = useState("");
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catErr, setCatErr] = useState("");
  const [journeys, setJourneys] = useState<Journey[]>([]);
  const [jLoaded, setJLoaded] = useState(false);
  const [expired, setExpired] = useState(false);

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenant, setTenant] = useState("");
  const [authErr, setAuthErr] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [recover, setRecover] = useState(false);

  const [pendingStage, setPendingStage] = useState<Stage | null>(null);
  const [consent, setConsent] = useState(false);
  const [startErr, setStartErr] = useState("");
  const [busy, setBusy] = useState(false);

  const [activeId, setActiveId] = useState<string | null>(null);
  const [view, setView] = useState<"mission" | "question">("mission");
  const [editing, setEditing] = useState<Question | null>(null);
  const [draft, setDraft] = useState("");
  const [fieldErr, setFieldErr] = useState("");
  const [saveErr, setSaveErr] = useState("");
  const [conflict, setConflict] = useState(false);
  const [status, setStatus] = useState("");
  const [prefMsg, setPrefMsg] = useState("");

  const [listening, setListening] = useState(false);
  const [voiceErr, setVoiceErr] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

  const headRef = useRef<HTMLHeadingElement>(null);
  const errRef = useRef<HTMLParagraphElement>(null);
  const recRef = useRef<SR | null>(null);
  const autoOpened = useRef(false);
  const busyRef = useRef(false);
  const accountId = useRef<string | null>(null);
  accountId.current = account?.id ?? null;
  busyRef.current = busy;
  const draftFor = useRef("");

  const active = journeys.find((j) => j.id === activeId) ?? null;
  const field: Question | null = view === "question" && active ? (editing ?? active.next_question) : null;
  const speechOk = typeof window !== "undefined" && "speechSynthesis" in window;
  const SRC = typeof window !== "undefined" ? recognitionCtor() : null;

  const clearAccount = useCallback((wasExpired: boolean) => {
    accountId.current = null;
    try { recRef.current?.abort(); } catch { /* Already stopped. */ }
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    setListening(false); setSpeaking(false); setVoiceConsent(false);
    setAccount(null); setJourneys([]); setJLoaded(false); setActiveId(null); setView("mission"); setEditing(null);
    setDraft(""); setFieldErr(""); setSaveErr(""); setConflict(false); setStatus(""); setPendingStage(null);
    setConsent(false); setStartErr(""); setPassword(""); setEmail(""); setTenant(""); setAuthErr("");
    setPrefMsg(""); setExpired(wasExpired); autoOpened.current = false;
    draftFor.current = "";
  }, []);

  const onErr = useCallback((e: unknown): string => {
    if (e instanceof ApiError && e.status === 401) { clearAccount(true); return ""; }
    return e instanceof Error ? e.message : "Error";
  }, [clearAccount]);

  const mergeJourney = (j: Journey) => setJourneys((cur) => cur.some((x) => x.id === j.id) ? cur.map((x) => x.id === j.id ? j : x) : [j, ...cur]);

  // boot
  const boot = useCallback(() => {
    setInitErr("");
    getSession().then(setAccount).catch((e) => setInitErr(e instanceof Error ? e.message : "Error"));
  }, []);
  useEffect(boot, [boot]);
  const loadCatalog = useCallback(() => {
    setCatErr(""); fetchCatalog().then(setCatalog).catch((e) => setCatErr(e instanceof Error ? e.message : "Error"));
  }, []);
  useEffect(loadCatalog, [loadCatalog]);

  const loadJourneys = useCallback(async (silent = false) => {
    const owner = accountId.current;
    if (!owner) return false;
    if (!silent) setInitErr("");
    try {
      const r = await fetchJourneys();
      if (accountId.current !== owner) return false;
      setJourneys(r.journeys); setJLoaded(true);
      return true;
    } catch (e) {
      if (accountId.current !== owner) return false;
      const m = onErr(e);
      if (m && !silent) setInitErr(m);
      return false;
    }
  }, [onErr]);

  useEffect(() => { if (account) void loadJourneys(); }, [account, loadJourneys]);

  // refetch on focus (never touches draft)
  useEffect(() => {
    if (!account) return;
    const f = () => { if (!busyRef.current && document.visibilityState === "visible") void loadJourneys(true); };
    window.addEventListener("focus", f); document.addEventListener("visibilitychange", f);
    return () => { window.removeEventListener("focus", f); document.removeEventListener("visibilitychange", f); };
  }, [account, loadJourneys]);

  // resume next unanswered question once
  useEffect(() => {
    if (!jLoaded || autoOpened.current) return;
    autoOpened.current = true;
    const latest = [...journeys].sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    const cur = latest.find((j) => j.next_question) ?? latest[0];
    if (cur) { setActiveId(cur.id); setView(cur.next_question ? "question" : "mission"); setLang(cur.language); setDetail(cur.detail_mode); }
  }, [jLoaded, journeys]);

  // prefill draft only when question identity changes
  const qIdentity = active && field ? `${active.id}:${field}` : "";
  useEffect(() => {
    if (!qIdentity || !active || !field) return;
    if (draftFor.current === qIdentity) return;
    draftFor.current = qIdentity;
    setDraft(active.answers[field] ?? ""); setFieldErr(""); setSaveErr(""); setConflict(false); setStatus(""); setVoiceErr(false);
    window.setTimeout(() => headRef.current?.focus(), 30);
  }, [qIdentity, active, field]);

  // cleanup speech on question change/unmount
  const stopSpeech = useCallback(() => {
    try { recRef.current?.abort(); } catch { /* ignore */ }
    recRef.current = null; setListening(false);
    if (speechOk) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, [speechOk]);
  useEffect(() => { stopSpeech(); return stopSpeech; }, [qIdentity, stopSpeech]);

  useEffect(() => {
    if (!speechOk) return;
    const load = () => setVoices(window.speechSynthesis.getVoices());
    load(); window.speechSynthesis.addEventListener?.("voiceschanged", load);
    return () => window.speechSynthesis.removeEventListener?.("voiceschanged", load);
  }, [speechOk]);
  const localVoice = useMemo(() => voices.find((v) => v.localService && v.lang.toLowerCase().startsWith(lang)), [voices, lang]);

  const submitAuth = async (e: FormEvent) => {
    e.preventDefault(); setAuthErr(""); setAuthBusy(true);
    try {
      const a = await signIn(mode, email.trim(), password, mode === "register" ? tenant.trim() : undefined);
      setPassword(""); setExpired(false); setAccount(a);
    } catch (x) { setAuthErr(x instanceof Error ? x.message : "Error"); } finally { setAuthBusy(false); }
  };
  const doLogout = async () => {
    setBusy(true);
    try { await signOut(); stopSpeech(); clearAccount(false); }
    catch (error) { const message = onErr(error); if (message) setInitErr(message); }
    finally { setBusy(false); }
  };

  const openStage = (s: Stage) => {
    if (!account) window.setTimeout(() => document.querySelector<HTMLElement>('[data-testid="email"]')?.focus(), 0);
    const j = journeys.filter((x) => x.stage === s).sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];
    if (j) {
      setPendingStage(null); setActiveId(j.id); setEditing(null); setLang(j.language); setDetail(j.detail_mode);
      setView(j.next_question ? "question" : "mission"); draftFor.current = "";
    } else { setPendingStage(s); setConsent(false); setStartErr(""); }
  };
  const doStart = async () => {
    if (!pendingStage) return;
    if (!consent) { setStartErr(t("startNeed")); return; }
    setBusy(true); setStartErr("");
    try {
      const j = await startJourney(pendingStage, lang, detail);
      mergeJourney(j); setActiveId(j.id); setPendingStage(null); setEditing(null); draftFor.current = "";
      setView(j.next_question ? "question" : "mission");
    } catch (x) { const m = onErr(x); if (m) setStartErr(m); } finally { setBusy(false); }
  };

  const validate = (q: Question, v: string) => {
    const s = v.trim();
    if (q === "goal") return s.length >= 5 && s.length <= 1200;
    return !!s;
  };
  const doContinue = async (e: FormEvent) => {
    e.preventDefault();
    if (!active || !field) return;
    if (!validate(field, draft)) {
      setFieldErr(t(VKEY[field])); window.setTimeout(() => errRef.current?.focus(), 20); return;
    }
    setFieldErr(""); setSaveErr(""); setConflict(false); setBusy(true); setStatus(t("saving"));
    try {
      const j = await saveAnswer(active, field, field === "goal" ? draft.trim() : draft);
      mergeJourney(j); setStatus(t("saved")); setEditing(null);
      if (!j.next_question) { setView("mission"); draftFor.current = ""; }
    } catch (x) {
      setStatus(t("notSaved"));
      if (x instanceof ApiError && x.status === 409) setConflict(true);
      else { const m = onErr(x); if (m) setSaveErr(`${t("saveFail")} ${m}`); }
      window.setTimeout(() => errRef.current?.focus(), 20);
    } finally { setBusy(false); }
  };
  const reload = async () => {
    setBusy(true);
    const ok = await loadJourneys(true);
    setBusy(false);
    if (ok) { setConflict(false); setStatus(t("reloaded")); }
  };

  const changePrefs = async (l: Language, d: DetailMode) => {
    setLang(l); setDetail(d); setPrefMsg("");
    if (!active) return;
    setBusy(true);
    try { const j = await savePreferences(active, l, d); mergeJourney(j); setPrefMsg(dict[l].prefSaved); }
    catch (x) {
      if (x instanceof ApiError && x.status === 409) { setConflict(true); setPrefMsg(dict[l].prefFail); }
      else { const m = onErr(x); if (m) setPrefMsg(`${dict[l].prefFail} ${m}`); }
    }
    finally { setBusy(false); }
  };

  const toggleListen = () => {
    if (listening) { stopSpeech(); return; }
    if (!SRC) return;
    const r = new SRC(); r.lang = lang === "es" ? "es-US" : "en-US"; r.continuous = false; r.interimResults = false;
    r.onresult = (ev) => {
      if (recRef.current !== r) return;
      let text = ""; for (let i = 0; i < ev.results.length; i++) text += ev.results[i][0].transcript;
      setDraft((d) => (d ? `${d} ` : "") + text.trim());
    };
    r.onerror = () => { setVoiceErr(true); setListening(false); };
    r.onend = () => { setListening(false); };
    recRef.current = r; setVoiceErr(false);
    try { r.start(); setListening(true); } catch { setVoiceErr(true); }
  };
  const toggleSpeak = () => {
    if (!speechOk || !field) return;
    if (speaking) { stopSpeech(); return; }
    if (!localVoice) return;
    const u = new SpeechSynthesisUtterance(`${t(QKEY[field][0])} ${t(QKEY[field][1])}`);
    u.voice = localVoice; u.lang = localVoice.lang;
    u.onend = () => setSpeaking(false); u.onerror = () => setSpeaking(false);
    window.speechSynthesis.cancel(); setSpeaking(true); window.speechSynthesis.speak(u);
  };
  const [voiceConsent, setVoiceConsent] = useState(false);

  const stateName = (code?: string) => catalog?.states.find((s) => s.code === code)?.name ?? code ?? "";
  const choiceName = (value: string) => {
    const spanish: Record<string, string> = {
      LLC: "LLC (responsabilidad limitada)", Corporation: "Corporación",
      Partnership: "Sociedad", Nonprofit: "Organización sin fines de lucro",
      "Sole proprietorship": "Empresa individual", "Independent business": "Empresa independiente",
      "Holding company": "Sociedad matriz (holding)", Subsidiary: "Empresa subsidiaria",
    };
    return lang === "es" ? spanish[value] ?? value : value;
  };
  const display = (q: Question, j: Journey) => { const v = j.answers[q]; return !v ? "" : q === "state" ? stateName(v) : q === "goal" ? v : choiceName(v); };

  const planText = (j: Journey) => {
    const L = [
      "GENESIS OS SAVED PLAN - PREPARED, NOT SUBMITTED",
      "Status: SAVED in your Genesis account. NOT submitted to any agency. NOT completed.",
      "Mode: GUIDED planning, not connected AI. Rule-based checklist, not state-specific legal advice.",
      "Answers are user-provided and not verified.", "",
      `Stage: ${j.stage}`, `Journey status: ${j.status}`, `Last saved: ${j.updated_at}`,
      `State: ${stateName(j.answers.state)}`, `Entity type: ${j.answers.entity_type ?? ""}`,
      `Ownership: ${j.answers.ownership_type ?? ""}`, `Goal: ${j.answers.goal ?? ""}`, "",
      `Costs: NOT QUOTED. Charges authorized: ${j.cost.charges_authorized ? "yes" : "no"}.`, "", "STEPS (all service workflows NOT_STARTED)",
    ];
    j.plan?.steps.forEach((s) => {
      L.push(`${s.order}. ${s.title} [${s.status}] workflow: ${s.workflow_status}${s.professional_review ? " (professional review)" : ""}`, `   Next: ${s.next_action}`);
      if (s.official_url) L.push(`   Official: ${s.official_url}`);
    });
    if (j.plan?.approvals.length) L.push("", "APPROVALS NEEDED FROM YOU", ...j.plan.approvals.map((a) => `- ${a}`));
    L.push("", j.plan?.notice ?? "", j.notice);
    return L.join("\n");
  };
  const download = (j: Journey) => {
    const url = URL.createObjectURL(new Blob([planText(j)], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = `genesis-saved-plan-${j.stage}-prepared-not-submitted.txt`;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  };

  const stageLabel = (s: Stage) => t(s);
  const stageBlurb = (s: Stage) => t(`${s}B` as Key);
  const guestHref = `${base}next/draft/`;

  /* ---------- render pieces ---------- */
  const header = (
    <header className="gx-top">
      <span className="gx-brand">{t("brand")} <span className="gx-badge" data-testid="text-mode">{t("mode")}</span></span>
      <div className="gx-tools">
        <OwnerAccessLink accountId={account?.id ?? null} language={lang} />
        <label>{t("language")}
          <select data-testid="language" disabled={busy} value={lang} onChange={(e) => void changePrefs(e.target.value as Language, detail)}>
            <option value="en">English</option><option value="es">Español</option>
          </select></label>
        <label>{t("details")}
          <select data-testid="details" disabled={busy} value={detail} onChange={(e) => void changePrefs(lang, e.target.value as DetailMode)}>
            <option value="simple">{t("simple")}</option><option value="details">{t("detailsOpt")}</option>
          </select></label>
        {account && <button type="button" className="gx-btn sec" data-testid="logout" disabled={busy} onClick={doLogout}>{t("logout")}</button>}
      </div>
    </header>
  );

  const stageCards = (
    <div className="gx-stages" role="group" aria-label="START / RUN / GROW">
      {STAGES.map((s) => {
        const j = journeys.find((x) => x.stage === s);
        return (
          <button key={s} type="button" className="gx-stage" aria-pressed={pendingStage === s || (active?.stage === s)}
            data-testid={`stage-${s}`} disabled={busy} onClick={() => openStage(s)}>
            <b>{stageLabel(s)}</b><span>{stageBlurb(s)}</span>
            {j && <small>{j.answered_count} {t("of")} {j.question_count} {t("progress")}</small>}
          </button>
        );
      })}
    </div>
  );

  const authView = (
    <>
      {stageCards}
      <section className="gx-hero">
        <h1>{t("heroH")}</h1><p>{t("heroP")}</p>
      </section>
      <div className="gx-two">
        <section className="gx-card" aria-labelledby="auth-h">
          <h2 id="auth-h">{mode === "login" ? t("signin") : t("register")}</h2>
          <p className="gx-help">{t("authWhy")}</p>
          {expired && <p className="gx-warn" role="alert" data-testid="text-expired">{t("expired")}</p>}
          <form onSubmit={submitAuth}>
            <div className="gx-row" role="group" aria-label={t("authMode")}>
              <button type="button" className={`gx-btn ${mode === "login" ? "" : "sec"}`} aria-pressed={mode === "login"} data-testid="auth-mode" onClick={() => setMode("login")}>{t("signin")}</button>
              <button type="button" className={`gx-btn ${mode === "register" ? "" : "sec"}`} aria-pressed={mode === "register"} data-testid="auth-mode-register" onClick={() => setMode("register")}>{t("register")}</button>
            </div>
            <label className="gx-field">{t("email")}
              <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} data-testid="email" /></label>
            <label className="gx-field">{t("password")}
              <input type="password" required autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(e) => setPassword(e.target.value)} data-testid="password" /></label>
            {mode === "register" && <label className="gx-field">{t("bizName")}
              <input type="text" autoComplete="organization" value={tenant} onChange={(e) => setTenant(e.target.value)} data-testid="tenant-name" /></label>}
            {authErr && <p className="gx-err" role="alert" data-testid="text-auth-error">{authErr}</p>}
            <div className="gx-row">
              <button className="gx-btn" type="submit" disabled={authBusy} data-testid="auth-submit">
                {authBusy ? t("working") : mode === "login" ? t("loginBtn") : t("registerBtn")}</button>
              <button type="button" className="gx-btn sec" data-testid="forgot" aria-expanded={recover} onClick={() => setRecover(!recover)}>{t("forgot")}</button>
            </div>
            {recover && <div className="gx-warn" role="status"><b>{t("recoverTitle")}.</b> {t("forgotHelp")}</div>}
          </form>
        </section>
        <section className="gx-card">
          {stageCardsPreview()}
          <div className="gx-row">
            <a className="gx-btn sec" href={guestHref} data-testid="link-guest-draft">{t("guest")}</a>
            <a className="gx-btn sec" href={base} data-testid="link-workspace">{t("workspace")}</a>
          </div>
        </section>
      </div>
    </>
  );
  function stageCardsPreview() {
    return (
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {STAGES.map((s) => <li key={s} style={{ marginBottom: 12 }}><b className="serif">{stageLabel(s)}</b><span className="gx-help">{stageBlurb(s)}</span></li>)}
      </ul>
    );
  }

  const startPanel = pendingStage && (
    <section className="gx-card" aria-labelledby="start-h" data-testid="panel-start">
      <h2 id="start-h">{t("startingH")}: {stageLabel(pendingStage)}</h2>
      <p>{t("whatSaved")}</p><p>{t("next")}</p><p className="gx-help">{t("reuse")}</p>
      <label className="gx-check">
        <input type="checkbox" checked={consent} onChange={(e) => { setConsent(e.target.checked); setStartErr(""); }} data-testid="consent" />
        <span>{t("consent")}</span></label>
      {startErr && <p className="gx-err" role="alert" data-testid="text-start-error">{startErr}</p>}
      <div className="gx-row">
        <button type="button" className="gx-btn" data-testid="start" disabled={busy} onClick={doStart}>{busy ? t("working") : t("startBtn")}</button>
      </div>
    </section>
  );

  const questionView = active && field && (
    <section className="gx-card" aria-labelledby="q-h">
      <span className="gx-badge">{stageLabel(active.stage)}</span>
      <div className="gx-bar" role="progressbar" aria-valuemin={0} aria-valuemax={active.question_count} aria-valuenow={active.answered_count} aria-label={t("progress")}>
        <i style={{ width: "100%", transform: `scaleX(${active.answered_count / active.question_count})` }} /></div>
      <p className="gx-help">{t("qOf")} {ORDER.indexOf(field) + 1} {t("of")} {active.question_count} · {active.answered_count} {t("progress")}</p>
      <form onSubmit={doContinue} noValidate>
        <h2 id="q-h" className="gx-q" tabIndex={-1} ref={headRef}>{t(QKEY[field][0])}</h2>
        <label className="gx-field" htmlFor="q-input"><span className="gx-help">{t(QKEY[field][1])}</span></label>
        {field === "goal" ? (
          <>
            <textarea id="q-input" data-testid="question-input" disabled={busy} lang={lang} maxLength={1200} value={draft} onChange={(e) => { setDraft(e.target.value); setFieldErr(""); }}
              aria-invalid={!!fieldErr} aria-describedby="q-err q-count" />
            <small id="q-count" className="gx-help">{draft.trim().length} / 1200 {t("chars")}</small>
          </>
        ) : (
          <select id="q-input" data-testid="question-input" value={draft} onChange={(e) => { setDraft(e.target.value); setFieldErr(""); }}
            aria-invalid={!!fieldErr} aria-describedby="q-err" disabled={busy || !catalog}>
            <option value="">{t("choose")}</option>
            {field === "state" && catalog?.states.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
            {field === "entity_type" && catalog?.entity_types.map((v) => <option key={v} value={v}>{choiceName(v)}</option>)}
            {field === "ownership_type" && catalog?.ownership_types.map((v) => <option key={v} value={v}>{choiceName(v)}</option>)}
          </select>
        )}
        {!catalog && catErr && <p className="gx-err" role="alert">{catErr} <button type="button" className="gx-btn sec" onClick={loadCatalog}>{t("retry")}</button></p>}
        <div id="q-err" aria-live="assertive">
          <p className="gx-err" tabIndex={-1} ref={errRef} data-testid="text-question-error">
            {fieldErr || saveErr || (conflict ? t("conflict") : "")}</p>
        </div>
        {conflict && <div className="gx-row"><button type="button" className="gx-btn sec" data-testid="reload" disabled={busy} onClick={reload}>{t("reload")}</button></div>}

        <div className="gx-row">
          <button className="gx-btn" type="submit" data-testid="continue" disabled={busy || conflict}>{busy ? t("saving") : t("saveContinue")}</button>
          {editing && <button type="button" className="gx-btn sec" onClick={() => { setEditing(null); setView("mission"); draftFor.current = ""; }}>{t("cancelEdit")}</button>}
          {!editing && <button type="button" className="gx-btn sec" data-testid="button-back" onClick={() => { setView("mission"); draftFor.current = ""; }}>{t("back")}</button>}
        </div>
        <p className="gx-help" role="status" aria-live="polite" aria-label={t("saveStatus")} data-testid="status-save">{status}</p>
        <p className="gx-help">{t("whatSaved")}</p>

        <fieldset style={{ border: "2px dashed var(--line)", borderRadius: 8, marginTop: 14 }}>
          <legend>{t("voice")}</legend>
          {field === "goal" && SRC ? (
            <>
              <label className="gx-check"><input type="checkbox" checked={voiceConsent} onChange={(e) => setVoiceConsent(e.target.checked)} data-testid="voice-consent" /><span>{t("voiceConsent")}</span></label>
              <div className="gx-row">
                <button type="button" className="gx-btn sec" data-testid="voice-toggle" disabled={!voiceConsent} onClick={toggleListen}>{listening ? t("voiceStop") : t("voiceStart")}</button>
                <span aria-live="polite">{listening ? t("voiceListening") : ""}</span>
              </div>
              <p className="gx-help">{t("voiceNote")}</p>
              {voiceErr && <p className="gx-err" role="alert">{t("voiceDenied")}</p>}
            </>
          ) : <p className="gx-help" data-testid="text-voice-unsupported">{field === "goal" ? t("voiceUnsupported") : t("voiceUnsupported")}</p>}
          {speechOk && localVoice ? (
            <div className="gx-row"><button type="button" className="gx-btn sec" data-testid="speak" onClick={toggleSpeak}>{speaking ? t("speakStop") : t("speak")}</button></div>
          ) : <p className="gx-help" data-testid="text-speak-none">{t("speakNone")}</p>}
        </fieldset>
      </form>
    </section>
  );

  const planView = (j: Journey) => (
    <section className="gx-card" aria-labelledby="plan-h" data-testid="section-plan">
      <span className="gx-badge">{j.status === "PREPARED" ? t("prepared") : t("inProgress")}</span>
      <h2 id="plan-h" style={{ marginTop: 10 }}>{stageLabel(j.stage)}</h2>
      {j.status === "PREPARED" && <p className="gx-warn">{t("preparedNote")}</p>}
      <p className="gx-ok" data-testid="text-saved-label">{t("savedLabel")} {t("updated")}: {new Date(j.updated_at).toLocaleString(lang)}</p>
      <h3 style={{ marginTop: 18 }}>{t("yourAnswers")}</h3>
      <dl>
        {ORDER.map((q) => (
          <div key={q}><dt>{t(q)}</dt>
            <dd>{display(q, j) || "-"} {j.answers[q] && <button type="button" className="gx-btn sec" style={{ minHeight: 44, marginLeft: 8 }} data-testid={`edit-${q}`}
              onClick={() => { setActiveId(j.id); setEditing(q); setView("question"); draftFor.current = ""; }}>{t("edit")}</button>}</dd></div>
        ))}
      </dl>
      <p className="gx-help">{t("dataNote")}</p>
      {j.next_question && <div className="gx-row"><button type="button" className="gx-btn" onClick={() => { setActiveId(j.id); setEditing(null); setView("question"); draftFor.current = ""; }}>{t("resume")}</button></div>}
      {j.plan && (
        <>
          <h3 style={{ marginTop: 22 }}>{t("checklist")}</h3>
          <p className="gx-help">{t("poweredBy")}</p>
          {lang === "es" && <p className="gx-warn" role="note" data-testid="text-translation-notice">{t("planEnglish")}</p>}
          <ol style={{ listStyle: "none", padding: 0 }}>
            {j.plan.steps.map((s) => (
              <li className="gx-step" key={s.order} data-testid={`step-${s.order}`}>
                <b className="serif">{s.order}. {s.title}</b>
                <div>
                  <span className="gx-tag">{t("workflow")}: {t("notStarted")}</span>
                  {s.professional_review && <span className="gx-tag">{t("prof")}</span>}
                  {detail === "details" && <span className="gx-tag">{pretty(s.status)} · {s.workflow_status}</span>}
                </div>
                <p style={{ margin: "6px 0" }}>{s.next_action}</p>
                {detail === "details" && s.official_url && <a href={s.official_url} target="_blank" rel="noopener noreferrer">{t("official")}</a>}
              </li>
            ))}
          </ol>
          {detail === "details" && j.plan.approvals.length > 0 && <><h3>{t("approvals")}</h3><ul>{j.plan.approvals.map((a) => <li key={a}>{a}</li>)}</ul></>}
          <h3 style={{ marginTop: 18 }}>{t("costs")}</h3><p data-testid="text-costs">{t("costsText")}</p>
          <h3>{t("nextSteps")}</h3><p>{t("nextStepsText")}</p>
          <div className="gx-row"><button type="button" className="gx-btn" data-testid="download" onClick={() => download(j)}>{t("download")}</button></div>
        </>
      )}
    </section>
  );

  const mission = (
    <>
      <section className="gx-hero" style={{ paddingBottom: 0 }}>
        <h1 data-testid="mission-control">{t("missionH")}</h1><p>{t("missionP")}</p>
        <p className="gx-help">{t("signedAs")} {account?.email}</p>
      </section>
      {stageCards}
      {startPanel}
      {!pendingStage && journeys.length === 0 && <p className="gx-card" data-testid="text-empty">{t("noJourneys")}</p>}
      {!pendingStage && active && planView(active)}
      <div className="gx-row">
        <a className="gx-btn sec" href={guestHref} data-testid="link-guest-draft">{t("guest")}</a>
        <a className="gx-btn sec" href={base} data-testid="link-workspace">{t("workspace")}</a>
      </div>
    </>
  );

  let body;
  if (initErr) body = (
    <section className="gx-card"><p className="gx-err" role="alert" data-testid="text-init-error">{t("initErr")} {initErr}</p>
      <button type="button" className="gx-btn" data-testid="retry" onClick={() => { if (account) void loadJourneys(); else boot(); }}>{t("retry")}</button></section>
  );
  else if (account === undefined || (account && !jLoaded)) body = <div className="gx-skel" role="status" aria-busy="true" aria-label={t("loading")} />;
  else if (!account) body = authView;
  else body = view === "question" && questionView ? questionView : mission;

  return (
    <div className="gx" lang={lang} data-testid="guided-root">
      <div className="gx-wrap">{header}<main>
        {prefMsg && <p className="gx-help" role="status" data-testid="text-pref">{prefMsg}</p>}
        {conflict && view === "mission" && <p role="alert" className="gx-warn">{t("conflict")} <button type="button" className="gx-btn sec" data-testid="reload" disabled={busy} onClick={reload}>{t("reload")}</button></p>}
        {body}
      </main></div>
    </div>
  );
}
