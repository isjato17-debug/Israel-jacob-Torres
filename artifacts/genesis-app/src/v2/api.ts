export type Stage = "start" | "run" | "grow";
export interface Service {
  id: string;
  stage: Stage;
  title: string;
  description: string;
  availability: "GUIDED_ONLY" | "NEEDS_CONNECTION" | "NEEDS_PROFESSIONAL";
  professional_review: boolean;
  official_url: string | null;
  price_cents: number | null;
  submission_available: boolean;
}
export interface Catalog {
  version: string;
  states: { code: string; name: string }[];
  entity_types: string[];
  ownership_types: string[];
  services: Service[];
  ai: { status: string; mode: string; notice: string };
  billing: { status: string; checkout_enabled: boolean };
  providers: { name: string; status: string }[];
  notice: string;
}
export interface Intake {
  stage: Stage;
  state: string;
  entity_type: string;
  ownership_type: string;
  goal: string;
}
export interface Plan {
  mode: string;
  persisted: boolean;
  intake: Intake;
  state_name: string;
  steps: {
    order: number; service_id: string; title: string; next_action: string;
    status: string; professional_review: boolean; official_url: string | null;
    price_cents: number | null; completed: boolean;
  }[];
  approvals: string[];
  notice: string;
}
const base = `${import.meta.env.BASE_URL.replace(/\/$/, "")}/api/v2`;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The planning service returned an invalid response. Please try again.");
  }
  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail :
      Array.isArray(detail) ? detail.map((item: { msg?: string }) => item.msg).join("; ") :
      "The planning service is unavailable. Please try again.");
  }
  return data as T;
}
export const fetchCatalog = () => request<Catalog>("/catalog");
export const createPlan = (intake: Intake) => request<Plan>("/plan", {
  method: "POST", body: JSON.stringify(intake),
});
