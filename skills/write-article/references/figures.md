# Figures

How to make, store, and check the figures of an article. Every figure this
workflow creates is generated from a source file, rendered to PNG, and looked
at before review.

## When a figure earns its place

Draw a figure when the point is a spatial, structural, or temporal relation
that prose states poorly: a memory layout, a tiling, a swizzle, a thread-to-data
mapping, a pipeline timeline, a data flow, a measured trend. Each figure makes
one point, its caption states that point, and the text refers to it. A figure
that repeats a sentence, or decorates a section, is cut.

## Tools

| Figure | Tool |
| --- | --- |
| Structure: layouts, tiles, swizzles, thread mappings, timelines, data flow | A stdlib Python script that writes SVG |
| Data: performance curves, rooflines, bar charts | matplotlib, saved as SVG |
| Checking any figure | `rsvg-convert` to PNG, then `read_image` |

Do not use Mermaid (`mmdc`), Plotly static export, or headless Chrome: they
launch a browser, which crashes under the agent sandbox.

## Sources and outputs

- Each figure this workflow creates or regenerates has one source in
  `.writing/<...>/<post>/figures/`: a script `<name>.py`, plus `<name>.csv`
  for a data figure. Write the source first; never hand-edit a generated SVG.
- Leave existing assets that have no source, such as screenshots and
  third-party figures, as they are unless the user asks to redraw them. Record
  where each came from in `brief.md`, with the credit or license for a
  third-party figure, and report it in review as a figure whose content cannot
  be verified from a source.
- The script takes the output path as its only argument and writes
  `<name>.svg` where the article's renderer expects assets: the page bundle
  next to a Hugo post's `index.md`, or the directory the series records.
- When the rendering target is LaTeX, also write `<name>.pdf` for
  `\includegraphics`, which `pdflatex` needs because it cannot include SVG:
  `rsvg-convert -f pdf -o <name>.pdf <name>.svg`. The SVG stays the generated
  output, and checking still uses PNG.
- Record each figure in `brief.md` under `## Figures`:
  `<name> — source (or origin, for an existing asset) — output — section that
  refers to it`.
- Run scripts with `python3 -B`, or with the virtual environment's `python -B`
  when matplotlib lives there, and set `MPLCONFIGDIR` to a private temporary
  directory for matplotlib; under the sandbox it cannot write `~/.matplotlib`.
  `Fontconfig error: No writable cache directories` is harmless.

## Structure figures

- Name the parameters at the top of the script with the article's symbols
  (`M_TILE = 128`, `D_H = 64`) and compute every coordinate from them. A figure
  whose numbers come from the same parameters as the text cannot drift from
  it; when a parameter changes, rerun the script.
- Set `viewBox`, `width`, and `height`; draw a white background rectangle
  first.
- Keep text as `<text>` elements with `font-family="Helvetica, Arial,
  sans-serif"`; never convert text to paths.
- Leave a margin around the drawing and estimate label widths (about 0.6 ×
  font size per character) before placing them; most overlaps come from
  labels placed at a guessed width.

## Data figures

```python
import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "svg.fonttype": "none",           # keep text as text
    "svg.hashsalt": "write-article",  # same input, same file
    "font.family": "sans-serif",
    "font.size": 11,
})
# ... plot from the CSV ...
fig.savefig(out, format="svg", metadata={"Date": None},
            bbox_inches="tight", facecolor="white")
```

- Read data only from the CSV next to the script; never type measured values
  into the script.
- Label both axes with quantity and unit, e.g. `Throughput (TFLOP/s)`. Use a
  log scale only when every value is positive and they span more than two
  orders of magnitude, and say so in the axis label. With zero or negative
  values, keep a linear axis, or use `symlog` and state its linear range in
  the caption.
- Name the hardware, dtype, and shape behind the data in the caption.

## Style

- **English only** inside every SVG: labels, legends, axis titles, and
  annotations. Both language versions of the article share one figure. Use
  symbols and code identifiers as they appear in the text.
- The caption and alt text belong to the article and are written in the
  version's language.
- **Color carries meaning.** The same color means the same thing in every
  figure of a series; record the mapping in `series.md` under `Figure palette`.
  Default to the Okabe–Ito palette, which stays distinguishable under color
  blindness: `#0072B2` `#E69F00` `#009E73` `#D55E00` `#CC79A7` `#56B4E9`
  `#F0E442` `#000000`. Use gray for context that carries no meaning.
- Yellow `#F0E442` and sky blue `#56B4E9` are too light for text or thin lines
  on white: use them only as fills, with a dark outline.
- Color is never the only distinction. Pair it with a direct label, a marker
  shape, or a line style, so the figure reads in grayscale.
- **White background**, set explicitly; a transparent figure turns black text
  invisible under a dark theme.
- Text at least 12 px at the width the page displays the figure.
- No gradients, shadows, 3D, icons, emoji, or decorative shapes. These are the
  figure's machine-sounding patterns.
- Annotate the one thing the reader should see, with an arrow or a label, and
  nothing else.

## Checking

Render every figure and look at it before review, and again after each
change. An existing asset in a raster format can be opened with `read_image`
directly.

```bash
rsvg-convert -w 1200 -o /absolute/tmp/dir/<name>.png <path/to/name>.svg
```

Then open the PNG with `read_image`. Check overlapping or clipped text, labels
pointing at the wrong element, legibility at display size, and that every
number and label matches the text. Keep the PNGs in the temporary directory
until the review ends, then remove it.
