import type { Intake, Plan, Stage } from "./api";

export interface Account {
  id: string; tenant_id: string; email: string; role: string;
}
export type Question = "state" | "entity_type" | "ownership_type" | "goal";
export type Language = "en" | "es";
export type DetailMode = "simple" | "details";
export interface Journey {
  id: string;
  business_id: string;
  stage: Stage;
  answers: Partial<Omit<Intake, "stage">>;
  language: Language;
  detail_mode: DetailMode;
  version: number;
  next_question: Question | null;
  answered_count: number;
  question_count: number;
  status: "IN_PROGRESS" | "PREPARED";
  plan: (Omit<Plan, "steps"> & { steps: (Plan["steps"][number] & { workflow_status: "NOT_STARTED" })[] }) | null;
  data_classification: "USER_PROVIDED_NOT_VERIFIED";
  consent_at: string;
  updated_at: string;
  cost: { amount_cents: null; status: "NOT_QUOTED"; charges_authorized: false };
  notice: string;
}
export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
const base = import.meta.env.BASE_URL.replace(/\/$/, "");

async function call<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const csrf = document.cookie.split("; ").find((part) => part.startsWith("genesis_csrf="));
  const token = csrf ? decodeURIComponent(csrf.slice("genesis_csrf=".length)) : "";
  const response = await fetch(`${base}/api${path}`, {
    method, credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(method !== "GET" && token ? { "X-CSRF-Token": token } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  let data;
  try { data = await response.json(); }
  catch { throw new ApiError("The service returned an invalid response. Please retry.", response.status); }
  if (!response.ok) {
    const detail = data?.detail;
    throw new ApiError(
      typeof detail === "string" ? detail :
        Array.isArray(detail) ? detail.map((item: { msg?: string }) => item.msg).join("; ") :
          "The request could not be completed.",
      response.status,
    );
  }
  return data as T;
}
export async function getSession(): Promise<Account | null> {
  try { return await call<Account>("/me"); }
  catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}
export async function signIn(mode: "login" | "register", email: string, password: string, tenantName?: string) {
  const data = await call<{ user: Account }>(`/auth/${mode}`, "POST", {
    email, password, ...(mode === "register" ? { tenant_name: tenantName || "My Business" } : {}),
  });
  return data.user;
}
export const signOut = () => call<{ ok: boolean }>("/auth/logout", "POST");
export const fetchJourneys = () => call<{ journeys: Journey[]; workflow_states: string[] }>("/v2/journeys");
export const startJourney = (stage: Stage, language: Language, detail_mode: DetailMode) =>
  call<Journey>("/v2/journeys", "POST", { stage, language, detail_mode, consent: true });
export const saveAnswer = (journey: Journey, field: Question, value: string) =>
  call<Journey>(`/v2/journeys/${journey.id}/answer`, "PATCH", {
    field, value, expected_version: journey.version,
  });
export const savePreferences = (journey: Journey, language: Language, detail_mode: DetailMode) =>
  call<Journey>(`/v2/journeys/${journey.id}/preferences`, "PATCH", {
    language, detail_mode, expected_version: journey.version,
  });
