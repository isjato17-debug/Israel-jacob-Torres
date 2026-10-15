import { useState } from "react";

export type Lang = "en" | "es";
const en = {
  title: "Infinite Growth planning console", private: "Private platform-owner area",
  lang: "Language", loading: "Loading your access...", retry: "Try again",
  signinTitle: "Sign in required", signinBody: "This console is private. Sign in with the existing guided sign-in, then return here.",
  signin: "Go to sign-in", workspace: "Open customer workspace",
  deniedTitle: "Access denied", deniedBody: "Your account is not authorized for this console. A workspace operator must explicitly authorize this account ID on the server. This page cannot grant access, and you should never enter secrets here.",
  yourId: "Your account ID", copy: "Copy ID", copied: "Copied", copyFail: "Copy failed. Select the ID and copy it manually.",
  configTitle: "Owner access is not configured", configBody: "The server has no owner allowlist configured. Ask the workspace operator to configure it.",
  errorTitle: "Something went wrong", logout: "Sign out", loggingOut: "Signing out...", logoutFail: "Sign out did not complete on the server. You are still signed in: ",
  signedOut: "You are signed out.", sessionEnded: "Your session ended. Sign in again.",
  overview: "Overview", count: "Campaigns", planned: "Planned budget (USD, a plan only)",
  noVerified: "No verified results. Nothing has been published, spent or measured, so no performance figures are shown.",
  caps: "Capabilities", available: "Available", unavailable: "Unavailable",
  cPlan: "Campaign planning", cReview: "Internal content review", cAi: "AI generation", cPub: "External publishing", cSpend: "Spending", cAnalytics: "Connected analytics",
  reviewNote: "Approval means internal content review only. It does not authorize spending, publishing or paid services.",
  newCampaign: "New campaign", campaigns: "Campaigns", refresh: "Refresh", refreshing: "Refreshing...", refreshFail: "Could not refresh the list. Showing the last loaded records: ",
  emptyTitle: "No campaigns yet", emptyBody: "Plan your first original campaign. Nothing is sent or published from here.",
  edit: "Edit", request_review: "Request review", approve: "Approve internally", pause: "Pause", archive: "Archive", reopen: "Reopen as draft",
  fTitle: "Title", fObjective: "Objective", fAudience: "Audience", fChannel: "Channel", fContent: "Campaign content", fBudget: "Planned budget in USD",
  hBudget: "Plan only, not money spent. Up to 2 decimals, max 1,000,000.", hContent: "May be blank in a draft. Review needs at least 10 characters.",
  website: "Website", email: "Email", social: "Social", referral: "Referral",
  save: "Save campaign", saving: "Saving...", cancel: "Close editor", saved: "Saved.",
  editing: "Editing campaign", creating: "New campaign",
  resetWarn: "Saving changes resets this campaign to DRAFT and clears any prior approval.", resetConfirm: "I understand this resets it to draft",
  needConfirm: "Confirm the reset to save.", reqTitle: "Title is required.", reqObjective: "Objective is required.", reqAudience: "Audience is required.", lenTitle: "Title must be 3 to 160 characters.", lenObjective: "Objective must be 5 to 1,200 characters.", lenAudience: "Audience must be 3 to 500 characters.", lenContent: "Content cannot exceed 6,000 characters.",
  budgetReq: "Enter a budget, for example 250 or 250.50.", budgetBad: "Use a non-negative amount with at most 2 decimals, no symbols.", budgetMax: "Budget cannot exceed 1,000,000.00 USD.",
  conflictTitle: "Someone changed this campaign before you saved.", conflictBody: "Your typed text is kept. Load the latest record, then review and save again.",
  rebase: "Load latest and keep my text", conflictGone: "The latest record could not be found.",
  contentShort: "Review needs at least 10 characters of content.",
  approveTitle: "Confirm internal approval", approveBody: "I confirm this is an internal content review only and does not authorize spending, publishing or paid services.",
  confirmApprove: "Confirm approval", cancelShort: "Cancel",
  status: "Status", DRAFT: "Draft", IN_REVIEW: "In review", APPROVED: "Approved (internal)", PAUSED: "Paused", ARCHIVED: "Archived",
  version: "Version", updated: "Updated", noContent: "No content yet.", actionFail: "Action failed: ",
  noAccountEnv: "Private data cleared.",
};
const es: typeof en = {
  title: "Consola de planificacion de Infinite Growth", private: "Area privada de propietarios de la plataforma",
  lang: "Idioma", loading: "Cargando su acceso...", retry: "Reintentar",
  signinTitle: "Se requiere iniciar sesion", signinBody: "Esta consola es privada. Inicie sesion con el acceso guiado existente y vuelva aqui.",
  signin: "Ir a iniciar sesion", workspace: "Abrir el espacio de clientes",
  deniedTitle: "Acceso denegado", deniedBody: "Su cuenta no esta autorizada para esta consola. Un operador del espacio de trabajo debe autorizar explicitamente este ID de cuenta en el servidor. Esta pagina no puede otorgar acceso y nunca debe ingresar secretos aqui.",
  yourId: "Su ID de cuenta", copy: "Copiar ID", copied: "Copiado", copyFail: "No se pudo copiar. Seleccione el ID y copielo manualmente.",
  configTitle: "El acceso de propietario no esta configurado", configBody: "El servidor no tiene lista de propietarios autorizados. Pida al operador que la configure.",
  errorTitle: "Algo salio mal", logout: "Cerrar sesion", loggingOut: "Cerrando sesion...", logoutFail: "El servidor no completo el cierre de sesion. Sigue con la sesion iniciada: ",
  signedOut: "Sesion cerrada.", sessionEnded: "Su sesion termino. Inicie sesion de nuevo.",
  overview: "Resumen", count: "Campanas", planned: "Presupuesto planificado (USD, solo un plan)",
  noVerified: "Sin resultados verificados. Nada se ha publicado, gastado ni medido, por lo que no se muestran cifras de rendimiento.",
  caps: "Capacidades", available: "Disponible", unavailable: "No disponible",
  cPlan: "Planificacion de campanas", cReview: "Revision interna de contenido", cAi: "Generacion con IA", cPub: "Publicacion externa", cSpend: "Gasto", cAnalytics: "Analitica conectada",
  reviewNote: "La aprobacion es solo una revision interna de contenido. No autoriza gasto, publicacion ni servicios de pago.",
  newCampaign: "Nueva campana", campaigns: "Campanas", refresh: "Actualizar", refreshing: "Actualizando...", refreshFail: "No se pudo actualizar la lista. Se muestran los ultimos registros cargados: ",
  emptyTitle: "Aun no hay campanas", emptyBody: "Planifique su primera campana original. Nada se envia ni se publica desde aqui.",
  edit: "Editar", request_review: "Solicitar revision", approve: "Aprobar internamente", pause: "Pausar", archive: "Archivar", reopen: "Reabrir como borrador",
  fTitle: "Titulo", fObjective: "Objetivo", fAudience: "Audiencia", fChannel: "Canal", fContent: "Contenido de la campana", fBudget: "Presupuesto planificado en USD",
  hBudget: "Solo un plan, no dinero gastado. Hasta 2 decimales, maximo 1,000,000.", hContent: "Puede quedar en blanco en un borrador. La revision requiere al menos 10 caracteres.",
  website: "Sitio web", email: "Correo", social: "Redes sociales", referral: "Referidos",
  save: "Guardar campana", saving: "Guardando...", cancel: "Cerrar editor", saved: "Guardado.",
  editing: "Editando campana", creating: "Nueva campana",
  resetWarn: "Guardar cambios devuelve esta campana a BORRADOR y borra cualquier aprobacion previa.", resetConfirm: "Entiendo que vuelve a borrador",
  needConfirm: "Confirme el reinicio para guardar.", reqTitle: "El titulo es obligatorio.", reqObjective: "El objetivo es obligatorio.", reqAudience: "La audiencia es obligatoria.", lenTitle: "El titulo debe tener de 3 a 160 caracteres.", lenObjective: "El objetivo debe tener de 5 a 1,200 caracteres.", lenAudience: "La audiencia debe tener de 3 a 500 caracteres.", lenContent: "El contenido no puede superar 6,000 caracteres.",
  budgetReq: "Ingrese un presupuesto, por ejemplo 250 o 250.50.", budgetBad: "Use un monto no negativo con maximo 2 decimales, sin simbolos.", budgetMax: "El presupuesto no puede superar 1,000,000.00 USD.",
  conflictTitle: "Alguien cambio esta campana antes de que guardara.", conflictBody: "Su texto se conserva. Cargue el registro mas reciente, revise y guarde de nuevo.",
  rebase: "Cargar lo ultimo y conservar mi texto", conflictGone: "No se encontro el registro mas reciente.",
  contentShort: "La revision requiere al menos 10 caracteres de contenido.",
  approveTitle: "Confirmar aprobacion interna", approveBody: "Confirmo que es solo una revision interna de contenido y no autoriza gasto, publicacion ni servicios de pago.",
  confirmApprove: "Confirmar aprobacion", cancelShort: "Cancelar",
  status: "Estado", DRAFT: "Borrador", IN_REVIEW: "En revision", APPROVED: "Aprobada (interna)", PAUSED: "Pausada", ARCHIVED: "Archivada",
  version: "Version", updated: "Actualizada", noContent: "Sin contenido aun.", actionFail: "La accion fallo: ",
  noAccountEnv: "Datos privados borrados.",
};
export const dict = { en, es };
export type Dict = typeof en;

export function useLang(): [Lang, (l: Lang) => void, Dict] {
  const [lang, set] = useState<Lang>(() => {
    try { const v = localStorage.getItem("genesis_owner_lang"); if (v === "es" || v === "en") return v; } catch { /* ignore */ }
    return "en";
  });
  const setLang = (l: Lang) => { set(l); try { localStorage.setItem("genesis_owner_lang", l); } catch { /* ignore */ } };
  return [lang, setLang, dict[lang]];
}
