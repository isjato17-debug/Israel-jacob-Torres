import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError, getSession, signIn, signOut } from "./journey-api";
import type { Account } from "./journey-api";
import { createIdea, editIdea, getIdea, getProject, ideaAction, listIdeas, listProjects, developIdea, selectPlan, setProjectTask } from "./ideas-api";
import type { BusinessPlan, Idea, IdeaInput, Project } from "./ideas-api";
import ProjectExecution from "./ProjectExecution";
import OwnerAccessLink from "./OwnerAccessLink";
import "./guided.css";
import "./ideas.css";

const base = import.meta.env.BASE_URL;
type L = "en" | "es";
const T = {
  en: { title: "Idea Vault", sub: "Private business ideas, three plans each, one project when you are ready.", signin: "Sign in", email: "Email", password: "Password", signout: "Sign out",
    notice: "Controls are available in English and Spanish; saved plan assessments currently remain in English. All six existing languages remain available in the guided consultation.",
    det: "Plans are deterministic calculations from your inputs, not generative AI. No live providers, payments or filings are used.",
    ideas: "Your ideas", none: "No ideas yet. Save your first one below.", newIdea: "New idea", editIdea: "Edit idea", concept: "Concept (at least 5 characters)", industry: "Industry (optional)",
    juris: "State code, for example NY", budget: "Budget in dollars", goals: "Goals (optional)", prefs: "Preferences (optional)", notes: "Notes (optional)", assum: "Assumptions (optional)",
    consent: "I agree B.I.G. may save this idea privately in my account.", save: "Save idea", saveCh: "Save changes", cancel: "Cancel", saving: "Saving...", saved: "Saved.",
    open: "Open", archive: "Archive", restore: "Restore", gen: "Generate three plans", regen: "Regenerate plans", select: "Select this plan", selected: "Selected", develop: "Develop into Business Project",
    showArch: "Show archived", startup: "Startup costs", monthly: "Monthly costs", gap: "Funding gap", fund: "Funding required", avail: "Available budget", reserve: "Reserve", rev: "Revenue scenarios", assumpH: "Assumptions",
    fixed: "fixed overhead", variable: "Estimated variable delivery costs at base revenue", totalMonthly: "Estimated total monthly expenses", marketing: "Marketing approach", milestones: "Launch milestones",
    reqs: "Official requirements (review needed)", pros: "Professional help categories", total: "Total", risks: "Risks", proj: "Business Projects", checklist: "Initial checklist", todo: "To do", done: "Done",
    vConcept: "Enter a concept of at least 5 characters.", vState: "Enter a two-letter state code.", vBudget: "Enter a dollar amount from 0 to 1,000,000 with up to two decimals.", s401: "Your session has expired. Sign in again; your draft is kept on this page.",
    s409: "This idea changed elsewhere. Reload the latest version, then repeat your action. Nothing was replayed.", reload: "Reload latest", back: "Back to vault", loading: "Loading", retry: "Retry",
    devNote: "This idea is developed. Editing is blocked; its project stays linked.", rec: "Recommended", status: "Status", open2: "Open project", compare: "Compare plans", breakeven: "Break-even revenue", profit: "Operating profit per month", revenue: "Revenue per month", mybiz: "My Businesses", reviewNav: "Review Decisions", primary: "Primary", heroH: "What would you like to accomplish?", firstSave: "Save your first idea", history: "Saved history", created: "Created", updated: "Updated", reviewH: "Review Decisions", reviewP: "Saved plans waiting for you to select a plan or create the project. Nothing is approved or submitted for you.", reviewNone: "No saved plans are waiting for a decision.", readyDevelop: "Selected, ready to develop", needSelect: "Choose one of three plans", more: "More: advanced features", guided: "Ask B.I.G. (guided consultation)", guest: "Guest draft", partners: "Partner Network", owner: "Owner growth", ws: "Workspace" },
  es: { title: "Bóveda de ideas", sub: "Ideas privadas, tres planes cada una, un proyecto cuando esté listo.", signin: "Iniciar sesión", email: "Correo", password: "Contraseña", signout: "Cerrar sesión",
    notice: "Los controles están en inglés y español; los análisis de los planes guardados siguen en inglés. Los seis idiomas existentes siguen disponibles en la consulta guiada.",
    det: "Los planes son cálculos determinísticos con sus datos, no IA generativa. No se usan proveedores, pagos ni trámites reales.",
    fixed: "gastos fijos", variable: "Costos variables estimados con ingresos base", totalMonthly: "Gastos mensuales totales estimados", marketing: "Enfoque de marketing", milestones: "Hitos de lanzamiento",
    ideas: "Sus ideas", none: "Aún no hay ideas. Guarde la primera abajo.", newIdea: "Nueva idea", editIdea: "Editar idea", concept: "Concepto (mínimo 5 caracteres)", industry: "Industria (opcional)",
    juris: "Código de estado, por ejemplo NY", budget: "Presupuesto en dólares", goals: "Metas (opcional)", prefs: "Preferencias (opcional)", notes: "Notas (opcional)", assum: "Supuestos (opcional)",
    consent: "Acepto que B.I.G. guarde esta idea de forma privada en mi cuenta.", save: "Guardar idea", saveCh: "Guardar cambios", cancel: "Cancelar", saving: "Guardando...", saved: "Guardado.",
    open: "Abrir", archive: "Archivar", restore: "Restaurar", gen: "Generar tres planes", regen: "Regenerar planes", select: "Elegir este plan", selected: "Elegido", develop: "Convertir en Proyecto de negocio",
    showArch: "Mostrar archivadas", startup: "Costos de inicio", monthly: "Costos mensuales", gap: "Brecha de fondos", fund: "Fondos requeridos", avail: "Presupuesto disponible", reserve: "Reserva", rev: "Escenarios de ingresos", assumpH: "Supuestos",
    reqs: "Requisitos oficiales (requieren revisión)", pros: "Categorías de ayuda profesional", total: "Total", risks: "Riesgos", proj: "Proyectos de negocio", checklist: "Lista inicial", todo: "Pendiente", done: "Hecho",
    vConcept: "Escriba un concepto de al menos 5 caracteres.", vState: "Escriba un código de estado de dos letras.", vBudget: "Escriba un monto de 0 a 1,000,000 dólares con hasta dos decimales.", s401: "Su sesión expiró. Inicie sesión de nuevo; su borrador se conserva en esta página.",
    s409: "Esta idea cambió en otro lugar. Recargue la última versión y repita la acción. Nada se repitió automáticamente.", reload: "Recargar", back: "Volver a la bóveda", loading: "Cargando", retry: "Reintentar",
    devNote: "Esta idea ya se desarrolló. La edición está bloqueada; el proyecto sigue vinculado.", rec: "Recomendado", status: "Estado", open2: "Abrir proyecto", compare: "Comparar planes", breakeven: "Ingreso de equilibrio", profit: "Utilidad operativa mensual", revenue: "Ingreso mensual", mybiz: "Mis negocios", reviewNav: "Revisar decisiones", primary: "Principal", heroH: "¿Qué le gustaría lograr?", firstSave: "Guarde su primera idea", history: "Historial guardado", created: "Creada", updated: "Actualizada", reviewH: "Revisar decisiones", reviewP: "Planes guardados que esperan que elija un plan o cree el proyecto. Nada se aprueba ni se envía por usted.", reviewNone: "No hay planes guardados esperando una decisión.", readyDevelop: "Elegido, listo para desarrollar", needSelect: "Elija uno de tres planes", more: "Más: funciones avanzadas", guided: "Pregunte a B.I.G. (consulta guiada)", guest: "Borrador de invitado", partners: "Red de socios", owner: "Crecimiento", ws: "Espacio de trabajo" },
} as const;
type K = keyof typeof T.en;

