import { useEffect, useState } from "react";
import { call } from "./journey-api";
type Limits = { request: number; task: number; customer: number; daily: number; monthly: number };
interface Policy { version: number; shutdown: boolean; simulation_enabled: boolean; limits: Limits;
  allowed_models: string[]; concurrency_limit: number; retry_ceiling: number; mode: string;
  buckets: { scope: string; reserved_microusd: number; spent_microusd: number }[]; residual_exposure: string; }
const root = "/v2/operator/ai-finance";
export default function AIFinancePanel() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  useEffect(() => { let live = true; call<Policy>(root).then((p) => { if (live) setPolicy(p); })
    .catch((e: Error) => { if (live) setError(e.message); }); return () => { live = false; }; }, []);
  const save = async (shutdown: boolean) => {
    if (!policy) return;
    setBusy(true); setError("");
    try { setPolicy(await call<Policy>(root, "PUT", { expected_version: policy.version, shutdown,
      simulation_enabled: policy.simulation_enabled, paid_provider_enabled: false, limits: policy.limits,
      allowed_models: ["mock-budget-v1"], concurrency_limit: policy.concurrency_limit, retry_ceiling: policy.retry_ceiling })); }
    catch (e) { setError(e instanceof Error ? e.message : "Policy update failed safely"); }
    finally { setBusy(false); }
  };
  return <section className="ow-card" data-testid="ai-finance-panel">
    <h2>AI financial protection — offline tests only</h2>
    <p>Paid AI OFF. External spending authorization $0. These limits authorize virtual test accounting only,
      not provider activation, customer billing or real payments.</p>
    {error && <p role="alert" className="ow-err">{error}</p>}
    {policy && <form onSubmit={(e) => { e.preventDefault(); void save(policy.shutdown); }}>
      <p>Emergency shutdown: <b>{policy.shutdown ? "ON" : "OFF (virtual tests only)"}</b></p>
      <label><input type="checkbox" checked={policy.simulation_enabled} disabled={busy}
        onChange={(e) => setPolicy({ ...policy, simulation_enabled: e.target.checked })} /> Enable simulated accounting</label>
      <div className="ow-grid two">{(Object.keys(policy.limits) as (keyof Limits)[]).map((key) =>
        <label key={key}>{key} limit (micro-USD; 1,000,000 = $1 virtual)
          <input type="number" min="0" max="1000000000000" step="1" required value={policy.limits[key]}
            onChange={(e) => setPolicy({ ...policy, limits: { ...policy.limits, [key]: Number(e.target.value) } })} /></label>)}</div>
      <label>Concurrent reservations <input type="number" min="1" max="20" required value={policy.concurrency_limit}
        onChange={(e) => setPolicy({ ...policy, concurrency_limit: Number(e.target.value) })} /></label>
      <label>Retry ceiling <input type="number" min="1" max="3" required value={policy.retry_ceiling}
        onChange={(e) => setPolicy({ ...policy, retry_ceiling: Number(e.target.value) })} /></label>
      <div className="ow-row"><button className="ow-btn sec" type="submit" disabled={busy}>Save virtual limits</button>
        <button className="ow-btn" type="button" disabled={busy} onClick={() => void save(true)}>Emergency stop</button>
        <button className="ow-btn sec" type="button" disabled={busy || !policy.simulation_enabled}
          onClick={() => void save(false)}>Allow virtual tests</button></div>
      <p className="ow-help">{policy.residual_exposure}</p>
      <details><summary>Virtual ledger</summary><pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
        {JSON.stringify(policy.buckets, null, 2)}</pre></details>
    </form>}
  </section>;
}
