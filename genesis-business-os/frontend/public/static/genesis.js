'use strict';

let CSRF = '';
let BUSINESS_ID = '';
let CURRENT_USER = null;
let BUSINESS = null;
let BUSINESS_TWIN = {};
let FOUNDER_DNA = { profile: {}, dna: {} };
let NEXT_TURN = null;
let COMMUNITY_POSTS = [];
let ASK_LAST_TURN = null;
let ACTIONS = [];

const byId = (id) => document.getElementById(id);
const text = (id, value) => {
  const element = byId(id);
  if (element) element.textContent = value;
};
const hasValue = (object, key) => Object.prototype.hasOwnProperty.call(object || {}, key)
  && object[key] !== null && object[key] !== undefined && object[key] !== '';
const numberValue = (value) => value === '' || value === null || value === undefined ? null : Number(value);
const money = (value) => Number.isFinite(Number(value))
  ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(Number(value))
  : 'Not recorded';
const percent = (value) => Number.isFinite(Number(value)) ? `${Math.round(Number(value) * 100)}%` : 'Not recorded';
const splitList = (value) => String(value || '').split(',').map((item) => item.trim()).filter(Boolean);
const reality = () => BUSINESS_TWIN.founder_reality || null;
const destination = () => BUSINESS_TWIN.destination_contract || null;
const displayStage = () => {
  if (!destination()) return { index: 0, label: 'You Are Here', detail: 'Set your destination' };
  if (!reality()) return { index: 1, label: 'Setup', detail: 'Save your founder reality' };
  if (!(BUSINESS_TWIN.route_portfolio || []).length) return { index: 2, label: 'Launch', detail: 'Compare possible routes' };
  if (!NEXT_TURN && !BUSINESS_TWIN.next_turn) return { index: 2, label: 'Launch', detail: 'Choose a next turn' };
  const routeProofs = BUSINESS_TWIN.route_proofs || {};
  if (!Object.keys(routeProofs).length) return { index: 3, label: 'Grow', detail: 'Gather checkpoint evidence' };
  return { index: 4, label: 'Destination', detail: 'Review evidence and adapt' };
};

function cookie(name) {
  const item = document.cookie.split('; ').find((part) => part.startsWith(`${name}=`));
  return item ? item.split('=').slice(1).join('=') : '';
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

async function api(path, options = {}) {
  const method = options.method || 'GET';
  const headers = { ...(options.headers || {}) };
  if (options.body) headers['Content-Type'] = 'application/json';
  if (CSRF && method !== 'GET') headers['X-CSRF-Token'] = CSRF;

  const response = await fetch(path, {
    ...options,
    method,
    headers,
    credentials: 'same-origin',
  });
  let body;
  try {
    body = await response.json();
  } catch {
    body = { detail: 'Invalid server response' };
  }
  if (!response.ok) {
    const detail = body?.detail;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail || body));
  }
  return body;
}

function go(id) {
  if (!byId(id)) return;
  document.querySelectorAll('.view').forEach((view) => view.classList.remove('on'));
  byId(id)?.classList.add('on');
  document.querySelectorAll('nav button').forEach((button) => {
    button.classList.toggle('on', button.dataset.view === id);
  });
  if (id === 'do') loadExecution();
  if (id === 'community') loadCommunity();
  if (id === 'business') {
    renderBusinessState();
    loadBusinessDNA();
  }
  window.scrollTo(0, 0);
}

async function bootstrap() {
  try {
    CURRENT_USER = await api('/api/me');
    CSRF = decodeURIComponent(cookie('genesis_csrf'));
    byId('authgate')?.classList.add('off');
    await ensureBusiness();
  } catch {
    text('authmsg', 'Sign in or create a workspace.');
  }
}

