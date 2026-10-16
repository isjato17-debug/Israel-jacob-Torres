import { useEffect, useState } from "react";
import { call } from "./journey-api";
interface Profile { circumstance: string; work_authorization: string; adult: boolean | null;
  us_resident: boolean | null; all_owners_us_citizens_or_nationals: boolean | null;
  women_owned_50_percent: boolean | null; amount_cents: number; use_of_funds: string; }
interface Packet { id: string; revision: number; opportunity_id: string; content_hash: string;
  integrity_verified: boolean; approval_status: string; packet: Record<string, unknown> | null;
  deadline: string | null; reported_outcome: string; submission_status: string; }
interface FundingView { version: number; profile: Partial<Profile>; funding_gap_cents: number; loan_comparisons: Record<string, unknown>[];
  opportunities: { id: string; name: string; kind: string; source: string; checked_at: string;
    source_status: string; current_status: string; match_status: string; requirements: string[];
    application_requirements: string[]; missing: string[]; deadline_rule: string; reasons: string[] }[];
  applications: Packet[]; immigration: Record<string, string>; restrictions: string[]; }
const initial: Profile = { circumstance: "undisclosed", work_authorization: "uncertain", adult: null,
  us_resident: null, all_owners_us_citizens_or_nationals: null, women_owned_50_percent: null,
  amount_cents: 300000, use_of_funds: "" };
const checks = [["adult", "Applicant is at least 18"], ["us_resident", "Applicant principally resides in the U.S."],
  ["all_owners_us_citizens_or_nationals", "All business owners are U.S. citizens or U.S. nationals"],
  ["women_owned_50_percent", "Business is at least 50% women-owned"]] as const;

