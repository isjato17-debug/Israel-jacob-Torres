import { useEffect, useState } from "react";
import { getOwnerAccess } from "./owner-api";
import type { Language } from "./journey-api";
import { dict } from "./guided-i18n";

export default function OwnerAccessLink({ accountId, language }: { accountId: string | null; language: Language }) {
  const [allowed, setAllowed] = useState(false);
  useEffect(() => {
    let cancelled = false;
    setAllowed(false);
    if (accountId) {
      getOwnerAccess().then((access) => {
        if (!cancelled && access.account_id === accountId) setAllowed(access.owner_access);
      }).catch(() => { if (!cancelled) setAllowed(false); });
    }
    return () => { cancelled = true; };
  }, [accountId]);
  return allowed ? <a className="gx-btn sec" href={`${import.meta.env.BASE_URL}next/owner/`}>
    {dict[language].ownerLink} <small>{dict[language].legacyNote}</small>
  </a> : null;
}