async function authenticate(kind) {
  text('authmsg', 'Working…');
  try {
    const tenantName = byId('tenant')?.value.trim() || '';
    const email = byId('email')?.value.trim() || '';
    const password = byId('password')?.value || '';
    if (kind === 'register' && !tenantName) {
      text('authmsg', 'Enter a business workspace name to create your account.');
      byId('tenant')?.focus();
      return;
    }
    const body = kind === 'register'
      ? { tenant_name: tenantName, email, password }
      : { email, password };
    const result = await api(`/api/auth/${kind}`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
    CURRENT_USER = result.user || CURRENT_USER;
    CSRF = result.csrf || decodeURIComponent(cookie('genesis_csrf'));
    byId('authgate')?.classList.add('off');
    await ensureBusiness();
  } catch (error) {
    text('authmsg', error.message);
  }
}

async function ensureBusiness() {
  const businesses = await api('/api/businesses');
  if (!businesses.length) {
    const name = byId('tenant')?.value.trim() || CURRENT_USER?.business_name || '';
    if (!name) throw new Error('No business workspace name is available.');
    const business = await api('/api/businesses', {
      method: 'POST',
      body: JSON.stringify({ name, twin: {} }),
    });
    BUSINESS = business;
  } else {
    BUSINESS = businesses[0];
  }
  BUSINESS_ID = BUSINESS.id;
  BUSINESS_TWIN = BUSINESS.twin || {};
  NEXT_TURN = BUSINESS_TWIN.next_turn || null;
  const profileName = CURRENT_USER?.email || '';
  const badge = byId('profileBadge');
  if (badge) badge.textContent = profileName ? profileName.slice(0, 1).toUpperCase() : 'F';
  const name = byId('profileName');
  if (name) name.textContent = profileName || 'Founder';
  await Promise.allSettled([loadBusinessDNA(), loadActions(), loadCommunity()]);
  renderBusinessState();
}

async function loadBusinessDNA() {
  const output = byId('businessDna');
  if (!output) return;
  try {
    FOUNDER_DNA = await api('/api/founder-dna');
    const profile = FOUNDER_DNA.profile || {};
    const values = [
      ['dnaCapital', profile.capital],
      ['dnaHours', profile.hours_per_week],
      ['dnaExperience', profile.experience_years],
      ['dnaRisk', profile.risk_tolerance],
    ];
    values.forEach(([id, value]) => {
      const input = byId(id);
      if (input && !input.matches(':focus')) input.value = hasValue(profile, input.name) ? String(value) : '';
    });
    const dna = FOUNDER_DNA.dna || {};
    const entries = Object.entries(dna);
    output.textContent = entries.length
      ? `Derived from your saved founder profile: ${entries.map(([key, value]) => `${key.replaceAll('_', ' ')} ${value}`).join(' · ')}`
      : 'No Founder DNA profile has been saved yet.';
    renderBusinessState();
  } catch (error) {
    output.textContent = `Business DNA unavailable: ${error.message}`;
  }
}

function setInputValue(id, value, scale = 1) {
  const input = byId(id);
  if (!input || input.matches(':focus')) return;
  input.value = hasValue({ value }, 'value') ? String(Number(value) * scale) : '';
}

function renderProgress() {
  const routeProofs = BUSINESS_TWIN.route_proofs || {};
  const routes = Array.isArray(BUSINESS_TWIN.route_portfolio) ? BUSINESS_TWIN.route_portfolio : [];
  const verifiedAction = ACTIONS.some((action) => action.status === 'VERIFIED');
  const items = [
    { name: 'Destination', detail: 'Define what success means to you', done: Boolean(destination()) },
    { name: 'Founder reality', detail: 'Start with the resources you have', done: Boolean(reality()) },
    { name: 'Route portfolio', detail: 'Compare possible paths', done: routes.length > 0 },
    { name: 'Next turn', detail: 'Choose an evidence-based move', done: Boolean(NEXT_TURN?.action || BUSINESS_TWIN.next_turn?.action) },
    { name: 'Proof checkpoints', detail: 'Record evidence for your active route', done: Object.keys(routeProofs).length > 0 },
    { name: 'Resource envelope', detail: 'Calculate risk cash from saved limits', done: routes.length > 0 && Boolean(reality() && destination()) },
    { name: 'Results & evolution', detail: 'Use actuals or a verified action to adapt', done: Boolean(BUSINESS_TWIN.latest_evolution || verifiedAction) },
  ];
  const completed = items.filter((item) => item.done).length;
  const nextIndex = items.findIndex((item) => !item.done);
  const list = byId('homeProgress');
  if (list) {
    list.innerHTML = items.map((item, index) => {
      const state = item.done ? 'Recorded' : index === nextIndex ? 'Next' : 'Pending';
      const className = item.done ? 'done' : index === nextIndex ? 'selected' : '';
      return `<div class="milestone ${className}">
        <span class="milestone-mark">${item.done ? '✓' : index + 1}</span>
        <span><b>${escapeHtml(item.name)}</b><small>${escapeHtml(item.detail)}</small></span>
        <span class="milestone-state">${state}</span>
      </div>`;
    }).join('');
  }
  text('homeProgressLabel', `${completed} of ${items.length} milestones recorded`);
  text('homeProgressPercent', `${Math.round((completed / items.length) * 100)}%`);
  const bar = byId('homeProgressBar');
  if (bar) bar.style.width = `${(completed / items.length) * 100}%`;
  const track = document.querySelector('.progress-track[role="progressbar"]');
  if (track) track.setAttribute('aria-valuenow', String(completed));
}

function renderJourney() {
  const stage = displayStage();
  text('heroYouAreHere', stage.label);
  text('heroStageDetail', stage.detail);
  const target = destination();
  text('homeDestination', target
    ? `${money(target.target_monthly_owner_income)}/month owner income`
    : 'Waiting for your destination');
  document.querySelectorAll('.route-dot').forEach((dot) => {
    const step = Number(dot.dataset.step);
    dot.classList.toggle('active', step === Math.min(stage.index, 3));
    dot.classList.toggle('complete', step < stage.index);
  });

  const journey = byId('businessJourney');
  const steps = [
    ['You Are Here', 'Your current starting point'],
    ['Setup', 'Save your founder reality'],
    ['Launch', 'Compare a route to market'],
    ['Grow', 'Use evidence to adapt'],
    ['Destination', target ? `${money(target.target_monthly_owner_income)}/month owner income` : 'Set a destination target'],
  ];
  if (journey) {
    journey.innerHTML = steps.map(([title, detail], index) => {
      const status = index < stage.index ? 'complete' : index === stage.index ? 'now' : '';
      return `<div class="stage ${status}" ${index === stage.index ? 'aria-current="step"' : ''}>
        <span class="stage-index">0${index + 1}</span><b>${escapeHtml(title)}</b><small>${escapeHtml(detail)}</small>
      </div>`;
    }).join('');
  }
  text('journeyStatus', stage.detail);

  const r = reality() || {};
  const d = target || {};
  [
    ['realityCash', r.cash],
    ['realityReserve', r.reserve_floor],
    ['realityHours', r.hours_per_week],
    ['realitySkills', Array.isArray(r.skills) ? r.skills.join(', ') : ''],
    ['realityAssets', Array.isArray(r.assets) ? r.assets.join(', ') : ''],
    ['realityLocation', r.location],
    ['destinationIncome', d.target_monthly_owner_income],
    ['destinationHorizon', d.horizon_months],
    ['destinationRiskCash', d.max_risk_cash],
  ].forEach(([id, value]) => {
    const input = byId(id);
    if (input && !input.matches(':focus')) input.value = hasValue({ value }, 'value') ? String(value) : '';
  });

  const model = BUSINESS_TWIN.business_model || BUSINESS_TWIN.industry || '';
  const resourceText = r.cash === undefined
    ? 'Not recorded'
    : `${money(r.cash)} cash · ${money(r.reserve_floor)} protected · ${r.hours_per_week ?? '—'} hours/week`;
  const locationText = r.location || 'Not recorded';
  const facts = byId('businessFacts');
  if (facts) {
    facts.innerHTML = [
      ['Business model', model || 'Not recorded', model ? 'Saved business profile' : 'Add a business model to your profile'],
      ['Available resources', resourceText, 'From your saved founder reality'],
      ['Location', locationText, locationText === 'Not recorded' ? 'Requirements depend on location' : 'From your saved founder reality'],
    ].map(([label, value, detail]) => `<div><small>${escapeHtml(label)}</small><b>${escapeHtml(value)}</b><span>${escapeHtml(detail)}</span></div>`).join('');
  }
}

function renderOverview() {
  const stage = displayStage();
  const focus = NEXT_TURN?.action || BUSINESS_TWIN.next_turn?.action || '';
  const tiles = [
    ['Business stage', stage.label, 'Based on saved journey data'],
    ['Monthly revenue', hasValue(BUSINESS_TWIN, 'monthly_revenue') ? money(BUSINESS_TWIN.monthly_revenue) : 'Not recorded', 'Owner-reported actual'],
    ['Customers', hasValue(BUSINESS_TWIN, 'customer_count') ? String(BUSINESS_TWIN.customer_count) : 'Not recorded', 'Owner-reported actual'],
    ['Key focus', focus || 'Not available', focus ? (NEXT_TURN?.checkpoint || BUSINESS_TWIN.next_turn?.checkpoint || 'Route Engine') : 'Route Engine recommendation'],
  ];
  const output = byId('homeBusinessOverview');
  if (output) output.innerHTML = tiles.map(([label, value, detail]) =>
    `<div><small>${escapeHtml(label)}</small><b>${escapeHtml(value)}</b><span>${escapeHtml(detail)}</span></div>`).join('');
  const title = byId('businessPageTitle');
  if (title && BUSINESS?.name) title.textContent = BUSINESS.name;
}

function renderNextTurn() {
  NEXT_TURN = NEXT_TURN || BUSINESS_TWIN.next_turn || null;
  const turn = NEXT_TURN;
  const missing = Array.isArray(turn?.proof_missing) ? turn.proof_missing : [];
  const output = byId('nextTurnDetail');
  const home = byId('homeNextMove');
  const proofForm = byId('proofForm');
  if (!turn) {
    if (output) output.innerHTML = '<span class="placeholder-title">Your next turn appears after you calculate a route.</span><span class="muted">The Route Engine needs a saved destination and founder reality.</span>';
    if (home) home.innerHTML = '<span class="placeholder-title">Your next move will appear here</span><span class="muted">Save your destination and founder reality, then compare routes.</span>';
    if (proofForm) proofForm.classList.remove('ready');
    text('homeMoveCost', 'Waiting for your route');
    text('homeMoveTime', 'Not estimated');
    text('homeMoveOutcome', 'Not yet available');
    text('why', 'The Route Engine will explain how a recommendation fits your saved destination, constraints and resources.');
    return;
  }
  const commitment = money(turn.max_cash_commitment);
  const evidence = missing[0] || 'Route complete';
  if (output) {
    output.innerHTML = `<div class="next-turn-card">
      <h3>${escapeHtml(turn.action || 'Next action not available')}</h3>
      <p><b>Checkpoint:</b> ${escapeHtml(turn.checkpoint || 'Not specified')}</p>
      <p><b>Evidence needed:</b> ${escapeHtml(missing.length ? missing.join(' · ') : 'No checkpoint evidence is currently required')}</p>
      <p><b>Maximum cash commitment:</b> ${escapeHtml(commitment)}</p>
      <p class="muted">${escapeHtml(turn.why || '')}</p>
    </div>`;
  }
  if (home) {
    home.innerHTML = `<span class="placeholder-title">${escapeHtml(turn.action || 'Next action not available')}</span>
      <span class="muted"><b>Checkpoint:</b> ${escapeHtml(turn.checkpoint || 'Not specified')} · <b>Evidence:</b> ${escapeHtml(evidence)}</span>`;
  }
  text('homeMoveCost', commitment);
  text('homeMoveTime', 'Not estimated');
  text('homeMoveOutcome', missing.length ? missing[0] : 'Route complete');
  text('why', turn.why || 'This next turn is based on your saved route and current checkpoint evidence.');
  if (proofForm) {
    const ready = missing.length > 0;
    proofForm.classList.toggle('ready', ready);
    text('proofPromptLabel', ready ? `Evidence for: ${missing[0]}` : 'No checkpoint evidence is currently required');
    const proofName = byId('proofName');
    if (proofName) proofName.value = ready ? missing[0] : '';
  }
}

function renderRoutePortfolio() {
  const routes = Array.isArray(BUSINESS_TWIN.route_portfolio) ? BUSINESS_TWIN.route_portfolio : [];
  const output = byId('routePortfolio');
  if (output) {
    output.innerHTML = routes.length
      ? routes.map((route) => `<article class="route-option">
          <div class="eyebrow">${escapeHtml(route.risk || 'Risk not specified')} · ${escapeHtml(money(route.initial_cash_envelope))} initial cash envelope</div>
          <h3>${escapeHtml(route.name || 'Route')}</h3>
          <p class="muted">${escapeHtml(route.reason || '')}</p>
        </article>`).join('')
      : '<div class="data-placeholder">No route portfolio has been calculated yet.</div>';
  }
  text('routePortfolioStatus', routes.length
    ? `${routes.length} routes calculated from your saved destination and founder reality.`
    : 'Save your journey details to calculate a route portfolio.');
  renderNextTurn();
}

function renderBusinessState() {
  if (!BUSINESS_ID) return;
  renderJourney();
  renderOverview();
  renderNextTurn();
  renderProgress();
  const twin = BUSINESS_TWIN;
  setInputValue('metricRevenue', twin.monthly_revenue);
  setInputValue('metricCustomers', twin.customer_count);
  setInputValue('metricMargin', twin.gross_margin, 100);
  setInputValue('metricRepeat', twin.repeat_customer_share, 100);
  setInputValue('metricCapacity', twin.capacity_used, 100);
  setInputValue('metricTicket', twin.average_ticket);
  setInputValue('metricCloseRate', twin.close_rate, 100);
  const currentReality = reality();
  if (currentReality) {
    setInputValue('whatIfCash', currentReality.cash);
    setInputValue('whatIfHours', currentReality.hours_per_week);
  }
  renderRoutePortfolio();
}

async function seeEvolution() {
  const output = byId('evolutionResult');
  if (!BUSINESS_ID || !output) return;
  output?.classList.add('on');
  const required = [
    ['monthly_revenue', 'monthly revenue'],
    ['repeat_customer_share', 'repeat customer share'],
    ['gross_margin', 'gross margin'],
    ['capacity_used', 'capacity used'],
  ];
  const missing = required.filter(([key]) => !hasValue(BUSINESS_TWIN, key));
  if (!reality() || !destination() || missing.length) {
    output.textContent = `Save your founder reality and destination, then record ${missing.length ? missing.map(([, label]) => label).join(', ') : 'the required business actuals'} before comparing futures.`;
    return;
  }
  output.textContent = 'Comparing possible futures from your saved inputs…';
  try {
    const result = await api('/api/route/evolution', {
      method: 'POST',
      body: JSON.stringify({
        reality: reality(),
        destination: destination(),
        monthly_revenue: Number(BUSINESS_TWIN.monthly_revenue),
        repeat_customer_share: Number(BUSINESS_TWIN.repeat_customer_share),
        gross_margin: Number(BUSINESS_TWIN.gross_margin),
        capacity_used: Number(BUSINESS_TWIN.capacity_used),
      }),
    });
    const recommendation = result.recommended_evolution;
    const futures = (result.possible_futures || []).map((future) => {
      const score = Math.max(0, Math.min(100, Number(future.score) || 0));
      return `<div><small>${escapeHtml(future.title)} · ${escapeHtml(score)}/100</small><div class="futurebar"><i style="width:${score}%"></i></div></div>`;
    }).join('');
    const dna = Object.entries(result.business_dna || {})
      .map(([key, value]) => `${escapeHtml(key.replaceAll('_', ' '))}: ${escapeHtml(value)}`)
      .join(' · ');
    output.innerHTML = `<div class="eyebrow">${escapeHtml(result.generation)}</div>
      <h3>Genesis recommends: ${escapeHtml(recommendation.title)}</h3>
      <p>${escapeHtml(recommendation.why)}</p>
      <div class="pills"><span class="pill">Fit score ${escapeHtml(recommendation.score)}/100</span>
      <span class="pill">Cash envelope $${escapeHtml(recommendation.estimated_cash_needed)}</span></div>
      <b>Next:</b> ${escapeHtml(recommendation.next_action)}
      <div style="margin-top:14px" class="muted">Possible futures compared</div>${futures}
      <p class="muted"><b>Business DNA:</b> ${dna || 'No derived signals.'}</p>
      <small class="muted">${escapeHtml(result.disclaimer)} This is a model estimate, not a guaranteed outcome.</small>`;
    BUSINESS_TWIN = (await api(`/api/businesses/${BUSINESS_ID}/twin`, {
      method: 'PATCH',
      body: JSON.stringify({ patch: { latest_evolution: result } }),
    })).twin;
    renderBusinessState();
  } catch (error) {
    output.textContent = `Genesis could not calculate the evolution: ${error.message}`;
  }
}

async function saveTwinPatch(patch) {
  const result = await api(`/api/businesses/${BUSINESS_ID}/twin`, {
    method: 'PATCH',
    body: JSON.stringify({ patch }),
  });
  BUSINESS_TWIN = result.twin || BUSINESS_TWIN;
  if (BUSINESS) BUSINESS.twin = BUSINESS_TWIN;
  return result;
}

function routeProofFlags() {
  return Object.fromEntries(Object.entries(BUSINESS_TWIN.route_proofs || {})
    .map(([name, record]) => [name, Boolean(record?.evidence_id)]));
}

async function refreshRoutes() {
  const realityNow = reality();
  const destinationNow = destination();
  if (!BUSINESS_ID || !realityNow || !destinationNow) {
    text('routePortfolioStatus', 'Save a founder reality and destination before calculating routes.');
    return;
  }
  text('routePortfolioStatus', 'Calculating routes from your saved inputs…');
  try {
    const portfolio = await api('/api/route/portfolio', {
      method: 'POST',
      body: JSON.stringify({ reality: realityNow, destination: destinationNow }),
    });
    const next = await api('/api/route/next-turn', {
      method: 'POST',
      body: JSON.stringify({ reality: realityNow, destination: destinationNow, proofs: routeProofFlags() }),
    });
    NEXT_TURN = next;
    await saveTwinPatch({
      route_portfolio: portfolio.routes || [],
      next_turn: next,
      route_calculated_at: new Date().toISOString(),
    });
    renderBusinessState();
  } catch (error) {
    text('routePortfolioStatus', `Route calculation failed: ${error.message}`);
  }
}

async function saveJourney(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = new FormData(form);
  const realityNow = {
    cash: Number(values.get('cash')),
    reserve_floor: Number(values.get('reserve_floor')),
    hours_per_week: Number(values.get('hours_per_week')),
    skills: splitList(values.get('skills')),
    assets: splitList(values.get('assets')),
    location: String(values.get('location') || '').trim(),
  };
  const destinationNow = {
    target_monthly_owner_income: Number(values.get('target_monthly_owner_income')),
    horizon_months: Number(values.get('horizon_months')),
    max_risk_cash: Number(values.get('max_risk_cash')),
  };
  const status = byId('journeyFormStatus');
  text('journeyFormStatus', 'Saving your journey details…');
  try {
    await saveTwinPatch({
      founder_reality: realityNow,
      destination_contract: destinationNow,
      route_portfolio: [],
      next_turn: null,
      route_proofs: {},
      latest_evolution: null,
    });
    NEXT_TURN = null;
    renderBusinessState();
    if (status) status.textContent = 'Saved. Recalculating your route…';
    await refreshRoutes();
    if (status && byId('routePortfolioStatus')?.textContent.startsWith('3 routes')) {
      status.textContent = 'Journey details saved and routes recalculated.';
    }
  } catch (error) {
    if (status) status.textContent = `Journey details could not be saved: ${error.message}`;
  }
}

async function saveActuals(event) {
  event.preventDefault();
  const fields = [
    ['monthly_revenue', 'metricRevenue', 1],
    ['customer_count', 'metricCustomers', 1],
    ['gross_margin', 'metricMargin', 0.01],
    ['repeat_customer_share', 'metricRepeat', 0.01],
    ['capacity_used', 'metricCapacity', 0.01],
    ['average_ticket', 'metricTicket', 1],
    ['close_rate', 'metricCloseRate', 0.01],
  ];
  const updates = fields
    .map(([key, id, scale]) => [key, byId(id)?.value, scale])
    .filter(([, value]) => value !== undefined && value !== '')
    .map(([key, value, scale]) => [key, Number(value) * scale]);
  if (!updates.length) {
    text('metricsStatus', 'Enter at least one actual value. Blank fields are not saved as zero.');
    return;
  }
  text('metricsStatus', 'Saving owner-reported actuals…');
  const saved = [];
  try {
    for (const [key, value] of updates) {
      await api(`/api/businesses/${BUSINESS_ID}/actuals`, {
        method: 'POST',
        body: JSON.stringify({ key, value }),
      });
      BUSINESS_TWIN[key] = value;
      saved.push(key.replaceAll('_', ' '));
    }
    if (BUSINESS) BUSINESS.twin = BUSINESS_TWIN;
    renderBusinessState();
    text('metricsStatus', `Owner-reported actuals saved: ${saved.join(', ')}.`);
  } catch (error) {
    text('metricsStatus', `Some actuals were saved (${saved.join(', ') || 'none'}). Save stopped after an error: ${error.message}`);
  }
}

async function saveFounderDna(event) {
  event.preventDefault();
  const ids = ['dnaCapital', 'dnaHours', 'dnaExperience', 'dnaRisk'];
  const inputs = ids.map(byId);
  if (inputs.some((input) => !input?.value.trim())) {
    text('dnaStatus', 'Enter all four founder profile values so the derived score does not rely on defaults.');
    return;
  }
  const profile = {
    capital: Number(byId('dnaCapital').value),
    hours_per_week: Number(byId('dnaHours').value),
    experience_years: Number(byId('dnaExperience').value),
    risk_tolerance: Number(byId('dnaRisk').value),
  };
  text('dnaStatus', 'Saving founder profile…');
  try {
    FOUNDER_DNA = await api('/api/founder-dna', {
      method: 'POST',
      body: JSON.stringify({ profile }),
    });
    const dna = FOUNDER_DNA.dna || {};
    text('businessDna', Object.entries(dna).length
      ? `Derived from your saved founder profile: ${Object.entries(dna).map(([key, value]) => `${key.replaceAll('_', ' ')} ${value}`).join(' · ')}`
      : 'No derived founder signals are available.');
    text('dnaStatus', 'Founder profile saved.');
    renderProgress();
  } catch (error) {
    text('dnaStatus', `Founder profile was not saved: ${error.message}`);
  }
}

async function recordProof(event) {
  event.preventDefault();
  const proofName = byId('proofName')?.value || '';
  const value = byId('proofNote')?.value.trim() || '';
  if (!proofName || !value) {
    text('proofStatus', 'Enter evidence for the currently active checkpoint.');
    return;
  }
  text('proofStatus', 'Recording this as owner-reported evidence…');
  try {
    const evidence = await api('/api/evidence', {
      method: 'POST',
      body: JSON.stringify({
        business_id: BUSINESS_ID,
        classification: 'user_assertion',
        value,
        source_ref: `route_checkpoint:${proofName}`,
        confidence: 60,
      }),
    });
    const routeProofs = { ...(BUSINESS_TWIN.route_proofs || {}) };
    routeProofs[proofName] = {
      evidence_id: evidence.id,
      classification: evidence.classification,
      recorded_at: new Date().toISOString(),
    };
    await saveTwinPatch({ route_proofs: routeProofs });
    byId('proofNote').value = '';
    NEXT_TURN = null;
    await refreshRoutes();
    text('proofStatus', 'Evidence recorded as an owner assertion; it is not independently verified.');
  } catch (error) {
    text('proofStatus', `Evidence was not recorded: ${error.message}`);
  }
}

async function runCounterfactual(event) {
  event.preventDefault();
  const d = destination();
  const ticket = Number(BUSINESS_TWIN.average_ticket);
  const margin = Number(BUSINESS_TWIN.gross_margin);
  const closeRate = Number(BUSINESS_TWIN.close_rate);
  if (!d || !hasValue(BUSINESS_TWIN, 'average_ticket') || !hasValue(BUSINESS_TWIN, 'gross_margin')
      || !hasValue(BUSINESS_TWIN, 'close_rate') || ticket <= 0 || margin <= 0 || closeRate <= 0) {
    text('counterfactualResult', 'Save a destination, average sale amount, gross margin above 0%, and close rate above 0% before calculating.');
    return;
  }
  text('counterfactualResult', 'Calculating from saved actuals…');
  try {
    const result = await api('/api/route/counterfactual', {
      method: 'POST',
      body: JSON.stringify({
        destination: d,
        avg_ticket: ticket,
        gross_margin: margin,
        close_rate: closeRate,
      }),
    });
    byId('counterfactualResult').innerHTML = `Model estimate based on your saved inputs:
      <ul><li>Monthly revenue needed: <b>${escapeHtml(money(result.monthly_revenue_needed))}</b></li>
      <li>Customers needed: <b>${escapeHtml(result.customers_needed)}</b></li>
      <li>Qualified opportunities needed: <b>${escapeHtml(result.qualified_opportunities_needed)}</b></li></ul>
      <small>This is a counterfactual estimate, not a guaranteed result.</small>`;
  } catch (error) {
    text('counterfactualResult', `Counterfactual could not be calculated: ${error.message}`);
  }
}

async function compareReroute(event) {
  event.preventDefault();
  const oldReality = reality();
  const d = destination();
  if (!oldReality || !d) {
    text('whatIfStatus', 'Save a founder reality and destination before comparing scenarios.');
    return;
  }
  const cash = numberValue(byId('whatIfCash')?.value);
  const hours = numberValue(byId('whatIfHours')?.value);
  const newReality = {
    ...oldReality,
    cash: cash === null ? oldReality.cash : cash,
    hours_per_week: hours === null ? oldReality.hours_per_week : hours,
  };
  text('whatIfStatus', 'Comparing the scenario. Your saved profile will not change…');
  try {
    const result = await api('/api/route/reroute', {
      method: 'POST',
      body: JSON.stringify({ old_reality: oldReality, new_reality: newReality, destination: d }),
    });
    const scenarioSpendable = Math.max(0, Math.min(d.max_risk_cash, newReality.cash - newReality.reserve_floor));
    const changed = Array.isArray(result.changed) && result.changed.length ? result.changed.join(', ') : 'No route inputs changed';
    text('whatIfStatus', `Scenario only — saved profile unchanged. Changed: ${changed}. Scenario spendable cash envelope: ${money(scenarioSpendable)}.`);
  } catch (error) {
    text('whatIfStatus', `Scenario could not be compared: ${error.message}`);
  }
}

function continueNextTurn() {
  if (!NEXT_TURN?.action) {
    go('business');
    byId('journeySettings')?.classList.add('on');
    text('journeyFormStatus', 'Set your destination and founder reality to calculate a next turn.');
    byId('journeyForm')?.scrollIntoView({ block: 'center', behavior: 'smooth' });
    return;
  }
  go('do');
  text('executionStatus', `Next Turn: ${NEXT_TURN.action}. Choose an available EXECUTE, PREPARE or GUIDE action below. No action has been completed yet.`);
}

function showRoute() {
  go('business');
  byId('routePanel')?.scrollIntoView({ block: 'start', behavior: 'smooth' });
}

async function loadExecution() {
  if (!BUSINESS_ID) return;
  text('executionStatus', 'Checking real execution connections…');
  try {
    const catalog = await api('/api/execution/catalog');
    byId('executionPoints').innerHTML = (catalog.points || []).map((point) => {
      const connection = point.connection?.state || 'UNKNOWN';
      const connected = connection === 'CONNECTED' || connection === 'READY';
      const modeLabel = point.mode === 'GUIDE'
        ? 'Open official step'
        : point.mode === 'PREPARE'
          ? 'Prepare with Genesis'
          : 'Execute with Genesis';
      const unavailable = point.mode === 'EXECUTE' && !connected;
      return `<div class="execpoint">
        <div class="eyebrow">${escapeHtml(point.mode)} · Risk ${escapeHtml(point.risk_tier)}</div>
        <h3>${escapeHtml(point.title)}</h3>
        <p class="muted">${escapeHtml(point.provider)} · ${escapeHtml(point.capability)}</p>
        <div class="${connected ? 'good' : 'warn'}">${escapeHtml(connection)}</div>
        ${unavailable
          ? `<button class="sec" type="button" disabled>Connection required</button>`
          : `<button class="cta" type="button" data-action="start-action" data-key="${escapeHtml(point.key)}" data-risk="${escapeHtml(point.risk_tier)}">${modeLabel}</button>`}
      </div>`;
    }).join('');
    text('executionStatus', 'Execution Center is live. Provider actions only execute when the required account is connected.');
    await loadActions();
  } catch (error) {
    text('executionStatus', `Execution unavailable: ${error.message}`);
  }
}

async function startAction(key, risk) {
  const payload = {};
  if (BUSINESS?.name) payload.business_name = BUSINESS.name;
  if (NEXT_TURN?.action) payload.goal = NEXT_TURN.action;
  if (key === 'email_send') {
    const to = window.prompt('Recipient email');
    const subject = window.prompt('Subject');
    const body = window.prompt('Message');
    if (to === null || subject === null || body === null) return;
    payload.to = to.trim();
    payload.subject = subject.trim();
    payload.body = body.trim();
  }
  if (key === 'crm_customer_create') {
    const email = window.prompt('Customer email');
    const givenName = window.prompt('First name');
    if (email === null || givenName === null) return;
    payload.email_address = email.trim();
    payload.given_name = givenName.trim();
  }
  if (key === 'payment_link_create') {
    const name = window.prompt('What are you selling?');
    const amount = window.prompt('Price in cents');
    if (name === null || amount === null || !Number.isFinite(Number(amount)) || Number(amount) <= 0) return;
    payload.name = name.trim();
    payload.amount_cents = Number(amount);
    payload.currency = 'USD';
  }

  try {
    const action = await api('/api/execution/actions', {
      method: 'POST',
      body: JSON.stringify({ business_id: BUSINESS_ID, point_key: key, payload }),
    });
    if (Number(risk) >= 2) {
      const approved = window.confirm('Approve this Genesis action? It may create an external record or send/prepare a consequential step.');
      if (!approved) {
        await loadActions();
        return;
      }
      await api(`/api/execution/actions/${action.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ confirm: true }),
      });
    }

    const performed = await api(`/api/execution/actions/${action.id}/perform`, {
      method: 'POST',
      body: '{}',
    });
    let message = `Genesis action status: ${performed.status}.`;

    if (performed.status === 'PREPARED' || performed.status === 'EXECUTED') {
      const verified = await api(`/api/execution/actions/${action.id}/verify`, {
        method: 'POST',
        body: '{}',
      });
      message = `Genesis verified this action from recorded evidence: ${verified.status}.`;
    } else if (performed.status === 'GUIDED') {
      const officialUrl = performed.result?.official_url;
      if (officialUrl) {
        message += ` Complete the step yourself at ${officialUrl}. Genesis has not filed or submitted it.`;
      }
      message += ' Use “Record official confirmation” only after you complete the step.';
      byId('executionStatus').innerHTML = `${escapeHtml(message)}
        <button class="sec" type="button" data-action="confirm-guided" data-id="${escapeHtml(action.id)}">Record official confirmation</button>`;
    } else {
      message += ' No external completion is assumed.';
      text('executionStatus', message);
    }
    if (performed.status !== 'GUIDED') text('executionStatus', message);
    await loadActions();
  } catch (error) {
    text('executionStatus', `Genesis did not mark this complete. ${error.message}`);
    await loadActions();
  }
}

async function confirmGuidedAction(actionId) {
  const reference = window.prompt('Enter the confirmation/reference from the official destination. Leave blank to keep this action unverified.');
  if (!reference?.trim()) return;
  try {
    await api(`/api/execution/actions/${actionId}/evidence`, {
      method: 'POST',
      body: JSON.stringify({
        evidence_type: 'user_confirmation',
        summary: 'User supplied the official completion reference.',
        external_reference: reference.trim(),
      }),
    });
    const verified = await api(`/api/execution/actions/${actionId}/verify`, {
      method: 'POST',
      body: '{}',
    });
    text('executionStatus', `Official user-confirmed evidence recorded. Action status: ${verified.status}.`);
    await loadActions();
  } catch (error) {
    text('executionStatus', `Genesis did not mark this complete. ${error.message}`);
  }
}

async function loadActions() {
  if (!BUSINESS_ID) return;
  const actions = await api(`/api/businesses/${BUSINESS_ID}/actions`);
  ACTIONS = Array.isArray(actions) ? actions : [];
  const output = byId('recentActions');
  if (output) {
    output.innerHTML = ACTIONS.length
      ? ACTIONS.slice(0, 8).map((action) => `<div class="task"><div><b>${escapeHtml(action.point_key)}</b><br><span class="muted">${escapeHtml(action.status)}</span></div></div>`).join('')
      : 'No execution actions yet.';
  }
  renderProgress();
  renderOverview();
}

function appendBubble(kind, value) {
  const bubble = document.createElement('div');
  bubble.className = `bubble ${kind}`;
  bubble.textContent = value;
  byId('askMessages')?.append(bubble);
  bubble.scrollIntoView({ block: 'nearest' });
}

async function askGenesis(event) {
  event.preventDefault();
  const input = byId('askInput');
  const question = input?.value.trim() || '';
  if (!question) return;
  appendBubble('user', question);
  input.value = '';
  try {
    const result = await api('/api/consultant/generate', {
      method: 'POST',
      body: JSON.stringify({
        objective: question,
        constraints: { business_id: BUSINESS_ID },
      }),
    });
    const candidates = (result.candidates || []).map((candidate, index) => {
      const name = candidate.title || candidate.name || candidate.archetype || `Option ${index + 1}`;
      const reason = candidate.rationale || candidate.reason || candidate.why || '';
      return `${index + 1}. ${name}${reason ? ` — ${reason}` : ''}`;
    });
    appendBubble('', candidates.length
      ? `${result.notice || 'Planning values remain assumptions until verified.'}\n${candidates.join('\n')}`
      : result.notice || 'Genesis returned no business candidates for this request.');
  } catch (error) {
    appendBubble('', `Genesis could not answer this request: ${error.message}`);
  }
}

function addCommunityPost(post) {
  const mine = post.is_mine === true;
  return `<article class="task community-post">
    <div class="community-post-body">
      <h3>${escapeHtml(post.display_name)} · ${escapeHtml(post.category)}</h3>
      <p class="muted">${escapeHtml(post.body)}</p>
      <div class="community-actions">
        <button class="sec" type="button" data-action="community-replies" data-post-id="${escapeHtml(post.id)}">Replies</button>
        <button class="sec" type="button" data-action="community-report" data-post-id="${escapeHtml(post.id)}">Report</button>
        ${mine
          ? `<button class="sec" type="button" data-action="community-delete" data-post-id="${escapeHtml(post.id)}">Delete</button>`
          : `<button class="sec" type="button" data-action="community-block" data-post-id="${escapeHtml(post.id)}">Block author</button>`}
      </div>
      <div id="replies-${escapeHtml(post.id)}" class="community-replies"></div>
      <form class="reply-form" data-post-id="${escapeHtml(post.id)}">
        <input name="display_name" aria-label="Reply display name" placeholder="Your display name" value="Founder" maxlength="80">
        <input name="body" aria-label="Reply to post" placeholder="Write a reply" maxlength="1500" required>
        <button class="sec" type="submit">Reply</button>
      </form>
    </div>
  </article>`;
}

async function loadCommunity() {
  const output = byId('communityFeed');
  if (!output) return;
  output.textContent = 'Loading community…';
  try {
    const category = byId('communityFilter')?.value || 'ALL';
    const query = category === 'ALL' ? '' : `?category=${encodeURIComponent(category)}`;
    const posts = await api(`/api/community${query}`);
    output.innerHTML = Array.isArray(posts) && posts.length
      ? posts.map(addCommunityPost).join('')
      : '<p class="muted">No community posts yet. Share an experience or ask a question to start the feed.</p>';
  } catch (error) {
    output.textContent = `Community unavailable: ${error.message}`;
  }
}

async function createCommunityPost(event) {
  event.preventDefault();
  const form = event.target;
  const body = new FormData(form);
  try {
    await api('/api/community', {
      method: 'POST',
      body: JSON.stringify({
        category: byId('communityCategory').value,
        display_name: String(body.get('display_name') || 'Founder').trim(),
        body: String(body.get('body') || '').trim(),
      }),
    });
    form.reset();
    byId('communityCategory').value = byId('communityCategory').dataset.selected || 'ASK';
    text('communityStatus', 'Post shared with the community.');
    await loadCommunity();
  } catch (error) {
    text('communityStatus', `Post was not shared: ${error.message}`);
  }
}

async function loadReplies(postId) {
  const target = byId(`replies-${postId}`);
  if (!target) return;
  try {
    const replies = await api(`/api/community/${postId}/replies`);
    target.innerHTML = replies.length
      ? replies.map((reply) => `<p class="muted"><b>${escapeHtml(reply.display_name)}</b>: ${escapeHtml(reply.body)}</p>`).join('')
      : '<p class="muted">No replies yet.</p>';
  } catch (error) {
    target.textContent = `Replies unavailable: ${error.message}`;
  }
}

async function submitReply(event) {
  event.preventDefault();
  const form = event.target;
  const body = new FormData(form);
  const postId = form.dataset.postId;
  try {
    await api(`/api/community/${postId}/replies`, {
      method: 'POST',
      body: JSON.stringify({
        display_name: String(body.get('display_name') || 'Founder').trim(),
        body: String(body.get('body') || '').trim(),
      }),
    });
    form.reset();
    await loadReplies(postId);
  } catch (error) {
    text('communityStatus', `Reply was not shared: ${error.message}`);
  }
}

async function communityAction(action, postId) {
  try {
    if (action === 'community-replies') return await loadReplies(postId);
    if (action === 'community-report') {
      const reason = window.prompt('Why are you reporting this post?');
      if (!reason?.trim()) return;
      await api(`/api/community/${postId}/report`, {
        method: 'POST',
        body: JSON.stringify({ reason: reason.trim() }),
      });
      text('communityStatus', 'Report submitted for review.');
    } else if (action === 'community-block') {
      if (!window.confirm('Block this founder and hide their posts from your feed?')) return;
      await api(`/api/community/${postId}/block-author`, {
        method: 'POST',
        body: '{}',
      });
      text('communityStatus', 'Founder blocked; refreshing your feed.');
      await loadCommunity();
    } else if (action === 'community-delete') {
      if (!window.confirm('Delete this post?')) return;
      await api(`/api/community/${postId}`, { method: 'DELETE' });
      text('communityStatus', 'Your post was deleted.');
      await loadCommunity();
    }
  } catch (error) {
    text('communityStatus', `Community action failed: ${error.message}`);
  }
}

document.addEventListener('click', (event) => {
  const origin = event.target instanceof Element ? event.target : null;
  const button = origin?.closest('[data-action]');
  if (!button) return;
  const action = button.dataset.action;
  if (action === 'auth') authenticate(button.dataset.kind);
  else if (action === 'navigate') go(button.dataset.view);
  else if (action === 'toggle') byId(button.dataset.target)?.classList.toggle('on');
  else if (action === 'see-evolution') seeEvolution();
  else if (action === 'start-action') startAction(button.dataset.key, Number(button.dataset.risk));
  else if (action === 'confirm-guided') confirmGuidedAction(button.dataset.id);
  else if (action === 'community-mode') {
    const category = button.dataset.category || 'ALL';
    if (category !== 'ALL') {
      const select = byId('communityCategory');
      select.value = category;
      select.dataset.selected = category;
    }
    byId('communityFilter').value = category;
    byId('communityForm')?.scrollIntoView({ block: 'center', behavior: 'smooth' });
    byId('communityBody')?.focus();
    loadCommunity();
  } else if (action.startsWith('community-')) {
    communityAction(action, button.dataset.postId);
  }
});

document.addEventListener('submit', (event) => {
  if (event.target.id === 'authForm') {
    event.preventDefault();
    authenticate(event.submitter?.dataset.kind || 'login');
  } else if (event.target.id === 'askForm') askGenesis(event);
  else if (event.target.id === 'communityForm') createCommunityPost(event);
  else if (event.target.matches('.reply-form')) submitReply(event);
});

byId('communityCategory')?.addEventListener('change', (event) => {
  event.currentTarget.dataset.selected = event.currentTarget.value;
});
byId('communityFilter')?.addEventListener('change', loadCommunity);

bootstrap();
