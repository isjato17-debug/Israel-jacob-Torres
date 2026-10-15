import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { createPlan, fetchCatalog } from './api';
import type { Catalog, Intake, Plan, Stage } from './api';
import './next.css';

const STAGES: { id: Stage; label: string; blurb: string }[] = [
  { id: 'start', label: 'START MY BUSINESS', blurb: 'Choose a structure and get legally set up.' },
  { id: 'run', label: 'RUN MY BUSINESS', blurb: 'Keep operations, money and compliance steady.' },
  { id: 'grow', label: 'GROW MY BUSINESS', blurb: 'Add customers, capacity and capital carefully.' },
];
const AVAIL: Record<string, string> = {
  GUIDED_ONLY: 'Guided only',
  NEEDS_CONNECTION: 'Needs a verified connection',
  NEEDS_PROFESSIONAL: 'Needs a professional',
};
const home = import.meta.env.BASE_URL;

function pretty(s: string) { return s.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase()); }

function planText(p: Plan) {
  const L = [
    'GENESIS OS PRELIMINARY PLAN - UNSAVED DRAFT',
    'Rule-based checklist. Not AI-generated. Not state-specific legal advice. Not saved by Genesis.',
    '',
    `Stage: ${p.intake.stage}`, `State: ${p.state_name}`, `Entity type: ${p.intake.entity_type}`,
    `Ownership: ${p.intake.ownership_type}`, `Goal / context: ${p.intake.goal}`, '', 'STEPS',
  ];
  p.steps.forEach((s) => {
    L.push(`${s.order}. ${s.title} [${s.status}]${s.professional_review ? ' (professional review)' : ''}`, `   Next: ${s.next_action}`);
    if (s.official_url) L.push(`   Official: ${s.official_url}`);
  });
  if (p.approvals.length) L.push('', 'APPROVALS NEEDED', ...p.approvals.map((a) => `- ${a}`));
  L.push('', p.notice);
  return L.join('\n');
}

