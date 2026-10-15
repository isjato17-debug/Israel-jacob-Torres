import { call } from "./journey-api";

export interface OwnerAccess {
  owner_access: boolean;
  account_id: string;
  configuration_required: boolean;
  publishing_enabled: false;
  spending_enabled: false;
}
export type CampaignStatus = "DRAFT" | "IN_REVIEW" | "APPROVED" | "PAUSED" | "ARCHIVED";
export type ReviewAction = "request_review" | "approve" | "pause" | "archive" | "reopen";
export interface CampaignInput {
  title: string;
  objective: string;
  audience: string;
  channel: "website" | "email" | "social" | "referral";
  content: string;
  planned_budget_cents: number;
}
export interface Campaign extends CampaignInput {
  id: string; currency: "USD"; status: CampaignStatus; version: number;
  approved_at: string | null; created_at: string; updated_at: string;
  publishing_enabled: false; spending_authorized: false; verified_performance: null;
}
export interface CampaignList {
  campaigns: Campaign[];
  overview: { campaign_count: number; planned_budget_cents: number; currency: "USD"; verified_performance: null };
  capabilities: { planning: true; internal_review: true; ai_generation: false; publishing: false; spending: false; connected_analytics: false };
  notice: string;
}
export const getOwnerAccess = () => call<OwnerAccess>("/v2/operator/access");
export const fetchCampaigns = () => call<CampaignList>("/v2/operator/campaigns");
export const createCampaign = (input: CampaignInput) => call<Campaign>("/v2/operator/campaigns", "POST", input);
export const updateCampaign = (campaign: Campaign, input: CampaignInput) =>
  call<Campaign>(`/v2/operator/campaigns/${campaign.id}`, "PUT", { ...input, expected_version: campaign.version });
export const reviewCampaign = (campaign: Campaign, action: ReviewAction, confirm = false) =>
  call<Campaign>(`/v2/operator/campaigns/${campaign.id}/review`, "POST", {
    action, confirm, expected_version: campaign.version,
  });
