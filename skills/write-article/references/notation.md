# Notation

The house standard for math, symbols, and quantities in every article. It
targets GPU, CUDA, and LLM systems writing, with general ML notation where
those topics need it. It lists choices where several conventions exist; for
anything not listed, use the standard convention of the field. The Chinese
and English versions of an article use identical symbols, units, and number
formats; only the rules marked for Chinese differ.

## Precedence

1. The user's explicit convention, then the series' `Symbols` table in
   `series.md`.
2. The convention of the domain being discussed: GEMM shapes as in CUTLASS, a
   paper's notation when the article walks through that paper.
3. This file.

When the article departs from this file, record the symbol in `series.md` so
later posts reuse it. When a source's notation conflicts with the series,
translate it into the series notation and say so once.

## Rendering target

Determine the renderer before writing math, and record it with its source in
`series.md` under `Rendering target`:

- **Hugo:** the site configuration (`hugo.toml`, `config.*`, or
  `config/_default/`), especially the goldmark passthrough delimiters, and the
  layout partial that loads KaTeX or MathJax, including any macros it defines.
- **LaTeX:** the preamble's packages and macros.
- **Slides:** the tool and its math support.

If it cannot be determined, ask the user; until then use the Markdown + KaTeX
rules below, restricted to commands KaTeX documents as supported.

### Markdown + KaTeX

- Inline math in `$...$`, display math in `$$...$$` on its own lines. No bare
  LaTeX in prose, and no `\(...\)` or `\[...\]` unless the site configures them.
- Environments such as `aligned`, `cases`, or `bmatrix` go inside `$$...$$`;
  use only environments the renderer supports.
- Do not number equations or use `\label`/`\eqref` unless the renderer is
  confirmed to support them. Refer to an equation by what it computes instead.
- Headings hold at most a short inline expression.
- Escape a literal dollar sign in prose when the renderer would read it as a
  delimiter.

## Equations in prose

- Inline math is short and reads as part of the sentence: `$x$`, `$O(S^2 d)$`.
  Fractions, sums, chained relations, matrices, and anything with nested
  indices go to display math. A trivial expression is not displayed.
- Introduce each display with a sentence that says what it is, and follow an
  important one with what it means or implies.
- Define every new symbol at or right after the equation that introduces it,
  with its shape or unit when that matters.
- A derivation puts one logical step per line, aligned on the relation symbol,
  and explains any non-obvious step in prose. Split a long derivation into
  separate displays at each conceptual phase.
- Chinese version only: put a space between Chinese text and inline math. Do
  not put punctuation inside display math; continue the sentence in prose
  after the display. The English version punctuates displays as part of the
  sentence.
- Code identifiers stay in code formatting (`threadIdx.x`, `num_heads`). When
  a quantity appears both as a code name and a math symbol, map them once:
  "head dimension $d_h$ (`head_dim`)".

## Symbol choice and reuse

- Within one section or derivation, one base letter names one concept family.
  `\boldsymbol{W}` for a weight matrix and `W` for a window size is a conflict;
  `\boldsymbol{x}` and its component `x_j` are not.
- Reuse across typefaces only when the relation is direct and standard, such as
  a random variable `X` and its realization `x`.
- When a conventional symbol is taken, pick a nearby distinct one or add a
  semantic subscript; never redefine a symbol silently.
- Prefer symbols that suggest their role. Do not use code-like identifiers in
  math: `\boldsymbol{h}_{\text{class}}`, not `h_class`.

## Typeface and decorations

| Object | Form | Example |
| --- | --- | --- |
| Scalar | italic lowercase | `x`, `\alpha`, `\eta` |
| Vector | bold lowercase via `\boldsymbol` | `\boldsymbol{x} \in \mathbb{R}^{d}` |
| Matrix, tensor | bold uppercase via `\boldsymbol` | `\boldsymbol{W} \in \mathbb{R}^{d \times d_{\text{ff}}}` |
| Set, collection | calligraphic | `\mathcal{D}`, `\mathcal{X}` |
| Number system | blackboard bold | `\mathbb{R}`, `\mathbb{N}` |
| Named operator | `\operatorname` | `\operatorname{softmax}`, `\operatorname{diag}` |
| Size, count | italic uppercase | `S`, `M`, `N`, `K` |

- Use `\boldsymbol` only; do not mix it with `\mathbf`, `\bm`, or `\vec`.
- Hat for an estimate (`\hat{y}`), bar for a mean (`\bar{x}`), star for an
  optimum (`\boldsymbol{\theta}^*`).
- Subscripts carry position, component, step, or a semantic label in `\text{}`:
  `\boldsymbol{h}_t`, `x_j`, `\boldsymbol{\theta}_k`, `\mathcal{L}_{\text{train}}`.
- Parenthesized superscripts carry sample and layer labels:
  `\boldsymbol{x}^{(i)}`, `\boldsymbol{W}^{(\ell)}`. Plain superscripts are
  powers and structural operators: `x^2`, `^\top`, `^{-1}`, `^\dagger`.
- When both appear, write the subscript first: `\boldsymbol{h}_t^{(\ell)}`.
- Use `\ell`, never `l`, for a layer index.

