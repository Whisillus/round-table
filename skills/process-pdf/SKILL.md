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
- Write intermediate files only to a private directory created with `mktemp -d` outside the workspace, and remove it when done. Write output PDFs or images to the workspace only when the user asks for them.
- An agent whose instructions forbid generating files uses only the commands that print to standard output: `pdfinfo`, `pdffonts`, `pdfimages -list`, and `pdftotext ... -`. When a task needs page images, OCR, or new PDFs, report that it requires an agent that may write files.

## Preconditions

Check the tools before starting:

```bash
command -v pdfinfo pdftotext pdftoppm
```

If any is missing, stop and report that poppler is required (`brew install poppler` on macOS, `poppler-utils` on Debian or Ubuntu). Do not substitute Ghostscript `txtwrite`: it interleaves two-column pages line by line and drops word spaces. OCR additionally requires `tesseract`.

Under a sandbox, poppler may print `Fontconfig error: No writable cache directories`. The message is harmless; output is unaffected.

## Workflow

1. **Inspect.** Run `pdfinfo in.pdf` for page count, page size, and encryption. Run `pdffonts -l 3 in.pdf`; a document with no fonts listed has no text layer and is a scan (step 5).
2. **Read text.** Extract at most 10 pages per call:

   ```bash
   pdftotext -f 1 -l 10 in.pdf -
   ```

   The default mode follows reading order and separates columns correctly. Do not read a whole long document in one call; output beyond the tool's limit is truncated. Pages are separated by form feeds (`\f`).
3. **Search.** Map matches to page numbers by counting form feeds:

   ```bash
   pdftotext in.pdf - | awk -v pat='register file' 'BEGIN { page = 1 } { page += gsub(/\f/, ""); if (tolower($0) ~ pat) print page ": " $0 }'
   ```

   Write `pat` in lower case. Then read the matching pages with step 2 before citing them.
4. **Tables.** The default mode emits a table column by column. Extract the table region with `-layout`, cropped to the table so neighbouring page columns do not interleave. Crop coordinates are in points (1/72 inch) from the top-left corner; a US Letter page is 612 × 792 points:

   ```bash
   pdftotext -layout -f 10 -l 10 -x 0 -y 60 -W 306 -H 180 in.pdf -
   ```

   Find the region from a rendered page (step 5) or by widening the crop until the caption appears.
5. **Figures, equations, and layout.** Render the page and inspect it with the image-reading tool:

   ```bash
   dir=$(mktemp -d)
   pdftoppm -f 10 -l 10 -singlefile -r 150 -png in.pdf "$dir/page10"
   ```

   This writes `$dir/page10.png`; `-singlefile` keeps the name independent of page-number padding. For detail, render at `-r 300` with a crop; `-x -y -W -H` for `pdftoppm` are in pixels at the chosen resolution. Use rendering whenever extracted text is garbled, equations matter, or a figure carries the answer. Charts drawn as vector graphics are visible only by rendering.
6. **Scanned pages.** Render at `-r 300`, then run OCR:

   ```bash
   tesseract "$dir/page10.png" - -l eng
   ```

   Check the OCR text against the rendered image for numbers, symbols, and names. Install other language data before using `-l` with a language other than `eng`.
7. **Embedded images.** List raster images first with `pdfimages -list -f N -l N in.pdf`, then extract them with `pdfimages -png -f N -l N in.pdf "$dir/img"`. Small icons and `smask` entries are often numerous; extract only the pages needed.
8. **Split and merge.** Write new files; never name a source PDF as the output.

   ```bash
   pdfseparate -f 2 -l 4 in.pdf "$dir/page-%d.pdf"
   pdfunite "$dir/page-2.pdf" "$dir/page-3.pdf" "$dir/page-4.pdf" "$dir/pages-2-4.pdf"
   ```

   `pdfunite` treats its last argument as the output and overwrites it without asking; omitting the output name overwrites the last input. `pdfseparate` also overwrites existing files. Confirm the output path does not exist before running either. Verify the result with `pdfinfo` for the page count.

## Encrypted Files

When `pdfinfo` reports encryption and extraction fails, ask the user for the password and pass it with `-upw`. Never guess passwords or remove protection.

## Out Of Scope

- Creating PDFs from Office documents: use the `office-export-pdf` skill when it is available.
- Editing PDF text, filling forms, signing, rotating pages, or changing encryption: these need tools this skill does not cover, such as `qpdf`. Report the need instead of improvising.

## Reporting

- Cite page numbers for every quoted or summarized claim.
- State which pages were read and how: text extraction, rendering, or OCR.
- Mark OCR-derived text as possibly inaccurate.
- Do not describe pages that were not read; when only part of a document was read, say which part.
