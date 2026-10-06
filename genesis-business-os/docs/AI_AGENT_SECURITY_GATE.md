# AI / Agent Security Gate
All model, retrieved, uploaded, web, email, connector and Community content is untrusted. Before enabling agentic provider writes:
- keep system/policy instructions outside retrieved content;
- label provenance and trust level;
- prevent retrieved text from granting permissions;
- use typed tool schemas and server-side allowlists;
- bind capabilities to tenant, user, action, resource, risk tier and expiry;
- independently validate tool arguments and tool output;
- redact secrets before model calls/logging;
- isolate tenant retrieval/vector namespaces;
- scan/limit uploads and archive expansion;
- defend SSRF and unsafe URL redirects;
- test prompt injection, indirect injection, retrieval poisoning, fake approval text, tool-call injection, secret extraction, cross-tenant retrieval and data exfiltration;
- disable external writes in Lockdown Mode.