## Orientation

- A single vector is a column vector.
- Sequences and batches stack items as rows: one token per row. This matches
  the usual attention formulas and row-major code.

$$
\boldsymbol{X} \in \mathbb{R}^{S \times d}, \quad
\boldsymbol{Q} = \boldsymbol{X}\boldsymbol{W}_Q, \quad
\operatorname{Attention}(\boldsymbol{Q}, \boldsymbol{K}, \boldsymbol{V})
= \operatorname{softmax}\!\left(\frac{\boldsymbol{Q}\boldsymbol{K}^\top}{\sqrt{d_h}}\right)\boldsymbol{V}
$$

- Row `t` of `\boldsymbol{X}` is the token representation `\boldsymbol{x}_t^\top`.
  State the orientation once per article where the first such matrix appears.
- Juxtaposition is matrix multiplication; `\odot` is elementwise; `\otimes`
  only for Kronecker or tensor products.
- Norms `\lVert \cdot \rVert`, absolute value `\lvert \cdot \rvert`; do not mix
  them with plain `|` and `\|`.

## Default symbols

### Model

| Symbol | Meaning |
| --- | --- |
| `B` | batch size |
| `S` | sequence length; `S_q`, `S_{kv}` when query and key lengths differ |
| `d` | model (hidden) dimension |
| `d_h` | head dimension |
| `d_{\text{ff}}` | feed-forward intermediate dimension |
| `H_q`, `H_{kv}` | number of query heads, key/value heads |
| `L` | number of layers; `\ell` is the layer index |
| `N_{\text{vocab}}` | vocabulary size (`V` is the value matrix) |
| `E`, `k` | number of experts, experts routed per token |
| `\boldsymbol{W}_Q`, `\boldsymbol{W}_K`, `\boldsymbol{W}_V`, `\boldsymbol{W}_O` | attention projections |
| `\boldsymbol{\theta}` | all trainable parameters |
| `\mathcal{L}` | loss |
| `\tau` | temperature |
| `t`, `s` | query position, key position |
| `i` | sample index |

### Kernels and GEMM

| Symbol | Meaning |
| --- | --- |
| `M`, `N`, `K` | GEMM problem shape: `\boldsymbol{A} \in \mathbb{R}^{M \times K}`, `\boldsymbol{B} \in \mathbb{R}^{K \times N}` |
| `\boldsymbol{D} = \boldsymbol{A}\boldsymbol{B} + \boldsymbol{C}` | GEMM with accumulator input `\boldsymbol{C}` and output `\boldsymbol{D}` |
| `M_{\text{tile}}`, `N_{\text{tile}}`, `K_{\text{tile}}` | tile shape of one CTA |
| `F` | work in FLOPs (`W` and `Q` are taken by weights and queries) |
| `T` | memory traffic in bytes |
| `I = F / T` | arithmetic intensity in FLOP/byte |
| `\pi`, `\beta` | peak compute in FLOP/s, peak bandwidth in B/s |

- In a GEMM section, `\boldsymbol{A}`, `\boldsymbol{B}`, `\boldsymbol{C}`,
  `\boldsymbol{D}` are the GEMM operands, so the batch size there is
  `N_{\text{batch}}`, not `B`. `M`, `N`, `K` are reserved for GEMM shapes;
  outside GEMM, a sample count is `n`.
- When the article maps model shapes to GEMM, state the mapping explicitly:
  "the QKV projection is a GEMM with `M = BS`, `N = (H_q + 2H_{kv}) d_h`,
  `K = d`".
- Thread, warp, and block indices stay as code (`threadIdx.x`, `blockIdx.y`);
  they do not become math symbols.

## Probability

- `\mathbb{P}(A)` for an event, `p(\cdot)` for a mass or density function,
  `\mathbb{E}[\cdot]`, `\operatorname{Var}`, `\operatorname{Cov}` upright.
- Condition with `\mid`, never a plain `|`: `p(y \mid \boldsymbol{x}; \boldsymbol{\theta})`.
- Distinguish distributions by subscript: `p_{\text{data}}`, `p_{\boldsymbol{\theta}}`.
- Write a likelihood through the model, `p(\mathcal{D}; \boldsymbol{\theta})`;
  `\mathcal{L}` stays the loss.
- `X \sim \mathcal{N}(\mu, \sigma^2)`; random variables uppercase italic,
  realizations lowercase.

## Quantities and units

- A space between a number and its unit: `80 GiB`, `3.35 TB/s`.
- `B` is a byte, `b` a bit. State dtype sizes in bytes: bf16 is 2 bytes.
- Memory sizes computed in the article use binary units (KiB, MiB, GiB).
  Bandwidth uses decimal units (GB/s, TB/s). Quote vendor figures in the
  vendor's units and do not compare across unit systems without converting.
- FLOPs is a count, FLOP/s a rate (TFLOP/s, PFLOP/s). Never write "FLOPS".
- Parameter counts: `8.03B` in prose, the exact `8,030,261,248` in tables,
  `8.03 \times 10^9` inside math. Use one style per context.
- Keep significant digits consistent with the precision of the inputs, and
  name the hardware, dtype, and shape behind every measured number.
