# Extraction Attempt Log

This log records unsuccessful attempts as well as the method that ultimately verified the source. All activity was read-only.

1. **PDF command-line utilities:** Attempts to locate `pdftotext`, `pdfinfo`, `mutool`, `qpdf`, and Ghostscript commands returned no executable paths. These tools were unavailable through the command environment.
2. **Python PDF libraries:** Python was not available as a command (`python` was not recognized), so the attempted Python module probe did not run. No claim is made that any Python PDF library was installed or absent.
3. **Initial Node invocation:** Initial `node -e` invocations failed because PowerShell/native argument parsing stripped JavaScript quotes; Node reported `ReferenceError: Cannot access 'fs' before initialization` / `require(fs)`. These attempts did not verify source text.
4. **Node package probe:** `require.resolve` checks for common PDF packages produced no resolved module paths. No package was installed.
5. **Successful object inspection:** A later Node script was passed on standard input (`node -`) and read the original PDF directly. It located page object 475 and its `/Contents 509 0 R` reference.
6. **Successful stream extraction:** The dictionary for text stream object 509 declares `/Filter/FlateDecode`. Node's built-in `zlib.inflateSync` decompressed that stream. The decoded text contained the Section IV-C heading, the 37,883 and 6,686 sentences, surrounding wording, and the footer `72863`.
7. **Page mapping:** The PDF Catalog object 754 points to Pages root object 48. Recursive traversal of the page tree found 23 leaf pages and placed page object 475 at the 12th position (viewer page 12, zero-based index 11).

The PDF page was not visually rendered or inspected as a whole. The successful result is based on direct PDF object and text-stream inspection, not on the earlier R2A checkpoint or its paraphrase.
