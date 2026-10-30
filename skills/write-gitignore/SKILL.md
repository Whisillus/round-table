---
name: write-gitignore
description: Use when checking untracked Git files and conservatively updating .gitignore for generated files, secrets, local dependencies, caches, logs, OS/editor artifacts, and project-specific build outputs.
metadata:
  workflow: gitignore-maintenance
---

# Write Gitignore

Use this skill when asked to inspect untracked files and update `.gitignore`.
Follow the active agent's permissions and the user's authorized scope; loading this skill does not authorize file changes.

## Responsibility

- Check for untracked files that should not be versioned.
- Update only `.gitignore` with conservative ignore patterns.
- Never modify code files, non-gitignore project files, or tracked source content.
- Never make git commits.

## Workflow

1. Check for untracked files using `git status --porcelain=v1 -uall`.
2. Identify files that should be ignored using the heuristic rules below.
3. Read the existing `.gitignore` before editing it; create it only if missing.
4. Add appropriate non-duplicate patterns for files that should be ignored.
5. Report which patterns were added, or report `No changes needed` if `.gitignore` is already correct.

## Heuristic Rules For Ignoring Files

Apply these rules only to files or directories present in the project. Be conservative: when unsure, do not add the pattern.

### Common Directories

Add directory patterns with a trailing slash.

- `node_modules/` - Node.js dependencies
- `dist/`, `build/`, `out/` - build outputs
- `.cache/`, `.tmp/`, `tmp/` - cache and temp directories
- `vendor/` - vendored dependency directories, if project policy does not track them
- `.venv/`, `venv/`, `__pycache__/` - Python virtual environments and cache
- `.idea/`, `.vscode/`, `.sublime-*` - IDE configuration, only if project-wide settings should not be tracked
- `coverage/`, `.nyc_output/` - test coverage reports
- `logs/`, `log/` - log directories

### Environment And Secrets

Treat these names as candidates for inspection, not automatic ignore rules. Confirm their purpose from project documentation and surrounding usage; do not print secret values.

- `.env`, `.env.local`, `.env.*.local`, `*.env`, `.env.*` - ignore only confirmed local secrets or machine-specific environment files.
- `*.pem`, `*.key`, `*.crt` - distinguish private keys and local credentials from public certificates and test fixtures; the extension alone is not sufficient reason to ignore a file.
- `secrets.*`, `credentials.*` - ignore only files confirmed to hold local credentials or secrets.

Prefer exact paths for confirmed local files. Use a wildcard only when project evidence supports ignoring all files it would match. Preserve environment templates such as `.env.example`, `.env.sample`, `.env.template`, and documented example config files, including untracked ones, unless project evidence shows they are local-only.

### Build Artifacts And Outputs

- `*.log` - log files
- `*.pyc`, `*.pyo`, `*.class` - compiled files
- `*.min.js`, `*.min.css` - minified files, only when generated from tracked sources
- `*.swp`, `*.swo`, `*~` - editor swap and backup files

Do not blindly ignore lockfiles. Lockfiles such as `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`, `poetry.lock`, `uv.lock`, `Cargo.lock`, `Gemfile.lock`, and similar dependency lockfiles are often intentionally tracked. Ignore a lockfile only when project evidence shows it is local-only or generated noise.

### OS-Specific Files

- `.DS_Store`, `Thumbs.db` - OS metadata files

### Project-Specific Patterns

- Check for framework-specific generated outputs, such as `.next/`, `.nuxt/`, `nuxt-dist/`, `.svelte-kit/`, `.astro/`, or similar directories that appear as untracked generated artifacts.
- Look for large binary files, archives, local database files, generated assets, or local tool state such as `.scriptor/` that should not be versioned.
- Do not ignore project source, documentation, fixtures, migrations, checked-in assets, or configuration files unless the user or project evidence clearly indicates they are local-only.

## Pattern Format

- For directories, use a trailing slash so the pattern matches directories only.
- A leading `/` anchors a pattern to the directory containing that `.gitignore`. In the repository-root `.gitignore`, use `/dirname/` or `/filename` for root-only paths.
- Use unanchored basename patterns such as `dirname/`, `filename`, or `*.ext` only when matching at every depth beneath that `.gitignore` is intended.
- For patterns that should match in any directory, use `**/pattern` only when necessary.

## Adding Patterns

- Avoid duplicates by checking existing `.gitignore` patterns first.
- Add patterns at the end of `.gitignore`, grouped by category with a concise comment header.
- Preserve existing `.gitignore` content and ordering unless an existing pattern is clearly incorrect.
- Prefer specific patterns over broad patterns when broad patterns could hide source files.

Example addition to the repository-root `.gitignore` for confirmed root-level dependencies, build output, and a local environment file:

```gitignore
# Local dependencies and build output
/node_modules/
/dist/

# Local environment
/.env
```

## Reporting

- Report each pattern added and the reason it was added.
- If nothing changed, report `No changes needed`.
- If a candidate was intentionally not ignored because it was ambiguous, mention that briefly when useful.
