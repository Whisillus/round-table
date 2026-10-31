---
name: process-pdf
description: Use when reading, searching, summarizing, or quoting PDF files; extracting their text, tables, figures, embedded images, or metadata; reading scanned PDFs with OCR; or splitting, merging, and rendering PDF pages. Covers poppler command-line tools, page rendering for visual inspection, and tesseract OCR.
metadata:
  workflow: pdf-processing
---

# Process PDF

Use this skill when a task involves the content or pages of a PDF file.
Follow the active agent's permissions and the user's authorized scope; loading this skill does not authorize file changes.

## Responsibility

- Read PDF content by page range and report findings with page numbers.
- Never modify, overwrite, or replace a source PDF.
- Write intermediate files only to a private temporary directory outside the workspace, and remove it when done. Write output PDFs or images to the workspace only when the user asks for them.
- An agent whose instructions forbid generating files uses only commands that print to standard output: `pdfinfo`, `pdfimages -list`, `pdftotext ... -`, and the OCR pipeline in step 6. When a task needs page images or new PDFs, report that it requires an agent that may write files.

## Preconditions

Check the tools before starting:

```bash
command -v pdfinfo pdftotext pdftoppm
```

If any is missing, stop and report that poppler is required (`brew install poppler` on macOS, `poppler-utils` on Debian or Ubuntu). Do not substitute Ghostscript `txtwrite`: it interleaves two-column pages line by line and drops word spaces. OCR additionally requires `tesseract`.

Under a sandbox, poppler may print `Fontconfig error: No writable cache directories`. The message is harmless; output is unaffected.

Start every pipeline below with `set -o pipefail`; otherwise a failed poppler command looks like empty output with exit code 0.

## Temporary Files

Each shell call may start a fresh shell, so a variable such as `$dir` does not survive between calls. Run `mktemp -d` once, note the absolute path it prints, and write that literal path in later commands. Remove it at the end with `rm -r -- /absolute/path/printed/by/mktemp`.

## Workflow

1. **Inspect.** For pages N to M:

   ```bash
   pdfinfo -f N -l M in.pdf
   set -o pipefail; pdftotext -f N -l M in.pdf - | awk -v first=N 'BEGIN { RS = "\f" } { t = $0; gsub(/[[:space:]]/, "", t); printf "page %d: %d chars\n", first + NR - 1, length(t) }'
   pdfimages -list -f N -l M in.pdf
   ```

   `pdfinfo` gives the page count and, with `-f`/`-l`, each page's size and rotation; without them it reports page 1 only. The character counts size the reads in step 2. In the image list, ignore `smask` rows and small icons. An image whose width ÷ `x-ppi` and height ÷ `y-ppi` match the page size in inches (points ÷ 72) covers the page: treat that page as scanned (step 6) even if it has a few lines of text, such as a stamp or header. A page with a large image that does not cover it holds a figure; render it (step 5) when the figure may matter.
2. **Read text.** Choose consecutive pages totalling about 20,000 characters or fewer, from the counts in step 1, and print them with page markers:

   ```bash
   set -o pipefail; pdftotext -f N -l M in.pdf - | awk -v first=N 'BEGIN { RS = "\f" } { printf "=== page %d ===\n%s\n", first + NR - 1, $0 }'
   ```

   The default mode follows reading order and separates columns correctly. If the tool reports truncated or omitted output, or the page markers do not run continuously from N to M, the missing pages were not read; read them again in smaller ranges. A page with no characters has no text layer; read it by OCR (step 6).
3. **Search.** Map matches to page numbers by counting form feeds:

   ```bash
   set -o pipefail; pdftotext in.pdf - | awk -v pat='register file' 'BEGIN { page = 1 } { page += gsub(/\f/, ""); if (index(tolower($0), pat)) print page ": " $0 }'
   ```

   `pat` is matched literally; write it in lower case. Matches stay within one line, so a phrase broken across lines or a word hyphenated at a line end does not match; search also for one distinctive word before concluding a term is absent. No output means absent only when the exit code is 0. Read the matching pages with step 2 before citing them.
4. **Tables.** The default mode emits a table column by column. Extract the table region with `-layout`, cropped to the table so neighbouring page columns do not interleave. At the default resolution (`-r 72`), crop coordinates are in points from the top-left corner; take the page size from step 1:

   ```bash
   pdftotext -layout -f 10 -l 10 -x 0 -y 60 -W 306 -H 180 in.pdf -
   ```

   Find the region from a rendered page (step 5) or by widening the crop until the caption appears.
5. **Figures, equations, and layout.** Render the page into the temporary directory and inspect it with the image-reading tool:

   ```bash
   pdftoppm -f 10 -l 10 -singlefile -r 150 -png in.pdf /tmp/path/from/mktemp/page10
   ```

   This writes `page10.png`; `-singlefile` keeps the name independent of page-number padding. For detail, render at `-r 300` with a crop; `-x -y -W -H` for `pdftoppm` are in pixels at the chosen resolution. Render whenever extracted text is garbled, equations matter, or a figure carries the answer. Charts drawn as vector graphics are visible only by rendering.
6. **Scanned pages.** Render at 300 dpi and pipe the image to OCR; no file is written:

   ```bash
   set -o pipefail; pdftoppm -f 10 -l 10 -singlefile -r 300 -png in.pdf | tesseract - - -l eng
   ```

   Lower resolutions misread digits. Choose `-l` from the script on the page, rendering it first (step 5) if the script is unknown. Check `tesseract --list-langs`; if the language is missing, stop and report it (for example `brew install tesseract-lang`) instead of running OCR with another language. Check numbers, symbols, and names against the rendered page when one is available.
7. **Embedded images.** Extract raster images listed in step 1 with `pdfimages -png -f N -l N in.pdf /tmp/path/from/mktemp/img`. Extract only the pages needed.
8. **Split and merge.** Write new files; never name a source PDF as the output.

   ```bash
   pdfseparate -f 2 -l 4 in.pdf /tmp/path/from/mktemp/page-%d.pdf
   pdfunite /tmp/path/from/mktemp/page-2.pdf /tmp/path/from/mktemp/page-3.pdf /tmp/path/from/mktemp/page-4.pdf /tmp/path/from/mktemp/pages-2-4.pdf
   ```

   `pdfunite` treats its last argument as the output and overwrites it without asking; omitting the output name overwrites the last input. `pdfseparate` also overwrites existing files. Confirm the output path does not exist before running either. Verify the result with `pdfinfo` for the page count.

## Encrypted Files

When any poppler command fails with `Incorrect password`, ask the user for the password. Pass a user password with `-upw` or an owner password with `-opw` to `pdfinfo`, `pdftotext`, `pdftoppm`, or `pdfimages`, and tell the user that the password appears in the command record. `pdfseparate` and `pdfunite` accept no password, so splitting or merging a password-protected PDF is out of scope. Never guess passwords or remove protection.

## Out Of Scope

- Creating PDFs from other documents.
- Editing PDF text, filling forms, signing, rotating pages, or changing encryption: these need tools this skill does not cover, such as `qpdf`. Report the need instead of improvising.

## Reporting

- Cite page numbers for every quoted or summarized claim.
- State which pages were read and how: text extraction, rendering, or OCR.
- Mark OCR-derived text as possibly inaccurate.
- Do not describe pages that were not read; when only part of a document was read, say which part.
