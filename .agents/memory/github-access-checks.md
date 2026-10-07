---
name: GitHub access checks
description: Distinguish a local GitHub CLI authentication failure from revoked connector authorization.
---

Verify connector authorization health separately from workspace CLI authentication. A local `gh` login error alone is not evidence that the user's OAuth connection is revoked.

**Why:** The project connection was confirmed attached and healthy with repository permissions, but the workspace `gh` command still requested login after binding was confirmed.

**How to apply:** Do not request tokens, inspect stored credentials, or repeatedly reconnect a healthy integration. If repository discovery is unavailable and no GitHub remote exists, request the intended repository URL rather than guessing a target or overwriting another repository.
