import { call } from "./journey-api";
export interface BusinessAction {
  key: string; id: string; version: number; title: string; subsystem: string; status: string;
  dependencies: string[]; blocked_by: string[]; requirements: Record<string, unknown>;
  deadline: string | null; attempts: number; completed_at: string | null;
  evidence: { type: string; summary: string; provenance: string }[];
}
export interface TestSignature {
  id: string; document_id: string; document_hash: string; artifact_hash: string;
  typed_name: string; created_at: string; revoked: boolean; integrity_verified: boolean;
}
export interface Submission {
  id: string; signature_id: string; status: string; outcome: string; package_hash: string;
  result: Record<string, unknown>; simulation: true;
}
export interface RegulatoryChange {
  id: string; version: number; title: string; source_url: string; content_hash: string;
  checked_at: string; change_type: string; legal_status: string; effective_date: string | null;
  review_status: string; previous_revision_id: string | null; facts: Record<string, unknown>;
}
export interface OrchestratorView {
  initialized: boolean; scope: string; actions: BusinessAction[]; next_actions: string[];
  strategy: { selected: string; recommended: string; reason: string; classification: string;
    comparisons: { key: string; name: string; funding_gap_cents: number; advantages: string[];
      disadvantages: string[]; assumptions: string[]; risks: string[] }[];
    evidence_gaps: string[]; mitigation: string[] };
  signing: { disclosure: string; disclosure_version: string; passkeys: string; method: string };
  signatures: TestSignature[]; submissions: Submission[]; changes: RegulatoryChange[];
  registry: { key: string; title: string; category: string; status: string; source_url: string | null; [key: string]: unknown }[];
  government_workflows: { key: string; title: string; method: string; fee: string; source_url: string; status: string; prerequisites: string[] }[];
  collection?: { status: string; added: number; errors: string[] };
}
const root = (id: string) => `/v2/projects/${id}/orchestrator`;
export const loadOrchestrator = (id: string) => call<OrchestratorView>(root(id));
export const startOrchestrator = (id: string) => call<OrchestratorView>(`${root(id)}/start`, "POST", {});
export const acceptStrategy = (id: string, version: number) => call<OrchestratorView>(`${root(id)}/strategy`, "POST", { expected_version: version, confirmed: true });
export const testSign = (id: string, data: { expected_version: number; document_id: string; content_hash: string; typed_name: string; password: string; request_key: string; disclosure_version: string; reviewed: true; consent: true }) =>
  call<OrchestratorView>(`${root(id)}/sign`, "POST", data);
export const withdrawTestSignature = (id: string, sig: string) => call<OrchestratorView>(`${root(id)}/signatures/${sig}/withdraw`, "POST", { confirmed: true });
export const signedDownloadUrl = (id: string, sig: string) => `${import.meta.env.BASE_URL}api${root(id)}/signatures/${sig}/download`;
export const authorizeTestSubmission = (id: string, version: number, sig: string, outcome: string, request: string) =>
  call<OrchestratorView>(`${root(id)}/submission/authorize`, "POST", { expected_version: version, signature_id: sig, outcome, request_key: request, confirmed: true });
export const dispatchTestSubmission = (id: string, version: number) => call<OrchestratorView>(`${root(id)}/submission/dispatch`, "POST", { expected_version: version });
export const verifyTestSubmission = (id: string, version: number) => call<OrchestratorView>(`${root(id)}/submission/verify`, "POST", { expected_version: version });
export const cancelBusinessAction = (id: string, key: string, version: number) => call<OrchestratorView>(`${root(id)}/actions/${encodeURIComponent(key)}/cancel`, "POST", { expected_version: version, confirmed: true });
export const collectRegulatorySources = (id: string) => call<OrchestratorView>(`${root(id)}/regulatory/collect`, "POST", {});
export const reviewRegulatoryChange = (id: string, change: string, version: number, decision: string) =>
  call<OrchestratorView>(`${root(id)}/regulatory/${change}/review`, "POST", { expected_version: version, decision, confirmed: true });
