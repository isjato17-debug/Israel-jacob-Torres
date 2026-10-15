import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "./journey-api";
import { CATEGORIES, createApplication, updateApplication } from "./partner-api";
import type { PartnerApplication, PartnerCatalog, PartnerCategory, PartnerInput } from "./partner-api";
import type { PDict } from "./partner-i18n";

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const TEXT_KEYS = ["professional_credentials", "license_information", "api_capabilities", "partnership_interests", "pricing_information"] as const;
const FALLBACK_CODES = "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split(" ");

interface Props {
  t: PDict; catalog: PartnerCatalog | null; base: PartnerApplication | null; latest: PartnerApplication | null;
  onSaved: (a: PartnerApplication) => void; onClose: () => void; onDenied: () => void; onRefresh: () => Promise<boolean>;
}

export default function PartnerForm({ t, catalog, base, latest, onSaved, onClose, onDenied, onRefresh }: Props) {
  const d = base?.details;
  const [f, setF] = useState({
    business_name: d?.business_name ?? "", contact_name: d?.contact_name ?? "", contact_email: d?.contact_email ?? "",
    category: (d?.category ?? "") as PartnerCategory | "", services: d?.services ?? "",
    professional_credentials: d?.professional_credentials ?? "", license_information: d?.license_information ?? "",
    api_capabilities: d?.api_capabilities ?? "", partnership_interests: d?.partnership_interests ?? "", pricing_information: d?.pricing_information ?? "",
  });
  const [coverage, setCoverage] = useState<string[]>(d?.coverage ?? []);
  const [consent, setConsent] = useState(false);
  const [ack, setAck] = useState(false);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [serverErr, setServerErr] = useState("");
  const [stale, setStale] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [accepted, setAccepted] = useState(base);
  const [acceptRefresh, setAcceptRefresh] = useState(false);
  const alive = useRef(true);
  const head = useRef<HTMLHeadingElement>(null);
  const den = useRef(onDenied); den.current = onDenied;
  useEffect(() => { alive.current = true; head.current?.focus(); return () => { alive.current = false; }; }, []);

  useEffect(() => {
    if (acceptRefresh && latest) {
      setAccepted(latest); setAcceptRefresh(false); setStale(false); setAck(false); setServerErr("");
    }
  }, [acceptRefresh, latest]);
  const target = accepted;
  const noninitial = !!target && target.status !== "APPLICATION";
  const codes = catalog?.jurisdictions.length ? catalog.jurisdictions.map((j) => ({ code: j.code, name: j.name })) : FALLBACK_CODES.map((c) => ({ code: c, name: c }));
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  const validate = () => {
    const e: Record<string, string> = {};
    const n = (v: string, lo: number, hi: number) => v.trim().length >= lo && v.trim().length <= hi;
    if (!n(f.business_name, 2, 160)) e.business_name = t.vName;
    if (!n(f.contact_name, 2, 160)) e.contact_name = t.vName;
    if (!EMAIL.test(f.contact_email.trim()) || f.contact_email.trim().length > 254) e.contact_email = t.vEmail;
    if (!f.category) e.category = t.vCat;
    if (!n(f.services, 5, 2000)) e.services = t.vServices;
    if (coverage.length < 1) e.coverage = t.vCoverage;
    for (const k of TEXT_KEYS) if (f[k].trim().length > 2000) e[k] = t.vMax;
    if (!consent) e.consent = t.needConsent;
    if (noninitial && !ack) e.ack = t.needAck;
    setErrs(e);
    const first = Object.keys(e)[0];
    if (first) document.getElementById(`pf-${first}`)?.focus();
    return !first;
  };

  const submit = async (ev: FormEvent) => {
    ev.preventDefault();
    if (busy || stale || !validate()) return;
    const input: PartnerInput = {
      business_name: f.business_name.trim(), contact_name: f.contact_name.trim(), contact_email: f.contact_email.trim(),
      category: f.category as PartnerCategory, services: f.services.trim(), coverage,
      professional_credentials: f.professional_credentials.trim(), license_information: f.license_information.trim(),
      api_capabilities: f.api_capabilities.trim(), partnership_interests: f.partnership_interests.trim(),
      pricing_information: f.pricing_information.trim(), consent: true,
    };
    setBusy(true); setServerErr(""); setDone(false);
    try {
      const saved = target ? await updateApplication(target, input) : await createApplication(input);
      if (!alive.current) return;
      setAccepted(saved); setDone(true); setConsent(false); setAck(false); onSaved(saved);
    } catch (x) {
      if (!alive.current) return;
      if (x instanceof ApiError && (x.status === 401 || x.status === 403)) { den.current(); return; }
      if (x instanceof ApiError && x.status === 409) { setStale(true); setServerErr(t.conflict); }
      else setServerErr(`${t.saveErr} ${x instanceof Error ? x.message : ""}`);
    } finally { if (alive.current) setBusy(false); }
  };
  const refresh = async () => {
    setBusy(true);
    const ok = await onRefresh();
    if (!alive.current) return;
    setBusy(false);
    if (ok) { setAcceptRefresh(true); } else setServerErr(t.refreshFail);
  };

  const fe = (k: string) => errs[k] ? <p className="gx-err" id={`pf-${k}-err`} role="alert">{errs[k]}</p> : null;
  const ia = (k: string) => ({ id: `pf-${k}`, "aria-invalid": !!errs[k], "aria-describedby": errs[k] ? `pf-${k}-err` : undefined });
  const txt = (k: typeof TEXT_KEYS[number]) => (
    <div key={k}><label className="gx-field" htmlFor={`pf-${k}`}>{t[k]} ({t.optional})</label>
      <textarea {...ia(k)} lang="en" rows={3} value={f[k]} onChange={set(k)} data-testid={`partner-${k}`} />{fe(k)}</div>
  );

  return (
    <form className="gx-card" onSubmit={submit} noValidate aria-labelledby="pf-h" data-testid="partner-form">
      <h2 id="pf-h" ref={head} tabIndex={-1}>{target ? `${t.edit}: ${target.details.business_name}` : t.newApp}</h2>
      <p className="gx-help">{t.limits}</p>
      {noninitial && <div className="gx-warn" role="note"><p style={{ margin: 0 }}>{t.editWarn}</p>
        <label className="gx-check"><input id="pf-ack" type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} data-testid="partner-ack" /><span>{t.editAck}</span></label>{fe("ack")}</div>}
      <label className="gx-field" htmlFor="pf-business_name">{t.business_name}</label>
      <input {...ia("business_name")} type="text" maxLength={160} autoComplete="organization" value={f.business_name} onChange={set("business_name")} data-testid="partner-business-name" />{fe("business_name")}
      <label className="gx-field" htmlFor="pf-contact_name">{t.contact_name}</label>
      <input {...ia("contact_name")} type="text" maxLength={160} autoComplete="name" value={f.contact_name} onChange={set("contact_name")} data-testid="partner-contact-name" />{fe("contact_name")}
      <label className="gx-field" htmlFor="pf-contact_email">{t.contact_email}</label>
      <input {...ia("contact_email")} type="email" maxLength={254} autoComplete="email" value={f.contact_email} onChange={set("contact_email")} data-testid="partner-contact-email" />{fe("contact_email")}
      <label className="gx-field" htmlFor="pf-category">{t.category}</label>
      <select {...ia("category")} value={f.category} onChange={set("category")} data-testid="partner-category">
        <option value="">-</option>{CATEGORIES.map((c) => <option key={c} value={c}>{t.cat[c]}</option>)}
      </select>{fe("category")}
      <label className="gx-field" htmlFor="pf-services">{t.services}</label>
      <textarea {...ia("services")} lang="en" rows={4} value={f.services} onChange={set("services")} data-testid="partner-services" />{fe("services")}
      <fieldset style={{ border: "2px dashed var(--line)", borderRadius: 8, marginTop: 14 }} aria-describedby={errs.coverage ? "pf-coverage-err" : undefined}>
        <legend>{t.coverage}</legend>
        <div className="gx-row">
          <button type="button" className="gx-btn sec" onClick={() => setCoverage(codes.map((c) => c.code))}>{t.selectAll}</button>
          <button type="button" className="gx-btn sec" onClick={() => setCoverage([])}>{t.clearAll}</button>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 14px" }}>
          {codes.map((c) => (
            <label key={c.code} className="gx-check" style={{ minWidth: 70 }}>
              <input type="checkbox" id={c.code === codes[0].code ? "pf-coverage" : undefined} checked={coverage.includes(c.code)} title={c.name}
                onChange={(e) => setCoverage((cur) => e.target.checked ? [...cur, c.code] : cur.filter((x) => x !== c.code))} /><span>{c.code}</span>
            </label>
          ))}
        </div>
      </fieldset>{fe("coverage")}
      {TEXT_KEYS.map(txt)}
      <label className="gx-check"><input id="pf-consent" type="checkbox" checked={consent} onChange={(e) => { setConsent(e.target.checked); setErrs((x) => ({ ...x, consent: "" })); }} data-testid="partner-consent" /><span>{t.consent}</span></label>
      {fe("consent")}
      {serverErr && <div role="alert" data-testid="partner-error"><p className="gx-err">{serverErr}</p>
        {stale && <div className="gx-row"><button type="button" className="gx-btn sec" disabled={busy} onClick={() => void refresh()} data-testid="partner-refresh">{t.refresh}</button></div>}</div>}
      {done && <p className="gx-ok" role="status" data-testid="partner-saved">{t.saved}</p>}
      <div className="gx-row">
        <button type="submit" className="gx-btn" disabled={busy || stale} data-testid="partner-submit">{busy ? t.saving : target ? t.saveChanges : t.submit}</button>
        <button type="button" className="gx-btn sec" disabled={busy} onClick={onClose}>{t.cancel}</button>
      </div>
    </form>
  );
}
