import { call } from "./journey-api";

export const CATEGORIES = ["government_authorized", "formation", "registered_agent", "legal", "cpa", "tax", "insurance", "banking_lending", "payroll_accounting", "intellectual_property", "ai_technology", "marketing_growth"] as const;
export type PartnerCategory = typeof CATEGORIES[number];
export interface PartnerInput {
  business_name: string; contact_name: string; contact_email: string; category: PartnerCategory;
  services: string; coverage: string[]; professional_credentials: string; license_information: string;
  api_capabilities: string; partnership_interests: string; pricing_information: string; consent: true;
}
export interface PartnerApplication {
  id: string; applicant_id: string; details: PartnerInput; status: string; version: number; review_note: string;
  verification_status: "NOT_VERIFIED" | "MANUAL_REVIEW_RECORDED";
  agreement_status: "NOT_STARTED" | "PENDING" | "ACCEPTED";
  integration_status: "NOT_CONNECTED" | "TEST_EVIDENCE_RECORDED";
  created_at: string; updated_at: string; external_actions_enabled: false; verified_performance: null;
}
export interface PartnerCatalog {
  categories: { id: string; title: string }[]; statuses: string[]; limits: Record<string, unknown>;
  capabilities: { external_actions: false; public_directory: false; live_integrations: false };
  official_resources: { id?: string; title: string; url: string }[];
  jurisdictions: { code: string; name: string; reference_url: string; connection_type: "OFFICIAL_PUBLIC_INFORMATION"; manual_verification_required: true; filing_enabled: false }[];
}
export interface PartnerHistory { action: string; actor_id: string; created_at: string; details: { status?: string; version?: number } }
export const fetchPartnerCatalog = () => call<PartnerCatalog>("/v2/partners/catalog");
export const fetchApplications = () => call<{ applications: PartnerApplication[] }>("/v2/partners/applications");
export const createApplication = (input: PartnerInput) => call<PartnerApplication>("/v2/partners/applications", "POST", input);
export const updateApplication = (a: PartnerApplication, input: PartnerInput) =>
  call<PartnerApplication>(`/v2/partners/applications/${a.id}`, "PATCH", { ...input, expected_version: a.version });
export const fetchApplicationHistory = (id: string) => call<{ events: PartnerHistory[] }>(`/v2/partners/applications/${id}/history`);

export const REVIEW_ACTIONS = ["begin_review", "request_information", "verify", "await_agreement", "record_agreement", "approve", "begin_integration", "record_integration", "activate", "suspend", "reject", "reopen"] as const;
export type PartnerReviewAction = typeof REVIEW_ACTIONS[number];
export interface ReviewMeta {
  evidence: { kind: string; reference: string; note: string; recorded_at: string; actor_id: string }[];
  agreement_reference: string; integration_reference: string; valid: boolean;
}
export type OperatorApplication = PartnerApplication & { review: ReviewMeta };
export interface Promotion {
  id: string; partner_id: string; title: string; content: string; partner_permission_reference: string;
  status: "DRAFT" | "APPROVED" | "ARCHIVED"; version: number; attribution_code: string; verified_performance: null; publishing_enabled: false;
}
export const fetchOperatorPartners = () => call<{ applications: OperatorApplication[]; capabilities: Record<string, unknown> }>("/v2/operator/partners");
export const reviewApplication = (a: PartnerApplication, action: PartnerReviewAction, reference: string, note: string) =>
  call<OperatorApplication>(`/v2/operator/partners/${a.id}/review`, "POST", { expected_version: a.version, action, confirm: true, reference, note });
export const fetchOperatorHistory = (id: string) => call<{ events: PartnerHistory[] }>(`/v2/operator/partners/${id}/history`);
export const fetchPromotions = () => call<{ promotions: Promotion[]; external_publishing_enabled: false }>("/v2/operator/partner-promotions");
export const createPromotion = (i: { partner_id: string; title: string; content: string; partner_permission_reference: string }) =>
  call<Promotion>("/v2/operator/partner-promotions", "POST", { ...i, consent: true });
export const reviewPromotion = (p: Promotion, action: "approve" | "archive") =>
  call<Promotion>(`/v2/operator/partner-promotions/${p.id}/review`, "POST", { expected_version: p.version, action, confirm: true });
