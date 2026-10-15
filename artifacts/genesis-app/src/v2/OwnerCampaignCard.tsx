import { useState } from "react";
import type { Campaign, ReviewAction } from "./owner-api";
import type { Dict, Lang } from "./owner-i18n";
import { formatUsd } from "./owner-money";

interface Props {
  t: Dict; lang: Lang; c: Campaign; busy: boolean; error: string;
  onEdit: (c: Campaign) => void;
  onAction: (c: Campaign, a: ReviewAction, confirm?: boolean) => Promise<void>;
}

export default function OwnerCampaignCard({ t, lang, c, busy, error, onEdit, onAction }: Props) {
  const [confirming, setConfirming] = useState(false);
  const [ack, setAck] = useState(false);
  const s = c.status;
  const canReview = s === "DRAFT" || s === "PAUSED";
  const contentOk = c.content.trim().length >= 10;
  const btn = (a: ReviewAction, testid: string, onClick: () => void, disabled = false) => (
    <button type="button" className="ow-btn sec" disabled={busy || disabled} onClick={onClick} data-testid={testid}>{t[a]}</button>
  );
  return (
    <article className="ow-card" data-testid={`campaign-${c.id}`} aria-labelledby={`h-${c.id}`}>
      <div className="ow-row" style={{ justifyContent: "space-between", marginTop: 0 }}>
        <h3 id={`h-${c.id}`}>{c.title}</h3>
        <span className={`ow-badge ${s}`} data-testid={`campaign-status-${c.id}`}>{t[s]}</span>
      </div>
      <dl style={{ margin: "10px 0 0" }}>
        <dt>{t.fObjective}</dt><dd>{c.objective}</dd>
        <dt>{t.fAudience}</dt><dd>{c.audience}</dd>
        <dt>{t.fChannel}</dt><dd>{t[c.channel]}</dd>
        <dt>{t.fBudget}</dt><dd>{formatUsd(c.planned_budget_cents, lang)}</dd>
        <dt>{t.fContent}</dt><dd>{c.content.trim() ? <pre>{c.content}</pre> : <span className="ow-help">{t.noContent}</span>}</dd>
      </dl>
      <p className="ow-help">{t.version} {c.version} - {t.updated} {new Date(c.updated_at).toLocaleString(lang)}</p>
      {s === "APPROVED" && <p className="ow-note">{t.reviewNote}</p>}
      {canReview && !contentOk && <p className="ow-help">{t.contentShort}</p>}
      {confirming && (
        <div className="ow-warn" role="group" aria-label={t.approveTitle}>
          <b>{t.approveTitle}</b>
          <label className="ow-check"><input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} data-testid={`campaign-confirm-${c.id}`} /><span>{t.approveBody}</span></label>
          <div className="ow-row">
            <button type="button" className="ow-btn" disabled={!ack || busy} data-testid={`campaign-approve-confirm-${c.id}`}
              onClick={async () => { await onAction(c, "approve", true); setConfirming(false); setAck(false); }}>{t.confirmApprove}</button>
            <button type="button" className="ow-btn sec" onClick={() => { setConfirming(false); setAck(false); }}>{t.cancelShort}</button>
          </div>
        </div>
      )}
      {error && <p className="ow-err" role="alert">{t.actionFail}{error}</p>}
      <div className="ow-row">
        {s !== "ARCHIVED" && <button type="button" className="ow-btn" onClick={() => onEdit(c)} disabled={busy} data-testid={`campaign-edit-${c.id}`}>{t.edit}</button>}
        {canReview && btn("request_review", `campaign-review-${c.id}`, () => onAction(c, "request_review"), !contentOk)}
        {s === "IN_REVIEW" && btn("approve", `campaign-approve-${c.id}`, () => setConfirming(true))}
        {(s === "IN_REVIEW" || s === "APPROVED") && btn("pause", `campaign-pause-${c.id}`, () => onAction(c, "pause"))}
        {s !== "ARCHIVED" && btn("archive", `campaign-archive-${c.id}`, () => onAction(c, "archive"))}
        {s === "ARCHIVED" && btn("reopen", `campaign-reopen-${c.id}`, () => onAction(c, "reopen"))}
      </div>
    </article>
  );
}