export default function FundingPanel({ projectId, onUpdated }: { projectId: string; onUpdated: () => void }) {
  const root = `/v2/projects/${projectId}/funding`;
  const [view, setView] = useState<FundingView | null>(null);
  const [profile, setProfile] = useState(initial);
  const [consent, setConsent] = useState(false); const [busy, setBusy] = useState(false);
  const [error, setError] = useState(""); const [reviewed, setReviewed] = useState<Record<string, boolean>>({});
  const [quote, setQuote] = useState({ principal_cents: 300000, annual_rate_bps: 0, months: 36, upfront_fee_cents: 0 });
  const [comparison, setComparison] = useState<Record<string, unknown>[]>([]);
  useEffect(() => { let live = true;
    call<FundingView>(root).then((v) => { if (live) { setView(v); setComparison(v.loan_comparisons);
      setProfile({ ...initial, amount_cents: v.funding_gap_cents || initial.amount_cents, ...v.profile }); } })
      .catch((e: Error) => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [root]);
  const update = async (path: string, method: string, data: unknown) => {
    setBusy(true); setError("");
    try { const v = await call<FundingView>(root + path, method, data); setView(v);
      setConsent(false); setReviewed({}); onUpdated(); }
    catch (e) { setError(e instanceof Error ? e.message : "Funding update failed safely"); }
    finally { setBusy(false); }
  };
  return <section className="bo-item" data-testid="funding-panel">
    <h4>Funding and immigrant entrepreneur support</h4>
    <p>Private screening and application preparation — not legal advice, verified eligibility or a funding guarantee.
      We reuse your saved idea, selected financial plan and consented Business Passport.</p>
    {view && <><details><summary>Ownership, work authorization, licensing and funding are separate</summary>
      {Object.entries(view.immigration).map(([k, v]) => <p key={k}>{k === "source" ? <a href={v} target="_blank" rel="noreferrer">USCIS guidance</a> : v}</p>)}
      {view.restrictions.map((r) => <p key={r}>{r}</p>)}</details>
      <form onSubmit={(e) => { e.preventDefault(); void update("/profile", "PUT", {
        ...profile, expected_version: view.version, consent: true }); }}>
        <label>Optional entrepreneur circumstance <select className="bo-in" value={profile.circumstance}
          onChange={(e) => setProfile({ ...profile, circumstance: e.target.value })}>
          <option value="undisclosed">Prefer not to say / uncertain</option><option value="citizen_national">U.S. citizen or national</option>
          <option value="permanent_resident">Permanent resident</option><option value="visa_holder">Visa holder</option></select></label>
        <label>Work authorization for intended activities <select className="bo-in" value={profile.work_authorization}
          onChange={(e) => setProfile({ ...profile, work_authorization: e.target.value })}>
          <option value="uncertain">Uncertain — professional review needed</option>
          <option value="customer_declares_authorized">I declare authorization; B.I.G. has not verified it</option>
          <option value="not_authorized">Not authorized for these activities</option></select></label>
        {checks.map(([k, label]) => <label key={k}>{label}<select className="bo-in"
          value={profile[k] === null ? "" : String(profile[k])}
          onChange={(e) => setProfile({ ...profile, [k]: e.target.value === "" ? null : e.target.value === "true" })}>
          <option value="">Unknown / not provided</option><option value="true">Yes — customer declaration</option>
          <option value="false">No</option></select></label>)}
        <label>Requested funding (cents USD)<input className="bo-in" type="number" min="1" max="100000000" step="1"
          required value={profile.amount_cents} onChange={(e) => setProfile({ ...profile, amount_cents: Number(e.target.value) })} /></label>
        <label>Intended use of funds — no identity numbers or immigration documents<textarea className="bo-in" required
          minLength={5} maxLength={2000} value={profile.use_of_funds} data-testid="funding-use"
          onChange={(e) => setProfile({ ...profile, use_of_funds: e.target.value })} /></label>
        <label className="gx-check"><input type="checkbox" checked={consent} data-testid="funding-consent"
          onChange={(e) => setConsent(e.target.checked)} /> I authorize private storage and reuse of these declarations
          for funding screening/preparation. This does not authorize external sharing or an application.</label>
        <button type="submit" className="gx-btn sec" disabled={busy || !consent} data-testid="funding-save">
          Save and prepare supported packets</button>
      </form>
      <h5>Source-reviewed programs and discovery directories</h5>
      {view.opportunities.map((o) => <details key={o.id} data-testid={`funding-match-${o.id}`}>
        <summary>{o.name} — {o.match_status}</summary><p>{o.kind}; source checked {o.checked_at}: {o.source_status}.
          Current availability: {o.current_status}.</p>
        <a href={o.source} target="_blank" rel="noreferrer">Official provider/source</a>
        <ul>{o.requirements.map((r) => <li key={r}>{r}</li>)}</ul>
        <p>Application information: {o.application_requirements.join("; ")}</p>
        <p>Missing screening declarations: {o.missing.join(", ") || "None recorded; provider review still required"}</p>
        <p>Deadline: {o.deadline_rule}. {o.reasons.join(" ")}</p></details>)}
      <h5>Saved internal preparation packets</h5>
      {view.applications.map((a) => <details key={a.id} data-testid="funding-packet">
        <summary>{a.opportunity_id} revision {a.revision} — {a.approval_status}</summary>
        <p>{a.submission_status}. Integrity {a.integrity_verified ? "verified" : "FAILED"}.</p>
        <p><code>{a.content_hash}</code></p><pre>{JSON.stringify(a.packet, null, 2)}</pre>
        <a href={`${import.meta.env.BASE_URL}api${root}/applications/${a.id}/download`}>Download private preparation JSON</a>
        <label className="gx-check"><input type="checkbox" checked={!!reviewed[a.id]}
          onChange={(e) => setReviewed({ ...reviewed, [a.id]: e.target.checked })} />
          I reviewed this exact revision and approve internal preparation only.</label>
        <button className="gx-btn sec" type="button" disabled={busy || !reviewed[a.id] || !a.integrity_verified || a.approval_status !== "NEEDS_REVIEW"}
          data-testid="funding-approve" onClick={() => void update(`/applications/${a.id}/approve`, "POST", {
            revision: a.revision, content_hash: a.content_hash, confirmed: true })}>Approve this exact packet</button>
        <label>Customer-tracked deadline <input type="date" value={a.deadline || ""}
          onChange={(e) => setView({ ...view, applications: view.applications.map((p) => p.id === a.id ? { ...p, deadline: e.target.value || null } : p) })} /></label>
        <label>Customer-reported outcome (not verified)<select className="bo-in" value={a.reported_outcome}
          onChange={(e) => setView({ ...view, applications: view.applications.map((p) => p.id === a.id ? { ...p, reported_outcome: e.target.value } : p) })}>
          {["NOT_SUBMITTED", "USER_REPORTED_SUBMITTED", "USER_REPORTED_DECLINED", "USER_REPORTED_AWARDED", "WITHDRAWN"].map((v) => <option key={v}>{v}</option>)}</select></label>
        <button type="button" className="gx-btn sec" disabled={busy} onClick={() => void update(`/applications/${a.id}/tracking`, "PATCH",
          { deadline: a.deadline, reported_outcome: a.reported_outcome })}>Save tracking only</button>
      </details>)}
      <h5>Compare customer-supplied loan scenarios</h5>
      <form onSubmit={(e) => { e.preventDefault(); setBusy(true); setError("");
        call<Record<string, unknown>>(root + "/affordability", "POST", quote)
          .then((v) => setComparison((old) => [{ input: quote, result: v }, ...old].slice(0, 3)))
          .catch((e: Error) => setError(e.message)).finally(() => setBusy(false)); }}>
        {([["principal_cents", "Principal (cents)"], ["annual_rate_bps", "Annual nominal rate (basis points; 100 = 1%)"],
          ["months", "Term (months)"], ["upfront_fee_cents", "Upfront fee (cents)"]] as const).map(([k, text]) =>
          <label key={k}>{text}<input className="bo-in" type="number" min={k === "months" || k === "principal_cents" ? 1 : 0}
            required value={quote[k]} onChange={(e) => setQuote({ ...quote, [k]: Number(e.target.value) })} /></label>)}
        <button className="gx-btn sec" disabled={busy || !view.version} type="submit">Calculate and save scenario</button>
      </form>
      {comparison.map((v, i) => <details key={i}><summary>Loan scenario {comparison.length - i} — not a lender offer</summary><pre>{JSON.stringify(v, null, 2)}</pre></details>)}
    </>}
    {error && <p role="alert" className="gx-warn">{error}</p>}
  </section>;
}
