---
name: write-git-commit
description: Use when preparing, staging, and creating Git commits safely with repository-aware commit messages, conservative staging, and no destructive Git operations.
metadata:
  workflow: git-commit
---

# Write Git Commit

Use when asked to prepare, stage, and create a Git commit safely.
Follow the active agent's permissions and the user's authorized scope; loading this skill does not authorize staging or committing.

## Hard Limits

- Do not edit project files.
- Do not push, pull, branch, amend, reset, clean, checkout, switch, merge, rebase, stash, tag, `git rm`, `git mv`, or `git worktree`.
- Do not use interactive Git commands, empty commits, or hook/signing bypasses.

## Inspect

Run these checks before staging or committing:

- `git status --porcelain=v1 -uall`
- `git diff --cached`
- `git diff`
- `git log --format='%s' -20`

Stop if there are no staged, unstaged, or untracked changes.

## Stage

- If anything is staged, commit only staged changes unless asked to stage more.
- Stop before committing staged changes that look secret, generated, unrelated, or unsafe.
- If staged and unstaged changes overlap, preserve the unstaged changes and report them after committing the staged content.
- If nothing is staged, stage only changes that clearly belong to the request.
- Use `git add --all` only when asked for all changes and status/diffs show no unrelated or suspicious paths.
- Use `git add -- <path>...` for selective commits.
- Inspect untracked files that will be staged; do not rely on paths alone.
- Stop before staging or committing likely secrets, local config, generated output, dependency folders, caches, logs, large binaries, or unrelated work.
- Treat `.env*`, `.npmrc`, `.pypirc`, `.netrc`, private keys, `secrets.*`, and `credentials.*` as suspicious.
- If `write-gitignore` changes `.gitignore`, stage it only when the prompt permits staging new changes.
- After staging anything, re-run `git diff --cached` before writing the message.

## Message

- Base the message on the staged diff, not just the prompt.
- Follow the repository's documented commit conventions and existing message style; use recent history to identify consistent patterns.
- Use Conventional Commits when required by project conventions, requested by the user, or strongly supported by history.
- If using Conventional Commits, choose the type and scope according to the project's conventions and the staged change; preserve established types such as `docs`, `test`, or `refactor` rather than forcing them into `chore`.
- Otherwise use a concise imperative subject with no trailing period.
- Add a body only when it adds useful context.
- Do not copy weak history patterns such as vague subjects, noisy merge messages, or PR suffixes like `(#123)`.

## Commit

Use:

```bash
git commit -F - <<'EOF'
[commit message]
EOF
```

The quoted delimiter prevents shell expansion in the message.

After a successful commit, run `git status --porcelain` and report any residual changes.

## Failure

- Do not amend after hook changes.
- If commit fails, stop; do not restage, retry, or amend without a new user instruction.
- Report the failure and current state concisely.
- On success, report the commit hash and subject.