export default function GenesisNext() {
  const [cat, setCat] = useState<Catalog | null>(null);
  const [catErr, setCatErr] = useState('');
  const [stage, setStage] = useState<Stage>('start');
  const [form, setForm] = useState({ state: '', entity_type: '', ownership_type: '', goal: '' });
  const [touched, setTouched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [planErr, setPlanErr] = useState('');
  const [plan, setPlan] = useState<Plan | null>(null);
  const [q, setQ] = useState('');
  const [svcStage, setSvcStage] = useState<Stage | 'all'>('all');

  const load = () => {
    setCatErr(''); setCat(null);
    fetchCatalog().then(setCat).catch((e) => setCatErr(e instanceof Error ? e.message : 'Could not load the catalog.'));
  };
  useEffect(load, []);

  const errors = {
    state: form.state ? '' : 'Choose a state.',
    entity_type: form.entity_type ? '' : 'Choose a legal entity type.',
    ownership_type: form.ownership_type ? '' : 'Choose an ownership type.',
    goal: form.goal.trim().length < 5 || form.goal.trim().length > 1200 ? 'Describe your goal in 5–1,200 characters.' : '',
  };
  const invalid = Object.values(errors).some(Boolean);

  async function submit(e: FormEvent) {
    e.preventDefault(); setTouched(true); setPlanErr('');
    if (invalid) return;
    setBusy(true);
    const intake: Intake = { stage, ...form, goal: form.goal.trim() };
    try { setPlan(await createPlan(intake)); } catch (x) { setPlan(null); setPlanErr(x instanceof Error ? x.message : 'Plan failed.'); } finally { setBusy(false); }
  }

  function download() {
    if (!plan) return;
    const url = URL.createObjectURL(new Blob([planText(plan)], { type: 'text/plain' }));
    const a = document.createElement('a'); a.href = url; a.download = 'genesis-preliminary-plan-unsaved-draft.txt'; a.click();
    URL.revokeObjectURL(url);
  }

  const services = useMemo(() => {
    const n = q.trim().toLowerCase();
    return (cat?.services ?? []).filter((s) => (svcStage === 'all' || s.stage === svcStage) &&
      (!n || `${s.title} ${s.description}`.toLowerCase().includes(n)));
  }, [cat, q, svcStage]);

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });
  const fld = (k: keyof typeof errors) => ({ 'aria-invalid': touched && !!errors[k], 'aria-describedby': `err-${k}` });
  const fe = (k: keyof typeof errors) => <span id={`err-${k}`} className="err" role="alert">{touched ? errors[k] : ''}</span>;
  const unverified = cat?.providers.filter((p) => p.status === 'NOT_VERIFIED') ?? [];

  return (
    <div className="genesis-next">
      <main className="wrap">
        <header className="top">
          <span className="brand">Genesis OS 2.0</span>
          <span className="row"><span className="badge">Development preview</span>
            <a href={home} data-testid="link-workspace">Open current workspace</a></span>
        </header>

        <h1>One clear next step.</h1>
        <p className="lead">Pick where you are. Genesis builds a preliminary checklist and shows every service with honest availability. Nothing here is saved, filed or paid.</p>

        <div className="stages" role="group" aria-label="Business stage">
          {STAGES.map((s) => (
            <button key={s.id} type="button" className="stagebtn" aria-pressed={stage === s.id}
              data-testid={`button-stage-${s.id}`} onClick={() => { setStage(s.id); setSvcStage(s.id); }}>
              <b>{s.label}</b><span>{s.blurb}</span>
            </button>
          ))}
        </div>

        <section className="panel" aria-labelledby="plan-h">
          <h2 id="plan-h">Plan my next step</h2>
          <p className="notice">Preliminary rule-based stage checklist. Not AI-generated, not state-specific legal advice, and not saved.</p>
          {catErr && <p className="err" role="alert">{catErr} <button className="btn sec" onClick={load} data-testid="button-retry-catalog">Retry</button></p>}
          {!cat && !catErr && <div className="skel" aria-busy="true" aria-label="Loading catalog" />}
          {cat && (
            <form className="two" onSubmit={submit} noValidate style={{ marginTop: 14 }}>
              <label>State
                <select value={form.state} onChange={set('state')} data-testid="select-state" {...fld('state')}>
                  <option value="">Select a state</option>
                  {cat.states.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
                </select>{fe('state')}</label>
              <label>Legal entity type
                <select value={form.entity_type} onChange={set('entity_type')} data-testid="select-entity" {...fld('entity_type')}>
                  <option value="">Select entity type</option>
                  {cat.entity_types.map((t) => <option key={t} value={t}>{pretty(t)}</option>)}
                </select>{fe('entity_type')}</label>
              <label>Ownership type
                <select value={form.ownership_type} onChange={set('ownership_type')} data-testid="select-ownership" {...fld('ownership_type')}>
                  <option value="">Select ownership</option>
                  {cat.ownership_types.map((t) => <option key={t} value={t}>{pretty(t)}</option>)}
                </select>{fe('ownership_type')}</label>
              <label>Stage
                <input readOnly value={STAGES.find((s) => s.id === stage)!.label} aria-readonly="true" /></label>
              <label className="full">Your goal and context
                <textarea rows={3} maxLength={1200} value={form.goal} onChange={set('goal')} data-testid="input-goal"
                  placeholder="Example: open a weekend bakery and sell at farmers markets" {...fld('goal')} />{fe('goal')}</label>
              <div className="full row">
                <button className="btn" type="submit" disabled={busy} data-testid="button-create-plan">{busy ? 'Building your checklist...' : 'Create preliminary plan'}</button>
              </div>
            </form>
          )}
          {planErr && <p className="err" role="alert" data-testid="text-plan-error">{planErr}</p>}
        </section>

        {plan && (
          <section className="panel" aria-labelledby="res-h" aria-live="polite" data-testid="section-plan">
            <span className="badge">Unsaved draft</span>
            <h2 id="res-h" style={{ marginTop: 10 }}>Your preliminary checklist</h2>
            <p><b>Goal:</b> {plan.intake.goal}</p>
            <p className="lead">Stage {plan.intake.stage} · {plan.state_name} · {pretty(plan.intake.entity_type)} · {pretty(plan.intake.ownership_type)}</p>
            <p className="notice">{plan.notice} Mode: {plan.mode}. Saved: {plan.persisted ? 'yes' : 'no'}.</p>
            <ol>
              {plan.steps.map((s) => (
                <li className="step" key={s.order} data-testid={`step-${s.order}`}>
                  <b>{s.order}. {s.title}</b>
                  <div><span className="tag">{pretty(s.status)}</span>
                    {s.professional_review && <span className="tag w">Professional review</span>}</div>
                  <p style={{ margin: '6px 0' }}>{s.next_action}</p>
                  {s.official_url && <a href={s.official_url} target="_blank" rel="noopener noreferrer">Official source</a>}
                </li>
              ))}
            </ol>
            {plan.approvals.length > 0 && <><h3>Approvals needed from you</h3><ul>{plan.approvals.map((a) => <li key={a}>{a}</li>)}</ul></>}
            <div className="row" style={{ marginTop: 14 }}>
              <button className="btn" onClick={download} data-testid="button-download-plan">Download plan as text (unsaved draft)</button>
              <a className="btn sec" href={home}>Continue in current workspace</a>
            </div>
          </section>
        )}

        <section className="panel" aria-labelledby="svc-h">
          <h2 id="svc-h">Service discovery</h2>
          {cat && <p className="notice">{cat.notice} Billing: {pretty(cat.billing.status)}; checkout {cat.billing.checkout_enabled ? 'enabled' : 'not enabled'}. AI: {cat.ai.status}. {cat.ai.notice}
            {unverified.length > 0 && <> Not verified, so not connected: {unverified.map((p) => p.name).join(', ')}.</>}</p>}
          <div className="row" style={{ margin: '14px 0' }}>
            <label style={{ flex: '1 1 240px' }}>Search services
              <input type="search" value={q} onChange={(e) => setQ(e.target.value)} data-testid="input-search" placeholder="Try: tax, license, bank" /></label>
            <div className="row" role="group" aria-label="Filter by stage">
              {(['all', 'start', 'run', 'grow'] as const).map((f) => (
                <button key={f} type="button" className={`btn ${svcStage === f ? '' : 'sec'}`} aria-pressed={svcStage === f}
                  data-testid={`button-filter-${f}`} onClick={() => setSvcStage(f)}>{f === 'all' ? 'All' : pretty(f)}</button>
              ))}
            </div>
          </div>
          {!cat && !catErr && <div className="skel" aria-busy="true" />}
          {cat && <p aria-live="polite" data-testid="text-service-count">{services.length} of {cat.services.length} services</p>}
          {cat && services.length === 0 && <p className="notice">No services match. Clear the search or choose another stage.</p>}
          <div className="grid">
            {services.map((s) => (
              <article className="svc" key={s.id} data-testid={`card-service-${s.id}`}>
                <div><span className="tag">{pretty(s.stage)}</span>
                  <span className="tag w">{AVAIL[s.availability] ?? s.availability}</span>
                  {s.professional_review && <span className="tag w">Professional review</span>}</div>
                <h3>{s.title}</h3>
                <p style={{ margin: 0, color: 'var(--mut)' }}>{s.description}</p>
                <small>{s.submission_available ? 'Submission available' : 'Genesis cannot submit this for you.'}</small>
                {s.official_url && <a href={s.official_url} target="_blank" rel="noopener noreferrer">Official link</a>}
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
