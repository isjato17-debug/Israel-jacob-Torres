import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./journey-api";
import type { Journey, Language } from "./journey-api";
import type { Consultation, ConsultationState } from "./consultation-api";
import { createBusinessPath, getBusinessPath } from "./ideas-api";
import type { BusinessPath as BP } from "./ideas-api";

const base = import.meta.env.BASE_URL;
const EN = {
  h: "Turn this into a business path", p: "Your saved goal is reused. Only the budget is needed to prepare three financial plans and two business strategies.",
  concept: "Concept (from your saved goal)", state: "State", budget: "Budget in dollars", budgetHint: "Whole dollars or up to two decimals, for example 3000 or 3000.50.",
  bad: "Enter a budget of 0 or more with up to two decimals.", consent: "I agree B.I.G. may copy this saved goal, my state and this budget into a separate private idea. Deleting the consultation later does not delete the independently saved idea or project.",
  needConsent: "Tick the copy consent box first.", prepare: "Prepare plans", preparing: "Preparing...", compare: "Compare plans and strategies", go: "Go to idea", goProject: "Open idea and project",
  linked: "This goal already has a saved idea.", loading: "Loading...", loadErr: "Could not load the business path.", retry: "Retry",
  short: "Your saved goal is too short. Update your goal in the intake first.", s409: "Your consultation or intake changed. We refreshed it; review it, then press Prepare plans again. Nothing was resent.",
  s401: "Your session has expired. Sign in again.", fail: "Not prepared.", note: "Deterministic calculations, not AI. Nothing is filed, sent or paid.",
};
const ES: typeof EN = {
  h: "Convierta esto en un camino de negocio", p: "Se reutiliza su meta guardada. Solo se necesita el presupuesto para preparar tres planes financieros y dos estrategias de negocio.",
  concept: "Concepto (de su meta guardada)", state: "Estado", budget: "Presupuesto en dólares", budgetHint: "Dólares enteros o hasta dos decimales, por ejemplo 3000 o 3000.50.",
  bad: "Escriba un presupuesto de 0 o más con hasta dos decimales.", consent: "Acepto que B.I.G. copie esta meta guardada, mi estado y este presupuesto a una idea privada separada. Borrar la consulta después no borra la idea ni el proyecto guardados de forma independiente.",
  needConsent: "Marque primero el consentimiento de copia.", prepare: "Preparar planes", preparing: "Preparando...", compare: "Comparar planes y estrategias", go: "Ir a la idea", goProject: "Abrir idea y proyecto",
  linked: "Esta meta ya tiene una idea guardada.", loading: "Cargando...", loadErr: "No se pudo cargar el camino de negocio.", retry: "Reintentar",
  short: "Su meta guardada es muy corta. Actualice su meta en el formulario primero.", s409: "Su consulta o información cambió. La actualizamos; revísela y pulse Preparar planes otra vez. Nada se reenvió.",
  s401: "Su sesión expiró. Inicie sesión de nuevo.", fail: "No se preparó.", note: "Cálculos determinísticos, no IA. Nada se presenta, envía ni paga.",
};
const TX = (l: Language) => (l === "es" ? ES : EN);
export const parseBudgetCents = (v: string): number | null => {
  const m = /^(\d{1,9})(?:\.(\d{1,2}))?$/.exec(v.trim());
  if (!m) return null;
  const c = Number(m[1]) * 100 + Number((m[2] ?? "").padEnd(2, "0") || "0");
  return Number.isSafeInteger(c) && c <= 100_000_000 ? c : null;
};

interface Props { journey: Journey; lang: Language; consultation: Consultation; privacy: ConsultationState["privacy"]; onUnauthorized: () => void; onStale: () => Promise<unknown> | void }

