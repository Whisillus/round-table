# Style

One standard for the writer and the reviewer. The writer reads it before
drafting; the reviewer checks the draft against it item by item. Rules marked
in a post's `brief.md` or the series' `series.md` take precedence.

The Chinese version is checked against the general rules, the Chinese rules,
and every pattern marked for Chinese; the English version against the general
rules, the English rules, and every pattern marked for English. A model writes
translationese in both directions: Chinese that follows English syntax, and
English that follows Chinese syntax. Both are findings.

## What good text does

### Both versions

- **Each paragraph makes one point**, and its first sentence says which.
- **Claims carry their reason.** "X is faster" is incomplete; "X is faster
  because it reads each tile once" is a claim.
- **Specific over general.** Name the kernel, the shape, the number, the
  version. A sentence that would fit any article on the topic says nothing.
- **Terms are defined before use**, once, at the point the reader first needs
  them. Keep the same word for the same thing throughout.
- **Prose for reasoning, lists for parallel items.** An argument whose steps
  depend on each other is a paragraph, not bullets. Use a list only when the
  items are genuinely parallel and the reader may scan them.
- **Paragraph length follows content.** A short point gets a short paragraph.
  Uniform paragraph sizes and mirrored section shapes read as generated.
- **Cut what the reader already has.** Do not restate the previous section,
  explain what the target reader certainly knows, or announce what comes next.
- **Plain statements.** State the fact at the strength the evidence supports;
  no intensifiers, no hedges stacked on hedges.

### Chinese

- Keep an English term when no established Chinese term exists, and gloss it
  in one clause on first use. Use the wording in the series' `Terms` table.
- Put a space between Chinese and Latin letters or digits unless the series
  says otherwise. Use full-width punctuation in Chinese sentences.
- Short sentences with the verb close to the subject. Break a long modifier
  chain (「……的……的……的」) into two sentences.

### English

- Active voice and a concrete subject: "the kernel reads each tile once", not
  "each tile is read once by the kernel" or "a single read is performed".
- Verbs over nominalizations: "we measure", not "we perform a measurement".
- One idea per sentence; a sentence over about 30 words is usually two.
- Use the series' `Terms` table for every term that has a Chinese counterpart.

## Machine-sounding patterns

Each pattern below is a finding in the version whose language it is
written in; patterns without a language apply to both. The fix is almost
always to delete the phrase or replace it with the specific content it stands
in for.

### Empty openings
- 「在当今……的时代」「随着……的快速发展」「近年来，……备受关注」
- "In today's fast-paced world", "In the ever-evolving landscape of"
- Fix: open with the problem, the result, or the concrete situation.

### Formulaic closings and recaps
- 「总之」「综上所述」「总而言之」「总的来说」 followed by a restatement
- A summary paragraph at the end of every section
- "In conclusion", "To sum up", "Overall,"
- Fix: end a section on its last real point; end the article on what the
  reader can now do or what remains open.

### Filler and signposting
- 「值得注意的是」「需要指出的是」「可以说」「不难发现」「众所周知」
- 「让我们深入探讨」「接下来我们来看」「下面我们将……」「本文将……」
- "It's worth noting that", "Let's dive into", "delve", "In this section, we will"
- Fix: state the noted thing directly; drop the announcement.

### Set constructions
- 「不仅……更是……」「这不仅是 X，更是 Y」「与其说……不如说……」
- "It's not just X, it's Y", "not only... but also" used for emphasis
- Habitual triplets: three adjectives, three parallel clauses, three examples
  where one would do
- 「首先……其次……最后……」 scaffolding around points that are not sequential
- Fix: make the one claim you mean; keep a list of three only if there are
  exactly three things.

### Inflated or empty words
- 「赋能」「打造」「助力」「革命性」「颠覆」「至关重要」「强大的」「无缝」
  「全方位」「深度」 used as an intensifier, 「一站式」
- "crucial", "pivotal", "robust", "seamless", "powerful", "game-changer",
  "unlock", "leverage" as a verb for "use", "landscape", "realm", "tapestry"
- Fix: replace with the measurable property, or delete.

### Translationese in Chinese (English syntax in Chinese)
- 「进行了一个……的操作」「对……进行……」「……的一个过程」
- 「通过……的方式」「基于……的考虑」「作为……的一部分」 where a verb would do
- 「当……的时候」「在……的情况下」 copied from "when" and "in the case of"
- Long pre-nominal modifiers copied from English relative clauses
- Excess 「我们」, passive 「被」, and 「一个」 before every noun
- Fix: use the verb directly: 「对数据进行排序」→「排序数据」.

### Translationese in English (Chinese syntax in English)
- "carry out", "conduct", "perform", "realize" + noun for a plain verb:
  "realize the optimization" → "optimize"; 「实现」 is usually "implement"
- "relevant", "related", "corresponding" as filler for 「相关」「对应」
- Sentence-initial "So,", "As we all know,", "As is known to all,"
- Topic-comment order: "This method, its advantage is…"
- Lists ended with "and so on" or "etc." where the list is complete
- Stacked "very", "greatly", "effectively", "obviously"
- Four-character idioms rendered word for word, and "make/let sb. do" chains
- Missing or misused articles and plurals; "the" before every noun
- Fix: write the sentence an English engineer would write; keep the content,
  not the Chinese word order.

### Layout tics
- Bullets for content that is an argument
- Bold scattered through sentences; more than one bold phrase per paragraph
- A heading every one or two paragraphs
- Em dashes or 「——」 as the default way to attach a clause
- Emoji, or colons introducing every paragraph
- Fix: write the paragraph; let headings mark real topic changes.

### Shape
- Mirrored structure: every section the same length with the same internal
  pattern
- Rhetorical questions answered in the next sentence
- Metaphors the reader must decode (「就像一把钥匙」「如同交响乐」)
- Balanced pros-and-cons framing where the evidence is one-sided
- Fix: let structure follow content; replace a metaphor with the mechanism.

## Pattern scan

The literal part of the catalog as ripgrep patterns, one per language. Run
the matching one with the grep tool against each version after each draft.
Hits inside code blocks and math are not findings; every other hit is either
fixed or kept for a stated reason.

Chinese version:

```
在当今|随着.{0,12}(快速|迅速|飞速)发展|近年来|总之|综上所述|总而言之|总的来说|值得注意的是|需要指出的是|可以说[，,]|不难发现|众所周知|让我们|接下来我们|下面我们将|本文将|不仅.{0,20}更|与其说|赋能|打造|助力|革命性|颠覆|至关重要|无缝|全方位|一站式|进行了?一个|对.{1,12}进行|的一个过程|通过.{0,10}的方式|基于.{0,10}的考虑|作为.{1,12}的一部分|在.{1,12}的情况下
```

English version:

```
[Ii]n today's|ever-evolving|landscape|[Ii]t's worth noting|[Ll]et's dive|[Dd]elve|[Ii]n conclusion|[Tt]o sum up|[Cc]rucial|[Pp]ivotal|[Rr]obust|[Ss]eamless|[Gg]ame-changer|[Uu]nlock|[Tt]apestry|[Rr]ealm|(carry|carries|carried) out|\b(conduct|perform|realize)[sd]?\b|^So,|[Aa]s we all know|[Aa]s is known to all|and so on|\betc\.|\bvery\b|\bgreatly\b|\bobviously\b
```

## Exemplars

Articles the user has accepted as the target voice. Read the listed ones
before drafting a new post; the reviewer compares tone against them.

- (none yet)
