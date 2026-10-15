import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "./journey-api";
import type { Journey, Language } from "./journey-api";
import { decideConsultationPrivacy, fetchConsultation, sendConsultation } from "./consultation-api";
import type { ConsultationState } from "./consultation-api";
import { consultationText } from "./consultation-i18n";
import { isRtl } from "./journey-api";
import BusinessPath from "./BusinessPath";
import PrivacyControls from "./PrivacyControls";
import type { PrivacyAction } from "./PrivacyControls";
import { privacyText } from "./privacy-i18n";



interface Props { journey: Journey; lang: Language; accountId: string; onRefreshJourney: () => Promise<void> | void; onUnauthorized: () => void; stateName: (c?: string) => string }

function Inner({ journey, lang, accountId, onUnauthorized, onRefreshJourney, stateName }: Props) {
  const t = consultationText(lang);
  const [data, setData] = useState<ConsultationState | null>(null);
  const [loadErr, setLoadErr] = useState("");
  const [draft, setDraft] = useState("");
  const [ok, setOk] = useState(false);
  const [err, setErr] = useState("");
  const [conflict, setConflict] = useState(false);
  const [busy, setBusy] = useState(false);
  const [stale, setStale] = useState(false);
  const [refreshErr, setRefreshErr] = useState("");
  const [conflicts, setConflicts] = useState(0);
  const [privMsg, setPrivMsg] = useState("");
  const [privErr, setPrivErr] = useState("");
  const alive = useRef(true);
  const requestSerial = useRef(0);
  const unauth = useRef(onUnauthorized); unauth.current = onUnauthorized;
  const jv = useRef(journey); jv.current = journey;
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);

  const load = useCallback(async (): Promise<boolean> => {
    const serial = ++requestSerial.current;
    try {
      const r = await fetchConsultation(jv.current.id);
      if (!alive.current || serial !== requestSerial.current) return false;
      setData(r); setLoadErr(""); return true;
    } catch (e) {
      if (!alive.current || serial !== requestSerial.current) return false;
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) { unauth.current(); return false; }
      setLoadErr(e instanceof Error ? e.message : "Error");
      return false;
    }
  }, []);
  useEffect(() => { void load(); }, [load]);
  const busyRef = useRef(false);
  useEffect(() => {
    const f = () => { if (!busyRef.current && document.visibilityState === "visible") void load(); };
    window.addEventListener("focus", f); document.addEventListener("visibilitychange", f);
    return () => { window.removeEventListener("focus", f); document.removeEventListener("visibilitychange", f); };
  }, [load]);
  const refreshNow = async () => {
    setBusy(true); busyRef.current = true; setRefreshErr("");
    const okk = await load();
    if (!alive.current) return;
    if (okk) { setStale(false); setErr(""); } else setRefreshErr(t.refreshFail);
    setBusy(false); busyRef.current = false;
  };

  const c = data?.consultation ?? null;
  const max = data?.availability.max_turns ?? 8;
  const full = (c?.turns.length ?? 0) >= max;
  const last = c?.turns[c.turns.length - 1]?.answer;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busyRef.current || busy || !data || stale) return;
    if (data.privacy.status === "REVOKED" || data.privacy.status === "DELETED") return;
    const m = draft.trim();
    if (m.length < 5 || m.length > 1200) { setErr(t.len); return; }
    if (!ok) { setErr(t.needConsent); return; }
    ++requestSerial.current; // A late focus GET must not replace a successful mutation.
    setBusy(true); busyRef.current = true; setErr(""); setConflict(false); setRefreshErr("");
    try {
      const r = await sendConsultation(journey, c?.version ?? 0, m, data.privacy.version);
      if (!alive.current) return;
      setData((d) => d && { ...d, consultation: r }); setDraft(""); setOk(false); setConflicts(0);
    } catch (x) {
      if (!alive.current) return;
      if (x instanceof ApiError && (x.status === 401 || x.status === 403)) { unauth.current(); return; }
      if (x instanceof ApiError && x.status === 409) {
        setConflict(true); setErr(t.conflict); setStale(true); setConflicts((n) => n + 1);
        const okk = await load();
        if (!alive.current) return;
        if (okk) setStale(false); else setRefreshErr(t.refreshFail);
      }
      else setErr(`${t.sendErr} ${x instanceof Error ? x.message : ""}`);
    } finally { busyRef.current = false; if (alive.current) setBusy(false); }
  };

  const runPrivacy = async (action: PrivacyAction): Promise<boolean> => {
    if (busyRef.current || !data) return false;
    const pt = privacyText[lang];
    ++requestSerial.current; // Invalidate any in-flight GET so it cannot overwrite the result.
    setBusy(true); busyRef.current = true; setPrivMsg(""); setPrivErr("");
    try {
      await decideConsultationPrivacy(journey.id, data, action);
      if (!alive.current) return true;
      if (action !== "grant") { setDraft(""); setOk(false); }
      setErr(""); setStale(false);
      const fresh = await load();
      if (!alive.current) return true;
      if (fresh) setPrivMsg(pt.done); else setRefreshErr(t.refreshFail);
      return true;
    } catch (x) {
      if (!alive.current) return false;
      if (x instanceof ApiError && (x.status === 401 || x.status === 403)) { unauth.current(); return false; }
      if (x instanceof ApiError && x.status === 409) { setPrivErr(pt.conflict); await load(); }
      else setPrivErr(`${pt.fail} ${x instanceof Error ? x.message : ""}`);
      return false;
    } finally { busyRef.current = false; if (alive.current) setBusy(false); }
  };
  const blocked = data?.privacy.status === "REVOKED" || data?.privacy.status === "DELETED";

  const showDetail = journey.detail_mode === "details";
  void accountId;
  return (
    <section className="gx-card" aria-labelledby="cons-h" data-testid="section-consultation" lang={lang} dir={isRtl(lang) ? "rtl" : "ltr"}>
      <span className="gx-badge" data-testid="text-consultation-badge">{t.badge}</span>
      <h2 id="cons-h" style={{ marginTop: 10 }}>{t.h}</h2>
      <p className="gx-warn" role="note" data-testid="text-consultation-notice">{t.notice}</p>
      {!data && !loadErr && <div className="gx-skel" role="status" aria-busy="true" aria-label={t.loading} />}
      {loadErr && !data && <p className="gx-err" role="alert">{t.loadErr} {loadErr} <button type="button" className="gx-btn sec" data-testid="consultation-retry" onClick={() => { setLoadErr(""); void load(); }}>{t.retry}</button></p>}
      {data && (
        <>
          {c?.context_stale && <p className="gx-warn" role="alert" data-testid="text-consultation-stale">{t.stale}</p>}
          <h3>{t.yours}</h3>
          <p className="gx-help">{t.yoursNote}</p>
          <ul>
            {(["state", "entity_type", "ownership_type", "goal"] as const).map((q) => journey.answers[q] ? <li key={q}><b>{t[q]}:</b> {q === "state" ? stateName(journey.answers[q]) : journey.answers[q]}</li> : null)}
          </ul>
          {c && c.turns.length > 0 ? (
            <ol style={{ listStyle: "none", padding: 0 }} aria-live="polite">
              {c.turns.map((turn, i) => (
                <li className="gx-step" key={i} data-testid={`consultation-turn-${i}`}>
                  <b className="serif">{t.turn} {i + 1}: {turn.question}</b>
                  <p>{turn.answer.summary}</p>
                  <h4>{t.roadmap}</h4>
                  <ol>{turn.answer.roadmap.map((r, k) => <li key={k}><b>{r.title}</b>{(showDetail || i === c.turns.length - 1) && <span> - {r.explanation}</span>}</li>)}</ol>
                  {showDetail && turn.answer.assumptions.length > 0 && <><h4>{t.assumptions}</h4><ul>{turn.answer.assumptions.map((a, k) => <li key={k}>{a}</li>)}</ul></>}
                  {turn.answer.professional_review.length > 0 && <><h4>{t.review}</h4><ul>{turn.answer.professional_review.map((a, k) => <li key={k}>{a}</li>)}</ul></>}
                </li>
              ))}
            </ol>
          ) : <p className="gx-help" data-testid="text-consultation-empty">{t.none}</p>}
          {!showDetail && last && last.assumptions.length > 0 && <><h4>{t.assumptions}</h4><ul>{last.assumptions.map((a, k) => <li key={k}>{a}</li>)}</ul></>}
          <p className="gx-warn" role="note">{t.reviewNote}</p>
          {c && last && !blocked && !stale && !c.context_stale && (
            <BusinessPath journey={journey} lang={lang} consultation={c} privacy={data.privacy} onUnauthorized={onUnauthorized} onStale={load} />
          )}
          {last && !full && (
            <div data-testid="consultation-next">
              <h4>{t.next}</h4><p>{last.next_question}</p>
              <button type="button" className="gx-btn sec" disabled={busy} onClick={() => setDraft(last.next_question)}>{t.useNext}</button>
            </div>
          )}
          {data.resources.length > 0 && (
            <><h3>{t.official}</h3><p className="gx-help">{t.officialNote}</p>
              <ul>{data.resources.map((r) => <li key={r.id}><a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a></li>)}</ul></>
          )}
          {blocked ? null : full ? <p className="gx-warn" role="status" data-testid="text-consultation-max">{t.max}</p> : (
            <form onSubmit={submit} noValidate>
              <label className="gx-field" htmlFor="cons-q">{t.ask}</label>
              <p className="gx-help" id="cons-hint">{t.hint}</p>
              <textarea id="cons-q" lang={lang} maxLength={1200} disabled={busy} value={draft} data-testid="consultation-input"
                onChange={(e) => { setDraft(e.target.value); setErr(""); }} aria-invalid={!!err && !conflict} aria-describedby="cons-hint cons-err" />
              <small className="gx-help">{draft.trim().length} / 1200</small>
              <label className="gx-check"><input type="checkbox" checked={ok} onChange={(e) => { setOk(e.target.checked); setErr(""); }} data-testid="consultation-consent" /><span>{t.consent}</span></label>
              <div id="cons-err" role="alert">{err && <p className="gx-err" data-testid="text-consultation-error">{err}</p>}</div>
              {refreshErr && <p className="gx-err" role="alert" data-testid="text-consultation-refresh-error">{refreshErr} <button type="button" className="gx-btn sec" disabled={busy} data-testid="consultation-refresh" onClick={() => void refreshNow()}>{busy ? t.refreshing : t.refresh}</button></p>}
              {conflicts >= 2 && !stale && <p className="gx-warn" role="alert" data-testid="text-consultation-persist">{t.persist} <button type="button" className="gx-btn sec" onClick={() => void onRefreshJourney()}>{t.refreshJourney}</button></p>}
              <div className="gx-row"><button type="submit" className="gx-btn" disabled={busy || stale} data-testid="consultation-send">{busy ? t.sending : t.send}</button></div>
            </form>
          )}
          <PrivacyControls lang={lang} data={data} busy={busy} message={privMsg} error={privErr} onRun={runPrivacy} />
        </>
      )}
    </section>
  );
}

export default function ConsultationPanel(p: Props) {
  return <Inner key={`${p.accountId}:${p.journey.id}:${p.journey.version}:${p.lang}`} {...p} />;
}
