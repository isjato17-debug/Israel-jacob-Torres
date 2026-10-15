import { call } from "./journey-api";
export interface FormField { key: string; label: string; type: "text" | "textarea" | "date" | "money"; required: boolean; max_length?: number }
export interface DocumentRecord {
  id: string; revision: number; content_hash: string; filename: string; created_at: string;
  sections: { heading: string; body: string }[];
  approval: { approved_at: string; purpose: string } | null;
}
export interface DocumentWorkflow {
  id: string; version: number; status: "DRAFT" | "GENERATED" | "READY_FOR_SIGNATURE";
  fields: Record<string, string | number | null>; missing: string[];
  documents: DocumentRecord[]; latest_document: DocumentRecord | null;
}
export interface ExecutionContext {
  project_id: string; supported: boolean;
  passport: { version: number; fields: Record<string, string>; classification: string };
  template: { key: string; title: string; version: number; fields: FormField[]; notice: string };
  assistant: {
    classification: string; live_ai_connected: boolean; summary: string; next_action: string;
    reasons: string[]; financials: Record<string, number | null>;
    board: { agents: Record<string, { position: string; reason: string }> };
    founder_dna: { status: string; assessment: Record<string, string | number> | null };
  };
  workflow: DocumentWorkflow | null;
}
const root = (id: string) => `/v2/projects/${id}/execution`;
export const loadExecution = (id: string) => call<ExecutionContext>(root(id));
export const savePassport = (id: string, version: number, fields: Record<string, string>) =>
  call<ExecutionContext>(`${root(id)}/passport`, "PUT", { expected_version: version, fields, consent: true });
export const startDocument = (id: string) =>
  call<ExecutionContext>(`${root(id)}/documents`, "POST", { template_key: "cleaning_service_agreement" });
export const saveDocument = (id: string, version: number, fields: Record<string, string | number | null>) =>
  call<ExecutionContext>(`${root(id)}/document`, "PATCH", { expected_version: version, fields });
export const generateDocument = (id: string, version: number) =>
  call<ExecutionContext>(`${root(id)}/generate`, "POST", { expected_version: version });
export const approveDocument = (id: string, version: number, document: DocumentRecord) =>
  call<ExecutionContext>(`${root(id)}/approve`, "POST", { expected_version: version,
    document_id: document.id, content_hash: document.content_hash, confirmed: true });
export const documentDownloadUrl = (project: string, document: string) =>
  `${import.meta.env.BASE_URL}api${root(project)}/documents/${document}/download`;
export interface ConnectionReadiness { connections: { key: string; name: string; status: string; cost: string; next_dependency: string }[]; external_actions_authorized: false; notice: string }
export interface PublicNotices { status: string; checked_at: string; notice: string; notices: { title: string; url: string; publication_date: string; document_number: string }[] }
export const loadConnections = (id: string) => call<ConnectionReadiness>(`${root(id)}/connections`);
export const checkPublicNotices = (id: string) => call<PublicNotices>(`${root(id)}/connections/public-check`, "POST", {});
