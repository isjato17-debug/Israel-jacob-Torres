import { call } from "./journey-api";

export interface IdeaInput {
  concept: string; industry: string; jurisdiction: string; budget_cents: number;
  goals: string; preferences: string; notes: string; assumptions: string;
}
export interface BudgetLine { label: string; amount_cents: number }
export interface BusinessPlan {
  key: "start_smart" | "build_strong" | "grow_big"; name: string; strategy: string;
  business_model: string; target_customers: string; market_assumptions: string[];
  startup_items: BudgetLine[]; monthly_items: BudgetLine[];
  startup_total_cents: number; monthly_fixed_cents: number; funding_required_cents: number;
  funding_gap_cents: number; available_budget_cents: number; reserve_cents: number;
  average_ticket_cents: number; monthly_units: number; gross_margin: number;
  monthly_revenue_cents: number; operating_profit_cents: number; break_even_revenue_cents: number;
  revenue_scenarios: { label: string; revenue_cents: number; operating_profit_cents: number }[];
  assumptions: string[]; risks: string[]; marketing: string; milestones: string[];
  requirements: { title: string; status: string; reason: string; official_url: string }[];
  service_needs: { category: string; reason: string }[];
  classification: string; recommended: boolean; recommendation_reason: string;
}
export interface Idea extends IdeaInput {
  id: string; version: number; status: "DRAFT" | "PLANNED" | "DEVELOPED" | "ARCHIVED";
  selected_plan: string | null; plans: BusinessPlan[]; created_at: string; updated_at: string;
  project_id: string | null; history: { version: number; action: string; created_at: string }[];
}
export interface Project {
  id: string; business_id: string; idea_id: string; name: string; stage: string;
  plan: BusinessPlan; budget_cents: number; created_at: string;
  checklist: { id: string; horizon: string; task: string; budget: number; status: string; kpi: string }[];
}
export const listIdeas = () => call<{ ideas: Idea[] }>("/v2/ideas");
export const createIdea = (input: IdeaInput) => call<Idea>("/v2/ideas", "POST", { ...input, consent: true });
export const getIdea = (id: string) => call<Idea>(`/v2/ideas/${id}`);
export const editIdea = (idea: Idea, input: IdeaInput) =>
  call<Idea>(`/v2/ideas/${idea.id}`, "PATCH", { ...input, expected_version: idea.version });
export const ideaAction = (idea: Idea, action: "archive" | "restore" | "generate") =>
  call<Idea>(`/v2/ideas/${idea.id}/${action}`, "POST", { expected_version: idea.version });
export const selectPlan = (idea: Idea, plan_key: string) =>
  call<Idea>(`/v2/ideas/${idea.id}/select`, "POST", { expected_version: idea.version, plan_key });
export const developIdea = (idea: Idea) =>
  call<Project>(`/v2/ideas/${idea.id}/develop`, "POST", { expected_version: idea.version });
export const listProjects = () => call<{ projects: Project[] }>("/v2/projects");
export const getProject = (id: string) => call<Project>(`/v2/projects/${id}`);
export const setProjectTask = (project: Project, taskId: string, status: "todo" | "done") =>
  call<{ ok: boolean }>(`/businesses/${project.business_id}/execution/${taskId}`, "PATCH", { status });
