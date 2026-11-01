---
name: write-article
description: Use when planning, drafting, revising, or reviewing a blog post, technical report, or technical talk (script or slides), alone or as part of a series. Covers the writing brief, persisted working state under .writing/, the style rules against machine-sounding prose, math notation, and the two-part review of reading quality and factual and mathematical correctness.
metadata:
  workflow: article-writing
---

# Write Article

The lead agent writes. Reviewers judge: Bedivere reviews how the text reads,
Perceval checks whether its content is correct. Working state lives in files so
that a long session, a compacted context, or a new session can resume without
relying on memory.

## References

| File | Read when |
| --- | --- |
| `references/style.md` | Before drafting or revising, and by every reading reviewer |
| `references/forms.md` | Before structuring or drafting; read the section for the form in the brief |
| `references/notation.md` | Before writing or reviewing anything with math, symbols, or quantities with units |
| `references/review.md` | Before requesting a review |

Paths are relative to this skill's base directory.

## Working state

```
.writing/<series>/series.md            # shared by every post in a series
.writing/<series>/<post>/brief.md
.writing/<series>/<post>/sources.md
.writing/<series>/<post>/reviews.md
.writing/<slug>/brief.md, sources.md, reviews.md   # a post outside any series
```

`.writing/` sits at the root of the repository that holds the article. Do not
edit `.gitignore` for it; whether it is tracked is the user's decision. The
article itself is the target file the user names; write the draft there and
leave history to version control. Do not keep numbered draft copies.

`series.md`:

```markdown
# Series: <title>

## Reader
## Language and tone
<Chinese is the primary language. English version by default: yes / no>
## Rendering target
<renderer, delimiters, how it was determined; see references/notation.md>
## Terms
<中文 — English — note; one line each; both versions use exactly these>
## Symbols
<symbol — meaning — shape or unit; one line each>
## Posts
<order, slug, target files, status, one-line purpose>
## Covered so far
<per finished post: the points a later post may rely on without re-explaining>
```

`brief.md`:

```markdown
# Brief: <post title>

Target file (zh):
Target file (en): <path, or none>
English sync: not started / in sync / pending since <date>
Form: blog post / technical report / talk script / slides
Stage: discussion / outline / drafting / review / done

## Purpose
## Reader
<only what differs from series.md>
## Scope
## Out of scope
## Outline
<approved outline; mark it approved with the date>
## Decisions
<decision — reason — date>
## Post-specific style rules
<patterns the user rejected in this post>
```

`sources.md` lists each checkable claim: the claim, its location in the
article, the source URL or path, and its status (verified, contradicted,
unverifiable, or missing source). `reviews.md` lists each finding by id with
its round, location, summary, and disposition: fixed, rejected with the
reason, or open. Every finding id carries the version it applies to, e.g.
`BED-003 (en)`.

## Languages

Chinese is the primary version: discussion, outline, drafting, and both
reviews happen on it. An English version, when the brief names one, is
written only after the Chinese version is accepted, by adapting it to English
usage, not by translating sentence by sentence. Structure, facts, numbers,
formulas, code, and conclusions stay identical; sentences are rebuilt the way
an English technical writer would write them. Both versions are held to the
machine-sounding and translationese patterns of their own language in
`style.md`.

## Resuming

At the start of a session, after a context compaction, and whenever the user
asks to continue, read `series.md`, `brief.md`, and `reviews.md`, then the
target files, before writing anything. The files are authoritative over what
you remember. Update `Stage` in `brief.md` when the stage changes.

## Entry points

| Request | Start at |
| --- | --- |
| New series or post | 1. Discuss |
| Continue | Resuming, then the recorded stage |
| Revise an existing article | 3. Draft, after a brief exists |
| Review only | 4. Review; create `brief.md` from the user's statement of purpose and reader if none exists |
| Small edit (wording, typo, one sentence) | Edit directly; record in `reviews.md` that review was skipped |

## Workflow

1. **Discuss.** Settle reader, purpose, form, scope, whether an English version is needed, and tone with
   the user, and write them to `brief.md` (and `series.md` for a new series).
   Ask one question at a time. Do not draft during discussion.
2. **Outline.** Write the outline to `brief.md`: one line per section stating
   what the reader knows after it. Wait for the user to approve it; drafting
   starts only after approval.
3. **Draft.** Read `style.md`, the matching section of `forms.md`, and
   `notation.md` if the article has math. Write into the target file. Then run
   the pattern scan from `style.md` over the target and fix what it finds
   before any review.
4. **Review.** Follow `review.md`. Bedivere reviews every complete draft;
   Perceval runs in parallel when the article contains facts, numbers, or math
   that can be checked. Record each finding in `reviews.md`, then fix it or
   reject it with a reason. Re-review after fixing blocking findings. After
   three rounds with blocking findings still open, stop and ask the user.
5. **English version.** Skip when `Target file (en)` is none. After the user
   accepts the Chinese version, write the English adaptation, run the English
   pattern scan, and send it to Bedivere only, with both files in the packet;
   content was verified on the Chinese version. Set `English sync: in sync`
   when the user accepts it.
6. **Done.** Set `Stage: done`, and add the post's terms, symbols, and covered
   points to `series.md`.

When the Chinese version changes after the English version exists, set
`English sync: pending since <date>`; bring the English version back in line
and repeat its reading review before setting it to `in sync`.

## Rules

- The article's tone comes from the brief, not from the reply style used with
  the user.
- Never invent a source, figure, quote, or citation. A claim without a source
  goes to `sources.md` as missing and is raised with the user; the article
  never carries a placeholder such as "[citation needed]".
- Write only facts the sources support. When a number comes from a
  calculation, keep the inputs in `sources.md` so it can be rechecked.
- When the user marks a passage as machine-sounding, fix it, add the pattern to
  `Post-specific style rules`, and, if it is general, propose an addition to
  `references/style.md` in the round-table repository. The installed copy of
  this skill is not edited directly.
- A reviewer's finding is evidence, not a verdict. Reject a finding that
  conflicts with the brief, and say why in `reviews.md`.
