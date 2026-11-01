# Forms

What changes with the form. Rules here add to `style.md`; they do not repeat
it.

## Blog post

- **Reader:** reads by choice, can leave at any paragraph, usually skims first.
- **Opening:** the problem or the result within the first paragraph. No
  background chapter before the reader knows why it matters.
- **Structure:** one line of argument. Headings mark real turns in it; a post
  of 2,000 words rarely needs more than five.
- **Evidence:** code, measurements, and figures carry the argument; prose
  explains what they show. Every code block and figure is referred to in the
  text.
- **Ending:** stop after the last point. A short note on limits or next steps
  is enough.
- **Series post:** link the posts it builds on instead of re-explaining them,
  and state in one sentence what this post adds.
- **Risk:** the friendly-explainer voice — rhetorical questions, "let's",
  cheerful transitions. Keep the tone of an engineer explaining to a peer.

## Technical report

- **Reader:** needs to decide or reproduce something; reads the summary and
  jumps to the section that matters.
- **Opening:** a summary that states the question, the method in one sentence,
  and the result with its numbers. A reader who stops there has the answer.
- **Structure:** sections the reader can find by name: setup, method, results,
  discussion of limits. Results report what was measured; interpretation is
  kept apart.
- **Reproducibility:** versions, hardware, configurations, and commands
  precise enough to rerun. Units on every number.
- **Tone:** neutral and exact. Every comparison names its baseline.
- **Risk:** inflated significance and vague limits. State what was not tested.

## Technical talk

A talk is heard once, at the speaker's pace. Write the script and the slides as
two artifacts with different jobs: the script carries the reasoning, the
slides carry what the eye needs.

### Script

- Short sentences in spoken order; one idea per sentence.
- Say where the talk is going at the start and where the listener is at each
  turn. Spoken signposting is needed here and is not a pattern finding.
- Name a number only when the listener must remember it; round it.
- Mark each slide change in the script, e.g. `[slide 4]`.
- Time: about 150 Chinese characters or 120 English words per minute of
  speech. Fit the script to the slot in the brief.

### Slides

- One point per slide; the title states that point as a sentence.
- Diagrams, code, and plots over text. No paragraph copied from the script.
- At most about 30 words of text per slide, code excluded.
- Code on a slide is short enough to read in the time it is shown; highlight
  the lines that matter.
- Each plot states its axes, units, and the takeaway in the title.

### Risk

Slides that read as an outline of bullets, and a script that reads as an
article. Both mean the two artifacts were written as one.
