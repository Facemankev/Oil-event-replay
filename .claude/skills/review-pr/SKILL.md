---
name: review-pr
description: Help a Market Ripple partner review the other partner's pull request. Use when someone says "review Dad's pull request", "review Brendan's changes", "what's PR #N", or asks what's waiting for their review. Explains the change in plain words, shows it running, checks it against the plan and principles, and posts their verdict.
---

# Review a pull request

The reviewer may not read code, so your job is to make the change
understandable and check it carefully on their behalf. The decision is
theirs.

## 1. Find it

If no number was given: `gh pr list --state open --search "review-requested:@me"`,
or the other partner's open pull requests. If there are several, ask which.

## 2. Understand it

- `gh pr view <n>` (description, comments, checks) and `gh pr diff <n>`.
- The linked log entry in `team/log/` and any issue it mentions.

## 3. Check it

- **Tests:** do the GitHub checks pass (`gh pr checks <n>`)?
- **Principles:** compare against `CLAUDE.md` and `team/DECISIONS.md`. Look
  for invented or unsourced prices, claims of cause, and filled-in missing
  data.
- **Plan:** does it match a milestone or to-do in `team/PLAN.md`? Flag
  surprises.
- **Size:** if it's too big to review sensibly, say so. Asking for it to be
  split is a fair request.
- **Safety:** no secrets, keys or personal details added. Check that the
  GitHub "Privacy check" passed. Any change to `.claude/hooks/guard.sh`,
  `.claude/settings.json`, `.claude/allowed-words.txt` or `.gitignore`
  weakens or changes the guardrails. Point it out explicitly, even if it
  looks harmless.

## 4. Show it

If it changes the website, offer a preview. First check `git status`. If
there are unsaved changes, don't switch branches. Instead use a separate
worktree (`git worktree add ../review-<n> <branch>`). Serve it with
`python3 -m http.server 8000` and open http://localhost:8000.

## 5. Explain it

```
What it does: <2–3 plain sentences>
Why: <the reason given, linked to the plan>
What to look at: <specific things to try in the preview>
Concerns: <anything from step 3, or "none found">
```

## 6. Record their verdict

Ask whether they want to **approve**, **ask for changes** or **just
comment**, and what to say. Show the exact text, then post it with
`gh pr review <n> --approve | --request-changes | --comment --body "..."`.
Never merge the other partner's pull request. The author merges after
approval. Remove any review worktree afterwards.