const usd = (c: number) => (c < 0 ? "-" : "") + "$" + (Math.abs(c) / 100).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export function dollarsToCents(v: string): number | null {
  const m = /^\$?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?$/.exec(v.trim());
  if (!m) return null;
  const c = Number(m[1].replace(/,/g, "")) * 100 + Number((m[2] ?? "").padEnd(2, "0") || "0");
  return c >= 0 && c <= 10_000_000_000 ? c : null;
}
const centsToField = (c: number) => { const w = Math.floor(c / 100), r = c % 100; return r ? `${w}.${String(r).padStart(2, "0")}` : String(w); };
const empty = { concept: "", industry: "", jurisdiction: "NY", budget: "3000", goals: "", preferences: "", notes: "", assumptions: "" };
type Form = typeof empty;

function PlanCard({ p, t, sel, idea, busy, onSelect }: { p: BusinessPlan; t: (k: K) => string; sel: boolean; idea: Idea; busy: boolean; onSelect: () => void }) {
  const rows = (items: { label: string; amount_cents: number }[], tot: number) => (
    <table><tbody>{items.map((i, n) => <tr key={n}><td>{i.label}</td><td>{usd(i.amount_cents)}</td></tr>)}<tr><td><b>{t("total")}</b></td><td><b>{usd(tot)}</b></td></tr></tbody></table>);
  return (
    <article className="iv-plan" data-sel={sel} data-testid={`plan-${p.key}`} aria-label={p.name}>
      {p.recommended && <span className="gx-badge">{t("rec")}</span>}
      <h4 className="serif">{p.name}</h4><p>{p.strategy}</p>
      {p.recommended && <p className="gx-help">{p.recommendation_reason}</p>}
      <p className="gx-help">{p.business_model} {p.target_customers}</p>
      <h5>{t("startup")}</h5>{rows(p.startup_items, p.startup_total_cents)}
      <h5>{t("monthly")} ({t("fixed")})</h5>{rows(p.monthly_items, p.monthly_fixed_cents)}
      <p className="gx-help">{t("variable")}: {usd(Math.round(p.monthly_revenue_cents * (1 - p.gross_margin)))}.
        {" "}{t("totalMonthly")}: {usd(p.monthly_fixed_cents + Math.round(p.monthly_revenue_cents * (1 - p.gross_margin)))}.</p>
      <dl><dt>{t("avail")}</dt><dd>{usd(p.available_budget_cents)}</dd><dt>{t("reserve")}</dt><dd>{usd(p.reserve_cents)}</dd>
        <dt>{t("fund")}</dt><dd>{usd(p.funding_required_cents)}</dd><dt>{t("gap")}</dt><dd className={p.funding_gap_cents > 0 ? "gx-err" : ""}>{usd(p.funding_gap_cents)}</dd>
        <dt>{t("revenue")}</dt><dd>{usd(p.monthly_revenue_cents)}</dd><dt>{t("profit")}</dt><dd>{usd(p.operating_profit_cents)}</dd><dt>{t("breakeven")}</dt><dd>{usd(p.break_even_revenue_cents)}</dd></dl>
      <h5>{t("rev")}</h5>
      <table><tbody>{p.revenue_scenarios.map((r, n) => <tr key={n}><td>{r.label}</td><td>{usd(r.revenue_cents)} / {usd(r.operating_profit_cents)}</td></tr>)}</tbody></table>
      <h5>{t("assumpH")}</h5><ul>{[...p.market_assumptions, ...p.assumptions].map((a, n) => <li key={n}>{a}</li>)}</ul>
      <h5>{t("risks")}</h5><ul>{p.risks.map((a, n) => <li key={n}>{a}</li>)}</ul>
      <h5>{t("marketing")}</h5><p>{p.marketing}</p>
      <h5>{t("milestones")}</h5><ol>{p.milestones.map((a, n) => <li key={n}>{a}</li>)}</ol>
      <h5>{t("reqs")}</h5>
      <ul>{p.requirements.map((r, n) => <li key={n}><b>{r.title}</b> <span className="gx-tag">{r.status}</span> {r.reason} {r.official_url && <a href={r.official_url} target="_blank" rel="noopener noreferrer">{r.official_url}</a>}</li>)}</ul>
      <h5>{t("pros")}</h5><ul>{p.service_needs.map((r, n) => <li key={n}><b>{r.category}</b>: {r.reason}</li>)}</ul>
      {idea.status === "PLANNED" && <button type="button" className="gx-btn" disabled={busy || sel} aria-pressed={sel} data-testid={`select-${p.key}`} onClick={onSelect}>{sel ? t("selected") : t("select")}</button>}
      {idea.status !== "PLANNED" && sel && <span className="gx-badge">{t("selected")}</span>}
    </article>
  );
}

