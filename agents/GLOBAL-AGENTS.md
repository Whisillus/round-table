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
- Validate external inputs at trust boundaries. Inside those boundaries, trust
  established types, preconditions, and invariants unless concrete evidence shows
  they can be violated. Do not repeat validation or handle states excluded by
  those contracts.
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

## Local reference material

When `~/workspace/reference` exists, it holds local reference material for GPU
and CUDA work. Read it freely; do not modify it, build in it, or run its scripts
unless asked.

- `repo/` — upstream projects as git submodules, such as cutlass,
  flash-attention, FlashMLA, DeepGEMM, flashinfer, and TransformerEngine. List
  the directory for the current set; some submodules may be uninitialized.
- `docs/` — versioned NVIDIA documentation, such as `cuda-13-3/`. Cite the
  versioned copy and name the version.
- `article/` — papers on GPU microarchitecture.

For CUDA, PTX, GPU kernels, or these libraries, prefer the local checkout over
web search for implementation details, and the versioned docs for API and
instruction semantics. Local copies are snapshots and can lag upstream: when the
task depends on the latest release, API, or behaviour, check the online source
and say which version each claim comes from. Its own `AGENTS.md` applies when
working inside it.

## Version control

- Do not commit, stage, or unstage anything unless explicitly asked. Staging
  decisions belong to the user.
- Never push, and never rewrite history that has been shared.
- When a commit is requested, follow the repository's existing message style and
  keep one logical change per commit.
