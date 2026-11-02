# Review

Two independent reviews, run in parallel as subagents. Neither reviewer may
edit files; the lead agent applies fixes and keeps `reviews.md` and
`sources.md` current.

| Review | Reviewer | Question |
| --- | --- | --- |
| Reading | `bedivere` | Does it read as written by a person for this reader? |
| Content | `perceval` | Is everything it states true and correctly derived? |

Bedivere reviews every complete draft of either version. Perceval runs on
the Chinese version when it states checkable facts, figures, citations,
derivations, or calculated numbers; the English version inherits that check
through the parity check below.

## Task packet

Every review task names:

- the target file and its version (zh or en), and that the review covers the
  whole file or the listed sections only;
- for an English review, the accepted Chinese version as well;
- the path of `brief.md`, and of `series.md` if the post is in a series;
- the skill to load (`write-article`) and the references to read;
- the findings already rejected in `reviews.md`, with their reasons, and the
  instruction not to raise them again unless the text changed;
- for Bedivere, the pattern-scan hits that were kept and why;
- for Perceval, the path of `sources.md`;
- when the article has figures: for Bedivere, the rendered PNG of each figure
  (reviewers may not generate files, so the lead agent renders them); for
  Perceval, each figure's source script and its data file if it has one;
  existing assets without a source are listed as such;
- that the reviewer must not edit any file and returns findings as text.

## Reading review (Bedivere)

Read `references/style.md`, `references/forms.md` (the section for the form),
and `references/notation.md` if the article has math. Check, in this order:

1. **Machine-sounding prose and translationese.** Every pattern in
   `style.md` that applies to the version's language, including the shape
   patterns no scan can find. This check has the highest priority: quote the
   passage, name the pattern, and give the rewrite or the deletion.
   Translationese is checked on the Chinese version too, though it is not a
   translation.
2. **Reader gaps.** A term used before it is defined; a step the target reader
   cannot make alone; a conclusion without its reason; content the reader
   already knows.
3. **Brief and form.** Scope kept, purpose served, outline followed, form
   conventions met.
4. **Series consistency.** Terms and symbols match `series.md`, or the
   brief's tables for a standalone post; nothing re-explains a point listed
   under `Covered so far`.
5. **Notation and rendering.** Symbols follow `notation.md` and the series
   table; delimiters and environments suit the recorded rendering target.
6. **Redundancy.** Sentences and paragraphs that can be deleted without loss.
7. **Parity (English version only).** Against the Chinese version: the same
   sections in the same order, and identical numbers, formulas, code, claims,
   and conclusions. Any difference in content is a finding; a difference in
   wording is not.
8. **Figures.** Open each rendered PNG with `read_image` and check it against
   `references/figures.md`: one point per figure, stated in the caption and
   referred to in the text; labels, symbols, and numbers matching the text and
   `notation.md`; English-only text in the figure; palette meanings kept;
   overlapping, clipped, or illegible text; decoration. If `read_image` fails,
   say so in the findings instead of judging the figures from their source.

## Content review (Perceval)

Read `references/notation.md` if the article has math. Check:

1. **Facts and citations.** Each claim is supported by an authoritative source:
   official documentation, the paper, or upstream source code. Give the URL or
   path. Note version-dependent claims and which version the source states.
2. **Numbers.** Recompute every derived number from its stated inputs; a
   printing command such as `python3 -c` is allowed. Check units and orders of
   magnitude.
3. **Math.** Each derivation step follows from the previous; shapes agree;
   stated complexities match the algorithm described.
4. **Figures.** Read each figure's script and data: the parameters match the
   text, the computed shapes, offsets, and tile counts are correct, and plotted
   values come from the data file unchanged. A figure without a source is
   reported as unverifiable, not as wrong.

## Findings

Bedivere uses its own format, with ids `BED-001` onward. Perceval uses:

```
PER-001 · <severity> · <blocking yes/no> · <heading> L<line>
Claim: <the sentence or formula>
Verdict: holds / does not hold / unverifiable
Evidence: <URL or path, the quoted fragment, or the recomputation>
Fix: <the correction, or what source would settle it>
```

Locate every finding by heading and line number in the target file, and tag
its id with the version: `BED-003 (en)`, `PER-001 (zh)`.

Severity:

- **Critical**: a false fact, wrong number, or invalid derivation, or a content
  difference between the two versions. Always blocking.
- **High**: a passage that is machine-sounding or that the target reader cannot
  follow; an unsupported claim. Blocking.
- **Medium**: a local pattern, inconsistency, or redundancy that a reader
  notices. Blocking when several accumulate in one section.
- **Low**: polish. Never blocking.

## After the review

Copy each finding into `reviews.md` with its round number, update
`sources.md` from Perceval's verdicts, then fix or reject each finding. Choose the
follow-up reviewers by what the fixes changed, not by whose findings they
answered:

- any change in wording: Bedivere, on the changed sections;
- any change to a fact, number, formula, citation, or code in the Chinese
  version: Perceval, on the changed sections;
- any regenerated figure: Bedivere, on its new rendering, and Perceval when
  its script, parameters, or data changed.

Nearly every fix changes wording, so Bedivere runs in almost every round. State
in the packet which sections changed.
