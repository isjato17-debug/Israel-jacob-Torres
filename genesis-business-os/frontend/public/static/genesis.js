'use strict';

let CSRF = '';
let BUSINESS_ID = '';

const byId = (id) => document.getElementById(id);
const text = (id, value) => {
  const element = byId(id);
  if (element) element.textContent = value;
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
  document.querySelectorAll('.view').forEach((view) => view.classList.remove('on'));
  byId(id)?.classList.add('on');
  document.querySelectorAll('nav button').forEach((button) => {
    button.classList.toggle('on', button.dataset.view === id);
  });
  if (id === 'do') loadExecution();
  if (id === 'community') loadCommunity();
  if (id === 'business') loadBusinessDNA();
  window.scrollTo(0, 0);
}

async function bootstrap() {
  try {
    await api('/api/me');
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
    const tenantName = byId('tenant')?.value.trim() || 'My Business';
    const email = byId('email')?.value.trim() || '';
    const password = byId('password')?.value || '';
    const body = kind === 'register'
      ? { tenant_name: tenantName, email, password }
      : { email, password };
    const result = await api(`/api/auth/${kind}`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
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
    const name = byId('tenant')?.value.trim() || 'My Business';
    const business = await api('/api/businesses', {
      method: 'POST',
      body: JSON.stringify({ name, twin: {} }),
    });
    BUSINESS_ID = business.id;
  } else {
    BUSINESS_ID = businesses[0].id;
  }
  await loadExecution();
}

async function loadBusinessDNA() {
  const output = byId('businessDna');
  if (!output) return;
  try {
    const result = await api('/api/founder-dna');
    const entries = Object.entries(result.dna || {});
    output.textContent = entries.length
      ? entries.map(([key, value]) => `${key.replaceAll('_', ' ')}: ${value}`).join(' · ')
      : 'No Business DNA profile has been saved yet.';
  } catch (error) {
    output.textContent = `Business DNA unavailable: ${error.message}`;
  }
}

async function seeEvolution() {
  if (!BUSINESS_ID) return;
  const askNumber = (label, fallback) => {
    const value = window.prompt(label, String(fallback));
    return value === null ? null : Number(value || fallback);
  };
  const revenue = askNumber('Current monthly revenue (0 if not launched yet)', 0);
  if (revenue === null) return;
  const repeatPercent = askNumber('About what % of customers are repeat customers? (0–100)', 0);
  if (repeatPercent === null) return;
  const marginPercent = askNumber('Estimated gross margin % (example: 60)', 50);
  if (marginPercent === null) return;
  const capacityPercent = askNumber('About what % of your current capacity is being used?', 50);
  if (capacityPercent === null) return;
  const cash = askNumber('Cash available for the business', 300);
  if (cash === null) return;
  const reserve = askNumber('Amount you want Genesis to protect', 200);
  if (reserve === null) return;
  const goal = askNumber('Monthly income destination', 5000);
  if (goal === null) return;

  const output = byId('evolutionResult');
  output?.classList.add('on');
  if (output) output.textContent = 'Comparing possible futures…';
  try {
    const result = await api('/api/route/evolution', {
      method: 'POST',
      body: JSON.stringify({
        reality: {
          cash,
          reserve_floor: reserve,
          hours_per_week: 15,
          skills: [],
          assets: ['phone'],
          location: '',
        },
        destination: {
          target_monthly_owner_income: goal,
          horizon_months: 12,
          max_risk_cash: Math.max(0, cash - reserve),
        },
        monthly_revenue: revenue,
        repeat_customer_share: repeatPercent / 100,
        gross_margin: marginPercent / 100,
        capacity_used: capacityPercent / 100,
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
      <small class="muted">${escapeHtml(result.disclaimer)}</small>`;
  } catch (error) {
    output.textContent = `Genesis could not calculate the evolution: ${error.message}`;
  }
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
  const payload = { business_name: 'My Business', goal: 'Build a profitable validated business' };
  if (key === 'email_send') {
    payload.to = window.prompt('Recipient email') || '';
    payload.subject = window.prompt('Subject') || '';
    payload.body = window.prompt('Message') || '';
  }
  if (key === 'crm_customer_create') {
    payload.email_address = window.prompt('Customer email') || '';
    payload.given_name = window.prompt('First name') || '';
  }
  if (key === 'payment_link_create') {
    payload.name = window.prompt('What are you selling?') || 'Service';
    payload.amount_cents = Number(window.prompt('Price in cents') || 0);
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
  const output = byId('recentActions');
  if (!output) return;
  output.innerHTML = actions.length
    ? actions.slice(0, 8).map((action) => `<div class="task"><div><b>${escapeHtml(action.point_key)}</b><br><span class="muted">${escapeHtml(action.status)}</span></div></div>`).join('')
    : 'No execution actions yet.';
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
  if (event.target.id === 'askForm') askGenesis(event);
  else if (event.target.id === 'communityForm') createCommunityPost(event);
  else if (event.target.matches('.reply-form')) submitReply(event);
});

byId('communityCategory')?.addEventListener('change', (event) => {
  event.currentTarget.dataset.selected = event.currentTarget.value;
});
byId('communityFilter')?.addEventListener('change', loadCommunity);

bootstrap();
