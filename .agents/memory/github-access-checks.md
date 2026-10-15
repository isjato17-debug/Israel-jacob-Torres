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

When a user reports completed Shell sign-in but the agent cannot authenticate, compare
effective GitHub CLI configuration directories and credential-file existence only.
Do not assume that Shell and agent contexts differ, or read credential-file contents.
An explicitly selected shared configuration directory for a supported device sign-in
can remove ambiguity without requesting tokens.

**Why:** A reported reconnection still left no CLI login file visible to the agent in
either its effective configuration directory or the normal home directory.

**How to apply:** First test the actual Git transport with `git ls-remote` against the
configured origin. Working Git authentication does not require a working `gh` login.
Compare remote branch commit IDs with local source before requesting more authorization.
Only when an additional CLI sign-in is actually necessary, keep the device-flow process
alive through browser approval, configure Git through `gh auth setup-git`, then verify
identity, repository permissions and remote history before attempting a write.

Git source access can work even when both the default and explicitly selected `gh`
configuration contexts report no login.

**Why:** Repository refs and the exact latest source commit were successfully verified
through Git while both CLI identity checks still requested authentication.

**How to apply:** Do not repeat browser-device authorization solely to resolve a `gh`
login message when the user's actual Git operation already works. Treat verified source
presence, read access and write permission as separate claims; a read alone proves no
write capability. Preserve remote branch spellings rather than silently renaming them.
