export const MAX_CENTS = 100_000_000;

export function parseDollars(raw: string): { cents: number } | { error: "req" | "bad" | "max" } {
  const s = raw.trim();
  if (!s) return { error: "req" };
  if (!/^\d+(\.\d{1,2})?$/.test(s)) return { error: "bad" };
  const [whole, frac = ""] = s.split(".");
  const w = whole.replace(/^0+(?=\d)/, "");
  if (w.length > 9) return { error: "max" };
  const cents = Number(w) * 100 + Number(frac.padEnd(2, "0"));
  if (cents > MAX_CENTS) return { error: "max" };
  return { cents };
}

export function centsToInput(cents: number): string {
  const c = Math.max(0, Math.trunc(cents));
  return `${Math.floor(c / 100)}.${String(c % 100).padStart(2, "0")}`;
}

export function formatUsd(cents: number, lang: string): string {
  return new Intl.NumberFormat(lang === "es" ? "es-US" : "en-US", { style: "currency", currency: "USD" }).format(cents / 100);
}
