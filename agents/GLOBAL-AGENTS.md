# Global working agreements

These are the working agreements this repository produces. They are written to be
copied to `~/.agents/AGENTS.md`, where they apply to every repository; the copy
step belongs to README.md so that this file stays valid wherever it lands.

They describe how work is done, not a checklist to be quoted back. Where a rule
conflicts with a convention the surrounding code already establishes, the code
wins — report the conflict instead of choosing silently.

## Failure handling

- Fail fast at the boundary: validate required inputs, configuration, and
  environment before doing work, and surface the exact blocker — path, value,
  exit code — instead of a generic message.
- No silent fallback, default substitution, catch-all handler, or retry loop
  unless the project already does it or the user asks for it. Missing required
  state is a real failure.
- Error text must let the reader act: say what was expected, what was found, and
  where.

## Reuse and abstraction

- Before writing a helper, search for the utility, type, or constant that already
  does it. Reuse beats local neatness.
- Inline a helper when it has one call site, or a body short enough to read in
  place; a one-line wrapper earns nothing. Duplication is acceptable when the copy
  is short and the shared form would need parameters, options, or a name the
  domain does not have.
- Extract when several call sites share one shape, or when the name carries a
  domain concept the reader needs.
- No speculative generality: no unused parameters, options, flags, or hooks added
  for a case that has not occurred. Delete the abstraction when its second use
  disappears.
- Prefer the standard library, or a few explicit lines, over a new dependency.

## Change scope

- Make only the changes the task requires, and be able to give a concrete reason
  for each. Passing tests or satisfying the literal instruction is not sufficient
  justification; a change that does not belong in the design is unfinished work.
- Smallest correct diff. Do not refactor, reorder, or reformat code the task did
  not require; unrelated cleanups make review harder.
- Structure follows the problem: each responsibility sits where a reader would
  look for it, and the dependency direction matches the surrounding module.
- Follow the surrounding file's format, naming, error style, and idiom rather
  than a personal preference or a global ideal. Match the file being edited, not
  the one you would have written.
- Delete code instead of commenting it out. Version control is the archive.

## Readability

- Comment why, not what. Delete comments that restate the next line.
- Names are domain terms, not abbreviations and not type echoes: `retryCount`
  over `rc`.
- Prefer early returns and flat control flow over nested conditionals.
- A reviewer should be able to predict the next line. Cleverness that needs a
  comment to decode is a rewrite, not a comment.

## Verification

- Run the narrowest meaningful check before reporting completion. Say what was
  run, and say plainly when nothing could be run.

## Version control

- Do not commit, stage, or unstage anything unless explicitly asked. Staging
  decisions belong to the user.
- Never push, and never rewrite history that has been shared.
- When a commit is requested, follow the repository's existing message style and
  keep one logical change per commit.
