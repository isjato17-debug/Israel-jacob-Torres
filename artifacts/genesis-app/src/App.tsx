import { useEffect, useRef, useState } from 'react';
import { ArrowRight, BriefcaseBusiness, CircleHelp, Home as HomeIcon, Play, UsersRound } from 'lucide-react';

type ViewId = 'home' | 'business' | 'do' | 'community' | 'ask';
type AnyRecord = Record<string, any>;

const navItems: { id: ViewId; label: string; Icon: typeof HomeIcon }[] = [
  { id: 'home', label: 'Home', Icon: HomeIcon },
  { id: 'business', label: 'My Business', Icon: BriefcaseBusiness },
  { id: 'do', label: 'Do It', Icon: Play },
  { id: 'community', label: 'Community', Icon: UsersRound },
  { id: 'ask', label: 'Ask B.I.G.', Icon: CircleHelp },
];

function readCookie(name: string) {
  return document.cookie.split('; ').find((part) => part.startsWith(`${name}=`))?.split('=').slice(1).join('=') || '';
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}

function App() {
  const [view, setView] = useState<ViewId>('home');
  const [authVisible, setAuthVisible] = useState(true);
  const [tenant, setTenant] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authMessage, setAuthMessage] = useState('Checking session…');
  const [authBusy, setAuthBusy] = useState(false);
  const csrfRef = useRef('');
  const [businessId, setBusinessId] = useState<string | number>('');
  const [whyOpen, setWhyOpen] = useState(false);
  const [evolutionOpen, setEvolutionOpen] = useState(false);
  const [evolutionLoading, setEvolutionLoading] = useState(false);
  const [evolution, setEvolution] = useState<AnyRecord | null>(null);
  const [evolutionError, setEvolutionError] = useState('');
  const [executionStatus, setExecutionStatus] = useState('Loading execution points…');
  const [executionPoints, setExecutionPoints] = useState<AnyRecord[]>([]);
  const [executionLoading, setExecutionLoading] = useState(false);
  const [actionItems, setActionItems] = useState<AnyRecord[]>([]);
  const [actionError, setActionError] = useState('');
  const [communityPosts, setCommunityPosts] = useState<AnyRecord[]>([]);
  const [communityMessage, setCommunityMessage] = useState('Founder posts load from your community.');

  async function api(path: string, options: RequestInit = {}): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    new Headers(options.headers).forEach((value, key) => { headers[key] = value; });
    if (csrfRef.current && options.method && options.method !== 'GET') headers['X-CSRF-Token'] = csrfRef.current;
    const response = await fetch(path, { ...options, credentials: 'same-origin', headers });
    let body: any;
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

  async function ensureBusiness() {
    const businesses = await api('/api/businesses');
    if (!businesses.length) {
      const created = await api('/api/businesses', {
        method: 'POST',
        body: JSON.stringify({ name: tenant || 'My Business', twin: {} }),
      });
      setBusinessId(created.id);
      await loadExecution(created.id);
    } else {
      setBusinessId(businesses[0].id);
      await loadExecution(businesses[0].id);
    }
  }

  async function loadActions(id = businessId) {
    if (!id) return;
    setActionError('');
    try {
      const actions = await api(`/api/businesses/${id}/actions`);
      setActionItems(Array.isArray(actions) ? actions : []);
    } catch (error) {
      setActionError(`Recent execution could not be loaded: ${errorMessage(error)}`);
    }
  }

  async function loadExecution(id = businessId) {
    if (!id) return;
    setExecutionLoading(true);
    setExecutionStatus('Checking real execution connections…');
    try {
      const catalog = await api('/api/execution/catalog');
      setExecutionPoints(Array.isArray(catalog.points) ? catalog.points : []);
      setExecutionStatus('Execution Center is live. Provider actions only execute when the required account is connected.');
      await loadActions(id);
    } catch (error) {
      setExecutionPoints([]);
      setExecutionStatus(`Execution unavailable: ${errorMessage(error)}`);
    } finally {
      setExecutionLoading(false);
    }
  }

  async function loadCommunity() {
    setCommunityMessage('Loading founder feed…');
    try {
      const response = await api('/api/community');
      setCommunityPosts(Array.isArray(response.posts) ? response.posts.slice(0, 10) : []);
      setCommunityMessage(response.posts?.length ? '' : 'No community posts are available yet.');
    } catch (error) {
      setCommunityPosts([]);
      setCommunityMessage(`Founder feed unavailable: ${errorMessage(error)}`);
    }
  }

  useEffect(() => {
    let active = true;
    async function bootstrap() {
      try {
        await api('/api/me');
        const token = decodeURIComponent(readCookie('genesis_csrf'));
        if (!active) return;
        csrfRef.current = token;
        setAuthVisible(false);
        const businesses = await api('/api/businesses');
        let id: string | number;
        if (!businesses.length) {
          const created = await api('/api/businesses', {
            method: 'POST',
            body: JSON.stringify({ name: tenant || 'My Business', twin: {} }),
          });
          id = created.id;
        } else {
          id = businesses[0].id;
        }
        if (!active) return;
        setBusinessId(id);
        await loadExecution(id);
      } catch {
        if (active) setAuthMessage('Sign in or create a workspace.');
      }
    }
    void bootstrap();
    return () => { active = false; };
    // Bootstrap is intentionally a single session check on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function authenticate(kind: 'login' | 'register') {
    setAuthBusy(true);
    setAuthMessage('Working…');
    try {
      const payload = kind === 'register'
        ? { tenant_name: tenant || 'My Business', email, password }
        : { email, password };
      const result = await api(`/api/auth/${kind}`, { method: 'POST', body: JSON.stringify(payload) });
      csrfRef.current = result.csrf || '';
      setAuthVisible(false);
      await ensureBusiness();
      setAuthMessage('');
    } catch (error) {
      setAuthMessage(errorMessage(error));
    } finally {
      setAuthBusy(false);
    }
  }

  function navigate(next: ViewId) {
    setView(next);
    if (next === 'do') void loadExecution();
    if (next === 'community') void loadCommunity();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function seeEvolution() {
    if (!businessId) return;
    const revenue = Number(window.prompt('Current monthly revenue (0 if not launched yet)') || 0);
    const repeat = Number(window.prompt('About what % of customers are repeat customers? (0–100)') || 0) / 100;
    const margin = Number(window.prompt('Estimated gross margin % (example: 60)') || 50) / 100;
    const capacity = Number(window.prompt('About what % of your current capacity is being used?') || 50) / 100;
    const cash = Number(window.prompt('Cash available for the business') || 300);
    const reserve = Number(window.prompt('Amount you want B.I.G. to protect') || 200);
    const goal = Number(window.prompt('Monthly income destination') || 5000);
    setEvolutionOpen(true);
    setEvolutionLoading(true);
    setEvolution(null);
    setEvolutionError('');
    try {
      const result = await api('/api/route/evolution', {
        method: 'POST',
        body: JSON.stringify({
          reality: { cash, reserve_floor: reserve, hours_per_week: 15, skills: [], assets: ['phone'], location: '' },
          destination: { target_monthly_owner_income: goal, horizon_months: 12, max_risk_cash: Math.max(0, cash - reserve) },
          monthly_revenue: revenue,
          repeat_customer_share: repeat,
          gross_margin: margin,
          capacity_used: capacity,
        }),
      });
      setEvolution(result);
    } catch (error) {
      setEvolutionError(`B.I.G. could not calculate the evolution: ${errorMessage(error)}`);
    } finally {
      setEvolutionLoading(false);
    }
  }

  async function startAction(point: AnyRecord) {
    let payload: AnyRecord = { business_name: 'My Business', goal: 'Build a profitable validated business' };
    if (point.key === 'email_send') {
      payload = { to: window.prompt('Recipient email') || '', subject: window.prompt('Subject') || '', body: window.prompt('Message') || '' };
    }
    if (point.key === 'crm_customer_create') {
      payload = { email_address: window.prompt('Customer email') || '', given_name: window.prompt('First name') || '' };
    }
    if (point.key === 'payment_link_create') {
      payload = {
        name: window.prompt('What are you selling?') || 'Service',
        amount_cents: Number(window.prompt('Price in cents') || 0),
        currency: 'USD',
      };
    }
    try {
      const action = await api('/api/execution/actions', {
        method: 'POST',
        body: JSON.stringify({ business_id: businessId, point_key: point.key, payload }),
      });
      if (point.risk_tier >= 2) {
        if (!window.confirm('Approve this B.I.G. action? It may create an external record or send/prepare a consequential step.')) {
          await loadActions();
          return;
        }
        await api(`/api/execution/actions/${action.id}/approve`, {
          method: 'POST',
          body: JSON.stringify({ confirm: true }),
        });
      }
      const performed = await api(`/api/execution/actions/${action.id}/perform`, { method: 'POST', body: '{}' });
      window.alert(`${performed.status}${performed.result?.official_url ? `\n${performed.result.official_url}` : ''}`);
      await loadActions();
    } catch (error) {
      window.alert(`B.I.G. did not mark this complete. ${errorMessage(error)}`);
      await loadActions();
    }
  }

  const selectedEvolution = evolution?.recommended_evolution;
  const futureOptions = Array.isArray(evolution?.possible_futures) ? evolution.possible_futures : [];

  return (
    <>
      <main className="app-wrap">
        <header className="topbar">
          <div className="brand"><span className="logo">G</span>B.I.G. Business Inside Genesis</div>
          <span className="avatar" aria-label="Owner profile">IJ</span>
        </header>

        <section className={`view ${view === 'home' ? 'on' : ''}`} aria-hidden={view !== 'home'}>
          <div className="eyebrow">Start with what you have</div>
          <h1 className="hero">Build toward what you want.</h1>
          <p className="lead muted">B.I.G. keeps business simple. Tell it your goal, see your best next move, and let B.I.G. help you get it done.</p>
          <div className="grid">
            <div className="card">
              <div className="eyebrow">Your next best move</div>
              <h2>Get your first 3 paying customers before spending more.</h2>
              <p className="muted">You have enough to test demand now. Validate the service before using more of your startup money.</p>
              <div className="pills"><span className="pill">Est. cost $40</span><span className="pill">1–3 days</span><span className="pill">Low risk</span></div>
              <button className="cta" data-testid="button-do-it" onClick={() => navigate('do')}>Do it with B.I.G. <ArrowRight size={16} /></button>{' '}
              <button className="sec" data-testid="button-see-why" aria-expanded={whyOpen} onClick={() => setWhyOpen(!whyOpen)}>See why</button>
              <div className={`reveal ${whyOpen ? 'on' : ''}`} id="why">B.I.G. compared your capital, reserve, time, skills, startup costs and customer path. Real customers give you evidence before you make larger purchases.</div>
            </div>
            <div className="card center">
              <div className="eyebrow">Business progress</div><div className="ring"><span>42%</span></div>
              <b>You're moving forward.</b><p className="muted">B.I.G. tracks the complicated parts in the background.</p>
            </div>
          </div>
          <div className="three">
            <div className="card"><div className="eyebrow">Money available</div><h2>$300</h2><p className="muted">B.I.G. builds inside your real budget.</p></div>
            <div className="card"><div className="eyebrow">Coming next</div><h3>Set up the business</h3><p className="muted">Requirements appear only when relevant.</p></div>
            <div className="card"><div className="eyebrow">What if?</div><h3>What if I only spend $100?</h3><button className="sec" onClick={() => navigate('ask')}>Ask B.I.G.</button></div>
          </div>
          <div className="card evo" style={{ marginTop: 16 }}>
            <div className="eyebrow">B.I.G. Evolution</div><h2>Your business can change as the evidence changes.</h2>
            <p className="muted">B.I.G. quietly compares possible futures, then shows you one recommended move. No extra dashboard.</p>
            <button className="cta" data-testid="button-best-future" onClick={() => void seeEvolution()}>See my best future <ArrowRight size={16} /></button>
            <div className={`reveal ${evolutionOpen ? 'on' : ''}`} role="status" data-testid="status-evolution">
              {evolutionLoading && <p>Comparing possible futures…</p>}
              {evolutionError && <p className="error-text">{evolutionError}</p>}
              {selectedEvolution && <>
                <div className="eyebrow">{evolution.generation}</div><h3>B.I.G. recommends: {selectedEvolution.title}</h3>
                <p>{selectedEvolution.why}</p><div className="pills"><span className="pill">Fit score {selectedEvolution.score}/100</span><span className="pill">Cash envelope ${selectedEvolution.estimated_cash_needed}</span></div>
                <b>Next:</b> {selectedEvolution.next_action}<div className="muted" style={{ marginTop: 14 }}>Possible futures compared</div>
                {futureOptions.map((future: AnyRecord, index: number) => <div key={`${future.title}-${index}`}><small>{future.title} · {future.score}/100</small><div className="futurebar"><i style={{ width: `${Math.max(0, Math.min(100, Number(future.score)))}%` }} /></div></div>)}
                <small className="muted">{evolution.disclaimer}</small>
              </>}
            </div>
          </div>
        </section>

        <section className={`view ${view === 'business' ? 'on' : ''}`} aria-hidden={view !== 'business'}>
          <div className="eyebrow">My Business</div><h1 className="hero">One clear journey.</h1>
          <p className="lead muted">No giant checklist. B.I.G. reveals each stage when you need it.</p>
          <div className="journey">
            <div className="stage done"><b>Idea</b><br /><small>Chosen</small></div>
            <div className="stage now"><b>2 Setup</b><br /><small>You're here</small></div>
            <div className="stage"><b>3 Launch</b><br /><small>Coming up</small></div>
            <div className="stage"><b>4 Grow</b><br /><small>After launch</small></div>
          </div>
          <div className="card">
            <div className="eyebrow">Mobile detailing</div><h2>Your business at a glance</h2>
            <div className="task"><div><h3>Business model</h3><p className="muted">Mobile service • low fixed overhead</p></div><button className="sec" disabled aria-label="Business model view unavailable">View</button></div>
            <div className="task"><div><h3>My money</h3><p className="muted">$300 capital • reserve protected • validate first</p></div><button className="sec" disabled aria-label="Money details unavailable">View</button></div>
            <div className="task"><div><h3>Setup &amp; requirements</h3><p className="muted">Only supported requirements for your business and location.</p></div><button className="sec" disabled aria-label="Requirements unavailable">Check</button></div>
          </div>
          <div className="card evo" style={{ marginTop: 15 }}>
            <div className="eyebrow">Business DNA · Behind the scenes</div><h3>B.I.G. learns what actually works for this business.</h3>
            <p className="muted">Customer patterns, margins, capacity and verified results improve future recommendations. You only see the move that matters now.</p>
          </div>
        </section>

        <section className={`view ${view === 'do' ? 'on' : ''}`} aria-hidden={view !== 'do'}>
          <div className="eyebrow">Do It</div><h1 className="hero">Real actions. Verified results.</h1>
          <p className="lead muted">B.I.G. separates actions it can execute, work it can prepare, and official steps only you can complete.</p>
          <div className="status" role="status" data-testid="status-execution">{executionLoading ? 'Checking real execution connections…' : executionStatus}</div>
          <div className="execgrid" data-testid="list-execution-points">
            {executionPoints.map((point: AnyRecord) => {
              const state = point.connection?.state || 'UNKNOWN';
              const connected = state === 'CONNECTED' || state === 'READY';
              const label = point.mode === 'GUIDE' ? 'Open official step' : point.mode === 'PREPARE' ? 'Prepare with B.I.G.' : 'Execute with B.I.G.';
              return <div className="execpoint" key={point.key}>
                <div className="eyebrow">{point.mode} · Risk {point.risk_tier}</div><h3>{point.title}</h3>
                <p className="muted">{point.provider} · {point.capability}</p><div className={connected ? 'good' : 'warn'}>{state}</div>
                <button className="cta" data-testid={`button-execute-${point.key}`} onClick={() => void startAction(point)} disabled={!businessId}>{label}</button>
              </div>;
            })}
          </div>
          {!executionLoading && !executionPoints.length && executionStatus.startsWith('Execution unavailable') && <div className="status"><button className="sec" onClick={() => void loadExecution()}>Retry</button></div>}
          <div className="card" style={{ marginTop: 15 }}>
            <div className="eyebrow">Recent execution</div>
            {actionError && <p className="error-text" role="status">{actionError} <button className="sec" onClick={() => void loadActions()}>Retry</button></p>}
            {!actionError && (actionItems.length ? actionItems.slice(0, 8).map((item: AnyRecord, index: number) =>
              <div className="task" key={item.id ?? `${item.point_key}-${index}`}><div><b>{item.point_key}</b><br /><span className="muted">{item.status}</span></div></div>
            ) : <div className="muted">No execution actions yet.</div>)}
          </div>
        </section>

        <section className={`view ${view === 'community' ? 'on' : ''}`} aria-hidden={view !== 'community'}>
          <div className="eyebrow">Community</div><h1 className="hero">Connect. Learn. Share. Grow.</h1>
          <p className="lead muted">Ask other founders, share a win, exchange experience, or make useful connections. Your private business data stays private unless you deliberately share it.</p>
          <div className="three">
            <div className="card"><div className="eyebrow">Ask</div><h3>Get founder experience</h3><p className="muted">Ask practical business questions and learn from people building too.</p><button className="sec" disabled>Ask Community</button></div>
            <div className="card"><div className="eyebrow">Wins</div><h3>Share progress</h3><p className="muted">Celebrate first customers, launches and milestones without exposing private financial data.</p><button className="sec" disabled>Share a Win</button></div>
            <div className="card"><div className="eyebrow">Connect</div><h3>Meet useful people</h3><p className="muted">Find founders by business interest, skill or experience.</p><button className="sec" disabled>Explore</button></div>
          </div>
          <div className="card" style={{ marginTop: 15 }}>
            <div className="eyebrow">Founder feed</div>
            {communityMessage && <div className="status" role="status">{communityMessage}{communityMessage.startsWith('Founder feed unavailable') && <button className="sec" onClick={() => void loadCommunity()}>Retry</button>}</div>}
            {communityPosts.map((post: AnyRecord, index: number) => <div className="task" key={post.id ?? `post-${index}`}><div><h3>{post.display_name} · {post.category}</h3><p className="muted">{post.body}</p></div></div>)}
          </div>
        </section>

        <section className={`view ${view === 'ask' ? 'on' : ''}`} aria-hidden={view !== 'ask'}>
          <div className="eyebrow">Ask B.I.G.</div><h1 className="hero">Your business consultant.</h1>
          <div className="card chat">
            <div className="bubble">Tell me what you're trying to accomplish. You can talk normally: “I have $300 and love cooking,” “I need more customers,” or “What should I do today?”</div>
            <div className="bubble user">What if I only want to risk $100?</div>
            <div className="bubble">Then we protect the other $200. I would redesign the first-customer plan around a $100 maximum and avoid purchases that aren't necessary to validate demand.</div>
            <div className="compose"><input aria-label="Ask B.I.G. anything" placeholder="Ask B.I.G. anything…" disabled /><button className="cta" disabled title="Messaging is not connected in the supplied consumer page">Send</button></div>
          </div>
        </section>
      </main>

      <div className="navbox"><nav aria-label="Main navigation">
        {navItems.map(({ id, label, Icon }) => <button key={id} className={view === id ? 'on' : ''} aria-current={view === id ? 'page' : undefined} data-testid={`nav-${id}`} onClick={() => navigate(id)}>
          <Icon aria-hidden="true" /><span>{label}</span>
        </button>)}
      </nav></div>

      <div className={`authgate ${authVisible ? '' : 'off'}`} aria-hidden={!authVisible}>
        <form className="authcard" onSubmit={(event) => { event.preventDefault(); void authenticate('login'); }}>
          <div className="eyebrow">B.I.G. Business Inside Genesis</div><h2>Open your business workspace</h2>
          <p className="muted">Sign in, or create an owner workspace. B.I.G. stores execution state on the server.</p>
          <input aria-label="Business workspace name" placeholder="Business/workspace name" value={tenant} onChange={(event) => setTenant(event.target.value)} data-testid="input-tenant" />
          <input aria-label="Email" type="email" placeholder="Email" required value={email} onChange={(event) => setEmail(event.target.value)} data-testid="input-email" />
          <input aria-label="Password" type="password" placeholder="Password (12+ characters)" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} data-testid="input-password" />
          <div className="authactions">
            <button className="cta" type="submit" disabled={authBusy} data-testid="button-login">{authBusy ? 'Working…' : 'Sign in'}</button>
            <button className="sec" type="button" disabled={authBusy} onClick={() => void authenticate('register')} data-testid="button-register">Create workspace</button>
          </div>
          <div className={`status ${authMessage && !['Checking session…', 'Sign in or create a workspace.', 'Working…'].includes(authMessage) ? 'error-text' : ''}`} role="status" data-testid="status-auth">{authMessage}</div>
        </form>
      </div>
    </>
  );
}

export default App;