export default function BusinessPath({ journey, lang, consultation, privacy, onUnauthorized, onStale }: Props) {
  const t = TX(lang);
  const [path, setPath] = useState<BP | null>(null);
  const [loadErr, setLoadErr] = useState("");
  const [budget, setBudget] = useState("");
  const [ok, setOk] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [ideaId, setIdeaId] = useState<string | null>(null);
  const [hasProject, setHasProject] = useState(false);
  const alive = useRef(true); const busyRef = useRef(false); const serial = useRef(0);
  const un = useRef(onUnauthorized); un.current = onUnauthorized;
  const stale = useRef(onStale); stale.current = onStale;
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);

  const load = useCallback(async () => {
    const s = ++serial.current;
    try {
      const r = await getBusinessPath(journey.id);
      if (!alive.current || s !== serial.current) return;
      setPath(r); setLoadErr("");
      if (r.idea) { setIdeaId(r.idea.id); setHasProject(!!r.idea.project_id); }
    } catch (e) {
      if (!alive.current || s !== serial.current) return;
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) { un.current(); return; }
      setLoadErr(e instanceof Error ? e.message : "Error");
    }
  }, [journey.id]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    const f = () => { if (!busyRef.current && document.visibilityState === "visible") void load(); };
    window.addEventListener("focus", f); document.addEventListener("visibilitychange", f);
    return () => { window.removeEventListener("focus", f); document.removeEventListener("visibilitychange", f); };
  }, [load]);

  const cents = parseBudgetCents(budget);
  const concept = path?.concept ?? journey.answers.goal ?? "";
  const submit = async () => {
    if (busyRef.current || !path) return;
    if (cents === null) { setErr(t.bad); return; }
    if (!ok) { setErr(t.needConsent); return; }
    ++serial.current; busyRef.current = true; setBusy(true); setErr("");
    try {
      const i = await createBusinessPath(journey.id, { expected_version: journey.version, consultation_version: consultation.version, privacy_version: privacy.version, budget_cents: cents });
      if (!alive.current) return;
      setIdeaId(i.id); setHasProject(!!i.project_id); setOk(false);
    } catch (x) {
      if (!alive.current) return;
      if (x instanceof ApiError && (x.status === 401 || x.status === 403)) { un.current(); return; }
      if (x instanceof ApiError && x.status === 409) { setErr(t.s409); await stale.current(); }
      else if (x instanceof ApiError && x.status === 422) setErr(`${t.short} ${x.message}`);
      else setErr(`${t.fail} ${x instanceof Error ? x.message : ""}`);
    } finally { busyRef.current = false; if (alive.current) setBusy(false); }
  };

  return (
    <section className="gx-step" aria-labelledby="bp-h" data-testid="section-business-path">
      <h3 id="bp-h">{t.h}</h3>
      <p className="gx-help">{t.p}</p>
      {!path && !loadErr && <div className="gx-skel" role="status" aria-busy="true" aria-label={t.loading} />}
      {loadErr && !path && <p className="gx-err" role="alert">{t.loadErr} {loadErr} <button type="button" className="gx-btn sec" data-testid="business-path-retry" onClick={() => { setLoadErr(""); void load(); }}>{t.retry}</button></p>}
      {path && <>
        <dl>
          <dt>{t.concept}</dt><dd data-testid="text-path-concept">{concept}</dd>
          <dt>{t.state}</dt><dd data-testid="text-path-state">{path.jurisdiction}</dd>
        </dl>
        {ideaId ? <>
          <p className="gx-ok" role="status" data-testid="text-path-linked">{t.linked}</p>
          <div className="gx-row"><a className="gx-btn" data-testid="link-go-to-idea" href={`${base}next/ideas/?idea=${encodeURIComponent(ideaId)}`}>{hasProject ? t.goProject : t.go}</a></div>
        </> : <>
          <label className="gx-field" htmlFor="bp-budget">{t.budget}</label>
          <p className="gx-help" id="bp-hint">{t.budgetHint}</p>
          <input id="bp-budget" className="iv-in" inputMode="decimal" autoComplete="off" disabled={busy} value={budget} data-testid="input-path-budget"
            aria-invalid={!!budget && cents === null} aria-describedby="bp-hint bp-err" onChange={(e) => { setBudget(e.target.value); setErr(""); }} />
          {budget.trim() !== "" && cents === null && <p className="gx-err" role="alert">{t.bad}</p>}
          <label className="gx-check"><input type="checkbox" checked={ok} disabled={busy} onChange={(e) => { setOk(e.target.checked); setErr(""); }} data-testid="consent-path-copy" /><span>{t.consent}</span></label>
          <div id="bp-err" role="alert">{err && <p className="gx-err" data-testid="text-path-error">{err}</p>}</div>
          <p className="gx-help">{t.note}</p>
          <div className="gx-row"><button type="button" className="gx-btn" disabled={busy || cents === null || !ok} data-testid="button-path-prepare" onClick={() => void submit()}>{busy ? t.preparing : t.prepare}</button></div>
        </>}
      </>}
    </section>
  );
}
