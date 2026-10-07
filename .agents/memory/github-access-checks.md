---
name: GitHub access checks
description: Distinguish a local GitHub CLI authentication failure from revoked connector authorization.
---

Verify connector authorization health separately from workspace CLI authentication. A local `gh` login error alone is not evidence that the user's OAuth connection is revoked.

**Why:** The project connection was confirmed attached and healthy with repository permissions, but the workspace `gh` command still requested login after binding was confirmed.

**How to apply:** Do not request tokens, inspect stored credentials, or repeatedly reconnect a healthy integration. If repository discovery is unavailable and no GitHub remote exists, request the intended repository URL rather than guessing a target or overwriting another repository.

An actual authentication rejection from GitHub is different from a local CLI login error, even when connection metadata still reports healthy. Git-provider connections may also fail to render both the reconnect card and the standard connect card.

**Why:** Both card paths failed in this workspace after GitHub rejected a normal source push; account-level health did not establish working Git write access.

**How to apply:** Follow authorization recovery for an actual provider rejection. If the supported cards cannot open, stop retrying them, consult current Replit documentation, and direct the user to refresh GitHub under account settings → Git Providers. Do not substitute token handling or another assistant.