export default function IdeaVault() {
  const [lang, setLang] = useState<L>("en");
  const t = useCallback((k: K) => T[lang][k], [lang]);
  const [account, setAccount] = useState<Account | null | undefined>(undefined);
  const [boot, setBoot] = useState("");
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [showArch, setShowArch] = useState(false);
  const [cur, setCur] = useState<Idea | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [form, setForm] = useState<Form>(empty);
  const [consent, setConsent] = useState(false);
  const [editing, setEditing] = useState(false);
  const [formMode, setFormMode] = useState(false);
  const [fe, setFe] = useState<Partial<Record<keyof Form | "consent", string>>>({});
  const [err, setErr] = useState("");
  const [conflict, setConflict] = useState(false);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [authErr, setAuthErr] = useState("");
  const errRef = useRef<HTMLParagraphElement>(null);
  const headRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => { const e = document.documentElement, p = e.lang; e.lang = lang; return () => { e.lang = p; }; }, [lang]);

  const epoch = useRef(0);
  const verified = useRef<string | null>(null);
  const busyRef = useRef(false);
  const mut = useRef(0);
  const formRef = useRef(false); formRef.current = formMode;
  const curId = useRef<string | null>(null); curId.current = cur?.id ?? null;
  const [view, setView] = useState<"mine" | "review">("mine");

  const resetScoped = useCallback(() => {
    epoch.current++; busyRef.current = false; setBusy(false);
    setIdeas([]); setProjects([]); setCur(null); setProject(null); setForm(empty); setConsent(false); setFormMode(false); setEditing(false);
    setFe({}); setErr(""); setConflict(false); setMsg(""); setLoaded(false); setBoot(""); setView("mine"); setShowArch(false);
  }, []);
  const adopt = useCallback((a: Account) => {
    if (verified.current !== null && verified.current !== a.id) resetScoped();
    verified.current = a.id; setAccount(a);
  }, [resetScoped]);
  const begin = (): number | null => { if (busyRef.current) return null; busyRef.current = true; mut.current++; setBusy(true); return epoch.current; };
  const end = (ep: number) => { if (ep === epoch.current) { busyRef.current = false; setBusy(false); } };

  const fail = useCallback((e: unknown) => {
    setMsg(""); setConflict(false);
    if (e instanceof ApiError && e.status === 401) { epoch.current++; busyRef.current = false; setBusy(false); setErr(T[lang].s401); setAccount(null); }
    else if (e instanceof ApiError && e.status === 409) { setConflict(true); setErr(T[lang].s409); }
    else setErr(e instanceof Error ? e.message : "Error");
    window.setTimeout(() => errRef.current?.focus(), 20);
  }, [lang]);

  const refresh = useCallback(async () => {
    const ep = epoch.current;
    try {
      const [a, b] = await Promise.all([listIdeas(), listProjects()]);
      if (ep !== epoch.current) return;
      setIdeas(a.ideas); setProjects(b.projects); setLoaded(true); setBoot("");
    } catch (e) {
      if (ep !== epoch.current) return;
      if (e instanceof ApiError && e.status === 401) fail(e); else setBoot(e instanceof Error ? e.message : "Error");
    }
  }, [fail]);
  const start = useCallback(() => {
    setBoot("");
    getSession().then((a) => { if (a) adopt(a); else setAccount(null); }).catch((e) => setBoot(e instanceof Error ? e.message : "Error"));
  }, [adopt]);
  useEffect(start, [start]);
  useEffect(() => { if (account) void refresh(); }, [account, refresh]);

  // Refetch on focus without touching drafts; stale responses are dropped, failed mutations are never replayed.
  useEffect(() => {
    if (!account) return;
    const f = async () => {
      if (document.visibilityState !== "visible" || busyRef.current) return;
      const ep = epoch.current, ms = mut.current;
      const ok = () => ep === epoch.current && ms === mut.current && !busyRef.current;
      try {
        const a = await listIdeas(); const b = await listProjects();
        if (!ok()) return;
        setIdeas(a.ideas); setProjects(b.projects);
        const id = curId.current;
        if (id && !formRef.current) {
          const i = await getIdea(id);
          if (!ok() || formRef.current || curId.current !== id) return;
          const p = i.project_id ? await getProject(i.project_id) : null;
          if (!ok() || formRef.current || curId.current !== id) return;
          setCur(i); setProject(p);
        }
      } catch (e) { if (ep === epoch.current && e instanceof ApiError && e.status === 401) fail(e); }
    };
    const h = () => { void f(); };
    window.addEventListener("focus", h); document.addEventListener("visibilitychange", h);
    return () => { window.removeEventListener("focus", h); document.removeEventListener("visibilitychange", h); };
  }, [account, fail]);

  const submitAuth = async (e: FormEvent) => {
    e.preventDefault(); setAuthErr("");
    const ep = begin(); if (ep === null) return;
    try { const a = await signIn("login", email.trim(), password); setPassword(""); setErr(""); adopt(a); }
    catch (x) { setAuthErr(x instanceof Error ? x.message : "Error"); } finally { end(ep); }
  };
  const logout = async () => {
    const ep = begin(); if (ep === null) return;
    try { await signOut(); if (ep !== epoch.current) return; verified.current = null; resetScoped(); setAccount(null); setEmail(""); setPassword(""); }
    catch (e) { if (ep === epoch.current) fail(e); } finally { end(ep); }
  };

  const openIdea = async (id: string) => {
    const ep = begin(); if (ep === null) return;
    setErr(""); setConflict(false); setMsg(""); setFormMode(false); setEditing(false); setProject(null);
    try {
      const i = await getIdea(id);
      const p = i.project_id ? await getProject(i.project_id) : null;
      if (ep !== epoch.current) return;
      setCur(i); setProject(p);
      window.setTimeout(() => headRef.current?.focus(), 30);
    } catch (e) { if (ep === epoch.current) fail(e); } finally { end(ep); }
  };
  const openProject = async (id: string) => {
    const ep = begin(); if (ep === null) return;
    setErr("");
    try { const p = await getProject(id); const i = await getIdea(p.idea_id); if (ep !== epoch.current) return; setProject(p); setCur(i); setFormMode(false); window.setTimeout(() => headRef.current?.focus(), 30); }
    catch (e) { if (ep === epoch.current) fail(e); } finally { end(ep); }
  };
  const startNew = () => { setCur(null); setProject(null); setEditing(false); setFormMode(true); setForm(empty); setConsent(false); setFe({}); setErr(""); setConflict(false); setMsg(""); };
  const startEdit = (i: Idea) => {
    setEditing(true); setFormMode(true); setFe({}); setErr(""); setMsg("");
    setForm({ concept: i.concept, industry: i.industry, jurisdiction: i.jurisdiction, budget: centsToField(i.budget_cents), goals: i.goals, preferences: i.preferences, notes: i.notes, assumptions: i.assumptions });
  };
  const set = (k: keyof Form) => (e: { target: { value: string } }) => { setForm((f) => ({ ...f, [k]: e.target.value })); setFe((x) => ({ ...x, [k]: "" })); };

  const submitForm = async (e: FormEvent) => {
    e.preventDefault(); setErr(""); setConflict(false);
    const v: typeof fe = {}; const cents = dollarsToCents(form.budget);
    if (form.concept.trim().length < 5) v.concept = t("vConcept");
    if (!/^[A-Za-z]{2}$/.test(form.jurisdiction.trim())) v.jurisdiction = t("vState");
    if (cents === null) v.budget = t("vBudget");
    if (!editing && !consent) v.consent = t("consent");
    setFe(v);
    if (Object.keys(v).length || cents === null) { window.setTimeout(() => document.querySelector<HTMLElement>("[aria-invalid=true]")?.focus(), 20); return; }
    const input: IdeaInput = { concept: form.concept.trim(), industry: form.industry.trim(), jurisdiction: form.jurisdiction.trim().toUpperCase(), budget_cents: cents,
      goals: form.goals.trim(), preferences: form.preferences.trim(), notes: form.notes.trim(), assumptions: form.assumptions.trim() };
    const ep = begin(); if (ep === null) return;
    setMsg(t("saving"));
    try {
      const i = editing && cur ? await editIdea(cur, input) : await createIdea(input);
      if (ep !== epoch.current) return;
      setCur(i); setProject(null); setFormMode(false); setEditing(false); setForm(empty); setConsent(false); setMsg(t("saved")); await refresh();
    } catch (x) { if (ep === epoch.current) fail(x); } finally { end(ep); }
  };

  const act = async (fn: () => Promise<Idea>) => {
    const ep = begin(); if (ep === null) return;
    setErr(""); setConflict(false); setMsg(t("saving"));
    try { const i = await fn(); if (ep !== epoch.current) return; setCur(i); setMsg(t("saved")); await refresh(); }
    catch (x) { if (ep === epoch.current) fail(x); } finally { end(ep); }
  };
  const quick = async (id: string, action: "archive" | "restore") => {
    const ep = begin(); if (ep === null) return;
    setErr(""); setConflict(false); setMsg(t("saving"));
    try { const f = await getIdea(id); await ideaAction(f, action); if (ep !== epoch.current) return; setMsg(t("saved")); await refresh(); }
    catch (x) { if (ep === epoch.current) fail(x); } finally { end(ep); }
  };
  const develop = async () => {
    if (!cur) return;
    const ep = begin(); if (ep === null) return;
    setErr(""); setConflict(false); setMsg(t("saving"));
    try { const p = await developIdea(cur); const pr = await getProject(p.id); const i = await getIdea(cur.id); if (ep !== epoch.current) return; setProject(pr); setCur(i); setMsg(t("saved")); await refresh(); }
    catch (x) { if (ep === epoch.current) fail(x); } finally { end(ep); }
  };
  const toggle = async (id: string, status: string) => {
    if (!project) return; const next = status === "done" ? "todo" : "done";
    const ep = begin(); if (ep === null) return;
    setErr(""); setMsg(t("saving"));
    try { await setProjectTask(project, id, next); const p = await getProject(project.id); if (ep !== epoch.current) return; setProject(p); setMsg(t("saved")); }
    catch (x) { if (ep === epoch.current) fail(x); } finally { end(ep); }
  };
  const reloadLatest = async () => { if (cur) await openIdea(cur.id); else { const ep = begin(); if (ep === null) return; try { await refresh(); setConflict(false); setErr(""); } finally { end(ep); } } };
  const goMine = () => { setView("mine"); setCur(null); setProject(null); setFormMode(false); setErr(""); setMsg(""); setConflict(false); void refresh(); };
  const goReview = () => { setView("review"); setCur(null); setProject(null); setFormMode(false); setErr(""); setMsg(""); setConflict(false); void refresh(); };
  const fmt = (s: string) => { const d = new Date(s); return Number.isNaN(d.getTime()) ? s : d.toLocaleString(lang); };

  const field = (k: keyof Form, label: K, multi = false, extra: Record<string, string> = {}) => (
    <label className="gx-field" htmlFor={`f-${k}`}>{t(label)}
      {multi ? <textarea id={`f-${k}`} className="iv-in" value={form[k]} onChange={set(k)} data-testid={`input-${k}`} />
        : <input id={`f-${k}`} className="iv-in" value={form[k]} onChange={set(k)} aria-invalid={!!fe[k]} aria-describedby={`e-${k}`} data-testid={`input-${k}`} {...extra} />}
      <span id={`e-${k}`} className="gx-err" role={fe[k] ? "alert" : undefined}>{fe[k]}</span></label>);

  const formView = (
    <section className="gx-card" aria-labelledby="iv-fh">
      <h2 id="iv-fh">{editing ? t("editIdea") : t("newIdea")}</h2>
      <form onSubmit={submitForm} noValidate><fieldset disabled={busy} style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>
        <label className="gx-field" htmlFor="f-concept">{t("concept")}
          <textarea id="f-concept" className="iv-in" value={form.concept} onChange={set("concept")} aria-invalid={!!fe.concept} aria-describedby="e-concept" data-testid="input-concept" />
          <span id="e-concept" className="gx-err" role={fe.concept ? "alert" : undefined}>{fe.concept}</span></label>
        {field("industry", "industry")}
        {field("jurisdiction", "juris", false, { maxLength: "2", autoCapitalize: "characters", autoComplete: "off" })}
        {field("budget", "budget", false, { inputMode: "decimal" })}
        {field("goals", "goals", true)}{field("preferences", "prefs", true)}{field("notes", "notes", true)}{field("assumptions", "assum", true)}
        {!editing && <><label className="gx-check"><input type="checkbox" checked={consent} aria-invalid={!!fe.consent} onChange={(e) => { setConsent(e.target.checked); setFe((x) => ({ ...x, consent: "" })); }} data-testid="consent-idea" /><span>{t("consent")}</span></label>
          {fe.consent && <p className="gx-err" role="alert">{fe.consent}</p>}</>}
        <div className="gx-row">
          <button className="gx-btn" type="submit" disabled={busy} data-testid="save-idea">{busy ? t("saving") : editing ? t("saveCh") : t("save")}</button>
          <button type="button" className="gx-btn sec" disabled={busy} onClick={() => { setFormMode(false); setEditing(false); setFe({}); }}>{t("cancel")}</button>
        </div>
      </fieldset></form>
    </section>);

  const detail = cur && !formMode && (
    <section className="gx-card" aria-labelledby="iv-dh" data-testid="idea-detail">
      <button type="button" className="gx-btn sec" onClick={() => { setCur(null); setProject(null); setMsg(""); setErr(""); setConflict(false); }}>{t("back")}</button>
      <h2 id="iv-dh" tabIndex={-1} ref={headRef} style={{ marginTop: 14 }}>{cur.concept}</h2>
      <p><span className="gx-badge" data-testid="idea-status">{cur.status}</span> <span className="gx-help">{cur.industry} {cur.jurisdiction} {usd(cur.budget_cents)} v{cur.version}</span></p>
      {[cur.goals, cur.preferences, cur.notes, cur.assumptions].filter(Boolean).map((x, n) => <p key={n} className="gx-help">{x}</p>)}
      {cur.status === "DEVELOPED" && <p className="gx-warn">{t("devNote")}</p>}
      <div className="gx-row">
        {(cur.status === "DRAFT" || cur.status === "PLANNED") && <button type="button" className="gx-btn sec" disabled={busy} data-testid="edit-idea" onClick={() => startEdit(cur)}>{t("editIdea")}</button>}
        {(cur.status === "DRAFT" || cur.status === "PLANNED") && <button type="button" className="gx-btn" disabled={busy} data-testid="generate" onClick={() => act(() => ideaAction(cur, "generate"))}>{cur.plans.length ? t("regen") : t("gen")}</button>}
        {cur.status !== "ARCHIVED" && <button type="button" className="gx-btn sec" disabled={busy} data-testid="archive" onClick={() => act(() => ideaAction(cur, "archive"))}>{t("archive")}</button>}
        {cur.status === "ARCHIVED" && <button type="button" className="gx-btn" disabled={busy} data-testid="restore" onClick={() => act(() => ideaAction(cur, "restore"))}>{t("restore")}</button>}
        {cur.status === "PLANNED" && cur.selected_plan && <button type="button" className="gx-btn" disabled={busy} data-testid="develop" onClick={develop}>{t("develop")}</button>}
      </div>
      {cur.plans.length > 0 && <>
        <h3 style={{ marginTop: 20 }}>{t("compare")}</h3>
        <div className="iv-grid three">{cur.plans.map((p) => <PlanCard key={p.key} p={p} t={t} sel={cur.selected_plan === p.key} idea={cur} busy={busy} onSelect={() => act(() => selectPlan(cur, p.key))} />)}</div></>}
      {cur.history.length > 0 && <section aria-labelledby="iv-hh" data-testid="idea-history"><h3 id="iv-hh" style={{ marginTop: 22 }}>{t("history")}</h3>
        <ol style={{ listStyle: "none", padding: 0 }}>{cur.history.map((h, n) => <li className="iv-task" key={n}><span><b>v{h.version} {h.action}</b><small className="gx-help">{fmt(h.created_at)}</small></span></li>)}</ol></section>}
      <p className="gx-help">{t("created")}: {fmt(cur.created_at)}. {t("updated")}: {fmt(cur.updated_at)}.</p>
      {project && <section aria-labelledby="iv-ph" data-testid="project-detail">
        <h3 id="iv-ph" style={{ marginTop: 22 }}>{project.name}</h3>
        <p className="gx-help">{project.stage} {usd(project.budget_cents)} {project.plan.name}</p>
        <h4>{t("checklist")}</h4>
        {project.checklist.map((c) => (
          <label className="iv-task" key={c.id}>
            <input type="checkbox" checked={c.status === "done"} disabled={busy} onChange={() => void toggle(c.id, c.status)} data-testid={`task-${c.id}`} />
            <span><b>{c.task}</b><small className="gx-help">{c.horizon} {c.kpi} {usd(c.budget)} {c.status === "done" ? t("done") : t("todo")}</small></span></label>))}
        <ProjectExecution key={project.id} projectId={project.id} onProjectChange={async () => { const id = project.id; const p = await getProject(id); if (curId.current) setProject((o) => (o && o.id === id ? p : o)); }} />
      </section>}
    </section>);

  const shown = ideas.filter((i) => showArch || i.status !== "ARCHIVED");
  const review = ideas.filter((i) => i.status === "PLANNED");
  const rowButtons = (i: Idea) => (
    <div className="gx-row" style={{ marginTop: 0 }}><button type="button" className="gx-btn sec" disabled={busy} onClick={() => void openIdea(i.id)}>{t("open")}</button>
      {(view === "mine") && i.status !== "ARCHIVED" && i.status !== "DEVELOPED" && <button type="button" className="gx-btn sec" disabled={busy} onClick={() => void quick(i.id, "archive")}>{t("archive")}</button>}
      {(view === "mine") && i.status === "ARCHIVED" && <button type="button" className="gx-btn sec" disabled={busy} onClick={() => void quick(i.id, "restore")}>{t("restore")}</button>}
    </div>);
  const reviewView = (
    <section className="gx-card" aria-labelledby="iv-rh" data-testid="review-decisions">
      <h2 id="iv-rh">{t("reviewH")}</h2><p className="gx-help">{t("reviewP")}</p>
      {review.length === 0 && <p className="gx-help" data-testid="text-empty-review">{t("reviewNone")}</p>}
      {review.map((i) => <div className="iv-item" key={i.id} data-testid={`review-${i.id}`}>
        <b className="serif">{i.concept}</b>
        <span className="gx-help">{i.selected_plan ? `${t("readyDevelop")}: ${i.plans.find((p) => p.key === i.selected_plan)?.name ?? i.selected_plan}` : t("needSelect")} {usd(i.budget_cents)}</span>
        {rowButtons(i)}</div>)}
    </section>);
  const list = (
    <section className="gx-card" aria-labelledby="iv-lh">
      <h2 id="iv-lh">{t("ideas")}</h2>
      <div className="gx-row"><button type="button" className="gx-btn" disabled={busy} data-testid="new-idea" onClick={startNew}>{t("newIdea")}</button>
        <label className="gx-check" style={{ marginTop: 0 }}><input type="checkbox" checked={showArch} onChange={(e) => setShowArch(e.target.checked)} /><span>{t("showArch")}</span></label></div>
      {shown.length === 0 && <p className="gx-help" data-testid="text-empty-ideas">{t("none")}</p>}
      {shown.map((i) => <div className="iv-item" key={i.id} data-testid={`idea-${i.id}`}>
        <b className="serif">{i.concept}</b><span className="gx-help">{i.status} {i.jurisdiction} {usd(i.budget_cents)}</span>{rowButtons(i)}</div>)}
      {projects.length > 0 && <><h3>{t("proj")}</h3>{projects.map((p) => <div className="iv-item" key={p.id}><b>{p.name}</b>
        <div className="gx-row" style={{ marginTop: 0 }}><button type="button" className="gx-btn sec" disabled={busy} data-testid={`open-project-${p.id}`} onClick={() => void openProject(p.id)}>{t("open2")}</button></div></div>)}</>}
    </section>);

  let body;
  if (boot) body = <section className="gx-card"><p className="gx-err" role="alert">{boot}</p><button type="button" className="gx-btn" onClick={() => (account ? void refresh() : start())}>{t("retry")}</button></section>;
  else if (account === undefined || (account && !loaded)) body = <div className="gx-skel" role="status" aria-busy="true" aria-label={t("loading")} />;
  else if (!account) body = (
    <section className="gx-card"><h2>{t("signin")}</h2>
      {err && <p className="gx-err" role="alert" data-testid="text-session-error">{err}</p>}
      <form onSubmit={submitAuth}>
        <label className="gx-field">{t("email")}<input className="iv-in" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} data-testid="email" /></label>
        <label className="gx-field">{t("password")}<input className="iv-in" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} data-testid="password" /></label>
        {authErr && <p className="gx-err" role="alert">{authErr}</p>}
        <div className="gx-row"><button className="gx-btn" type="submit" disabled={busy}>{t("signin")}</button><a className="gx-btn sec" href={`${base}next/`}>{t("guided")}</a></div>
      </form></section>);
  else body = formMode ? formView : cur ? detail : view === "review" ? reviewView : list;

  return (
    <div className="gx" lang={lang} data-testid="ideas-root">
      <div className="gx-wrap">
        <header className="gx-top">
          <span className="gx-brand">B.I.G. <span className="gx-badge">{t("title")}</span></span>
          <div className="gx-tools">
            <label>Language<select data-testid="language" disabled={busy} value={lang} onChange={(e) => setLang(e.target.value as L)}><option value="en">English</option><option value="es">Español</option></select></label>
            {account && <button type="button" className="gx-btn sec" data-testid="logout" disabled={busy} onClick={logout}>{t("signout")}</button>}
          </div>
        </header>
        <nav className="iv-nav" aria-label={t("primary")}>
          <a className="gx-btn" href={`${base}next/`} data-testid="nav-ask">{t("guided")}</a>
          {account && <button type="button" className={`gx-btn ${view === "mine" && !formMode ? "" : "sec"}`} disabled={busy} aria-current={view === "mine" ? "page" : undefined} data-testid="nav-my-businesses" onClick={goMine}>{t("mybiz")}</button>}
          {account && <button type="button" className={`gx-btn ${view === "review" && !formMode ? "" : "sec"}`} disabled={busy} aria-current={view === "review" ? "page" : undefined} data-testid="nav-review" onClick={goReview}>{t("reviewNav")}{ideas.length ? ` (${ideas.filter((i) => i.status === "PLANNED").length})` : ""}</button>}
        </nav>
        <details className="iv-more" style={{ marginTop: 8 }}>
          <summary style={{ minHeight: 44, display: "flex", alignItems: "center", cursor: "pointer" }}>{t("more")}</summary>
          <div className="iv-nav">
            <a className="gx-btn sec" href={`${base}next/draft/`}>{t("guest")}</a>
            <a className="gx-btn sec" href={`${base}next/partners/`}>{t("partners")}</a>
            <OwnerAccessLink accountId={account?.id ?? null} language={lang} />
            <a className="gx-btn sec" href={base}>{t("ws")}</a>
          </div>
        </details>
        <main>
          <section className="gx-hero"><h1>{t("heroH")}</h1><p>{t("sub")}</p>{account && loaded && !formMode && !cur && <div className="gx-row"><button type="button" className="gx-btn" disabled={busy} data-testid="hero-save" onClick={startNew}>{ideas.length ? t("newIdea") : t("firstSave")}</button></div>}</section>
          <p className="gx-warn" role="note">{t("det")}</p>
          <p className="gx-help" role="note">{t("notice")}</p>
          <div className="iv-toast" aria-live="polite" role="status">{msg && <p className="gx-ok">{msg}</p>}</div>
          {account && err && <div aria-live="assertive"><p className="gx-err" role="alert" tabIndex={-1} ref={errRef} data-testid="text-idea-error">{err}</p>
            {conflict && <div className="gx-row"><button type="button" className="gx-btn sec" disabled={busy} data-testid="reload-idea" onClick={() => void reloadLatest()}>{t("reload")}</button></div>}</div>}
          {body}
        </main>
      </div>
    </div>
  );
}
