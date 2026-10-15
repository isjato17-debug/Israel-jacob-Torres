"""No-cost TEST signatures only; not executed contracts, biometrics or agency signatures."""
import hashlib
import hmac
import html
import json
import os

from fastapi import HTTPException
from ..config import settings
from .document_engine import canonical, render, digest

DISCLOSURE_VERSION = "test-sign-v1"
DISCLOSURE = (
    "TEST ONLY — this creates signature evidence for a software demonstration, not an executed "
    "contract or government-accepted signature. You are signing only as the test provider, not "
    "on behalf of the client. Review the exact document, confirm its information, and expressly "
    "consent to this test. Account-password reauthentication is required. A copy is available "
    "for download; consent can be withdrawn for further test processing. No paid provider, "
    "biometric data, customer transmission or live submission is involved."
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mac(envelope, artifact_hash):
    # Existing secret is used at runtime only; no new credential or database key is stored.
    secret = os.environ.get("SESSION_SECRET") or settings.jwt_secret
    if not secret:
        raise HTTPException(503, "Test-signature audit key is unavailable")
    return hmac.new(secret.encode(), ("BIG:test-sign:v1:" + canonical(envelope) + ":" +
                                     artifact_hash).encode(), hashlib.sha256).hexdigest()


def render_signed(source, envelope):
    body = render(source).decode()
    evidence = html.escape(json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2))
    return body.replace("</html>", '<section><h2>TEST SIGNATURE EVIDENCE — NOT A LEGALLY '
                        'EXECUTED CONTRACT</h2><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'
                        + evidence + "</pre></section></html>").encode()


def _verify(signature, document):
    envelope = json.loads(signature.envelope_json)
    return (digest(json.loads(document.source_json)) == envelope["document_hash"] == document.content_hash
            and envelope["document_id"] == document.id
            and envelope["project_id"] == signature.project_id
            and envelope["user_id"] == signature.user_id
            and envelope["signature_id"] == signature.id
            and sha(render_signed(json.loads(document.source_json), envelope)) == signature.artifact_hash
            and hmac.compare_digest(mac(envelope, signature.artifact_hash), signature.audit_mac))


def verify(signature, document):
    try:
        return _verify(signature, document)
    except (ValueError, TypeError, KeyError):
        return False
