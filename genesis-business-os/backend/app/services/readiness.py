"""Dependency checks expose only generic booleans, never URLs, credentials or exceptions."""
from sqlalchemy import text, inspect
from .migration_runtime import assert_current_revision


def check_readiness(engine, environment):
    checks = {"database": False, "schema": False}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = True
        if environment == "production":
            assert_current_revision(engine)
        else:
            # Development has no migration stamping; check the active schema, not just process life.
            tables = set(inspect(engine).get_table_names())
            if not {"users", "onboarding_journeys", "growth_campaigns", "ai_consultations",
                    "partner_applications", "partner_promotions", "consultation_privacy",
                    "business_ideas", "idea_revisions", "business_projects", "business_passports",
                    "document_workflows", "generated_documents", "document_approvals"} <= tables:
                return checks
        checks["schema"] = True
    except Exception:
        # Intentionally redact database driver/host/schema exception text.
        pass
    return checks
