import { useEffect, useRef, useState } from "react";
import type { ConsultationState } from "./consultation-api";
import type { Language } from "./journey-api";
import { privacyText } from "./privacy-i18n";

export type PrivacyAction = "revoke" | "delete" | "grant";
interface Props { lang: Language; data: ConsultationState; busy: boolean; message: string; error: string; onRun: (a: PrivacyAction) => Promise<boolean> }

export default function PrivacyControls({ lang, data, busy, message, error, onRun }: Props) {
  const p = privacyText[lang];
  const [pending, setPending] = useState<PrivacyAction | null>(null);
  const [sure, setSure] = useState(false);
  const boxRef = useRef<HTMLInputElement>(null);
  const st = data.privacy.status;
  const inactive = st === "REVOKED" || st === "DELETED";
  useEffect(() => { if (pending) boxRef.current?.focus(); }, [pending]);
  const open = (a: PrivacyAction) => { setPending(a); setSure(false); };
  const note = { revoke: p.revokeNote, delete: p.delNote, grant: p.grantNote };
  const conf = { revoke: p.confirmRevoke, delete: p.confirmDel, grant: p.confirmGrant };
  const run = async () => { if (!pending || !sure || busy) return; const ok = await onRun(pending); if (ok) { setPending(null); setSure(false); } };
  return (
    <section aria-labelledby="priv-h" data-testid="section-privacy" style={{ borderTop: "2px dashed var(--line)", marginTop: 18, paddingTop: 8 }}>
      <h3 id="priv-h">{p.h}</h3>
      <p><b>{p.status}:</b> <span className="gx-badge" data-testid="text-privacy-status">{p[`s_${st}` as "s_GRANTED"]}</span></p>
      {inactive && <p className="gx-warn" role="note" data-testid="text-privacy-blocked">{p.blocked}</p>}
      <div className="gx-row">
        {!inactive && <button type="button" className="gx-btn sec" disabled={busy} aria-expanded={pending === "revoke"} data-testid="privacy-revoke" onClick={() => open("revoke")}>{p.revoke}</button>}
        {st !== "DELETED" && data.consultation && <button type="button" className="gx-btn sec" disabled={busy} aria-expanded={pending === "delete"} data-testid="privacy-delete" onClick={() => open("delete")}>{p.del}</button>}
        {inactive && <button type="button" className="gx-btn" disabled={busy} aria-expanded={pending === "grant"} data-testid="privacy-grant" onClick={() => open("grant")}>{p.grant}</button>}
      </div>
      {pending && (
        <div role="group" aria-label={p[pending === "delete" ? "del" : pending]} className="gx-warn" data-testid="privacy-confirm">
          <p>{note[pending]}</p>
          <label className="gx-check"><input ref={boxRef} type="checkbox" checked={sure} disabled={busy} onChange={(e) => setSure(e.target.checked)} data-testid="privacy-confirm-box" /><span>{conf[pending]}</span></label>
          <div className="gx-row">
            <button type="button" className="gx-btn" disabled={busy || !sure} data-testid="privacy-confirm-run" onClick={() => void run()}>{busy ? p.working : p.run}</button>
            <button type="button" className="gx-btn sec" disabled={busy} onClick={() => setPending(null)}>{p.cancel}</button>
          </div>
        </div>
      )}
      <div aria-live="polite" role="status">{message && <p className="gx-ok" data-testid="text-privacy-done">{message}</p>}</div>
      {error && <p className="gx-err" role="alert" data-testid="text-privacy-error">{error}</p>}
    </section>
  );
}
