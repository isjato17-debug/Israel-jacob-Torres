import { call } from "./journey-api";
import type { DetailMode, Journey, Language } from "./journey-api";

export interface Recommendation {
  mode: "SIMULATION"; summary: string; next_question: string;
  roadmap: { title: string; explanation: string }[];
  assumptions: string[]; professional_review: string[]; source_ids: string[];
  classification: "SIMULATED_NOT_AI_GENERATED";
}
export interface Consultation {
  id: string; version: number; journey_version: number; language: Language; detail_mode: DetailMode;
  mode: "SIMULATION"; turns: { question: string; answer: Recommendation }[];
  context_stale: boolean; cost: { actual_cents: 0; live_authorized: false };
  consent_at: string; updated_at: string;
}
export interface ConsultationResource {
  id: string; title: string; url: string; kind: "OFFICIAL_RESOURCE"; verification: "REFERENCE_ONLY_NOT_STATUS_VERIFICATION";
}
export interface ConsultationState {
  consultation: Consultation | null;
  privacy: { status: "NOT_WITHDRAWN" | "REVOKED" | "DELETED" | "GRANTED"; version: number; updated_at: string | null };
  availability: { mode: "SIMULATION_ONLY"; live_enabled: false; max_turns: 8; external_actions_enabled: false };
  resources: ConsultationResource[];
}
export const fetchConsultation = (journeyId: string) =>
  call<ConsultationState>(`/v2/journeys/${journeyId}/consultation`);
export const sendConsultation = (journey: Journey, expectedVersion: number, message: string, privacyVersion = 0) =>
  call<Consultation>(`/v2/journeys/${journey.id}/consultation`, "POST", {
    consent: true, expected_version: expectedVersion, journey_version: journey.version, message, privacy_version: privacyVersion,
  });
export const decideConsultationPrivacy = (journeyId: string, state: ConsultationState, action: "revoke" | "delete" | "grant") =>
  call<{ privacy: ConsultationState["privacy"]; notice: string }>(`/v2/journeys/${journeyId}/consultation/privacy`, "POST", {
    action, expected_version: state.privacy.version, consultation_version: state.consultation?.version ?? 0, confirmed: true,
  });
