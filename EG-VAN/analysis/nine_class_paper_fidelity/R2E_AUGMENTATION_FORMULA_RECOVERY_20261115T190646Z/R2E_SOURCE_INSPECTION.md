# R2E Source Inspection

## Source identity and scope

Original PDF: `E:\Cancerdetection\EG-VAN_A_Global_and_Local_Attention-Based_Dual-Branch_Ensemble_Network_With_Advanced_Color_Balancing_for_Multi-Class_Skin_Cancer_Recognition.pdf`

SHA-256 was recalculated before source inspection and matched the expected value:

`bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`

The investigation was limited to Section B, its preceding crop-function context, the source page/stream, embedded font mappings, and the relevant prior R2C/R2D text. No patient images, masks, weights, predictions, or datasets were inspected.

## Page and object locator

- Section: `B. DATA AUGMENTATION`
- Printed page: 72857
- PDF viewer page: 6 (one-based)
- Zero-based PDF page index: 5
- Page object: 47
- Page content stream: 122 (`FlateDecode`)
- Equation number: (15)
- Page object 47 resource dictionary: fonts T1_0, T1_1, T1_2, T1_3, T1_4, T1_5, T1_6, T1_7, T1_8, T1_9; XObjects Fm0 and Fm1.

The browser produced a low-resolution full-page preview; its unrelated figure area was not inspected. A high-resolution full-page visual inspection was not achieved. Visual review was restricted to text/equation crops, and the text-only formula/context crop was legible enough to verify the equation layout and equation number. Text operators and font resources were used to recover the exact glyph sequence and subscripts/superscripts.

## Extraction and glyph-verification method

The original PDF bytes were read without modification. Node.js built-in `zlib` decompressed object 122. The equation and inline notation were reconstructed from PDF text-show operators, the page resource font references, the embedded `ToUnicode` CMaps, and the font `Encoding` Differences array:

- T1_8 is font object 101 (BLEX); its encoding is object 515 and its ToUnicode map is object 140. Encoding Differences map character code 80 (`P`) to `/summationtext` and code 88 (`X`) to `/summationdisplay`. Thus the source glyphs are summation signs, not literal P or X.
- T1_5 is font object 9 (MTSYN), with ToUnicode map object 34; source code `D` (0x44) maps to `=`.
- T1_6 is font object 102 (Times italic), with ToUnicode map object 156; it supplies italic variable glyphs including `x`, `y`, `f`, `i`, `j`, and `T`.
- T1_7 is font object 103 (RMTMI), with ToUnicode map object 513; its source glyph codes for the parentheses map to `(` and `)`.
- T1_4 is font object 10 (Times Roman), with ToUnicode map object 37; it supplies the printed digits and ordinary text glyphs used in the notation.

The BLEX ToUnicode map does not assign a Unicode character to codes 80 and 88; those identities were recovered from the font encoding's glyph names and cross-checked against the visual equation crop. No unreadable glyph was promoted to a symbol based on appearance alone.

## Source wording around the formulas

The Section B text states that augmentation uses random transformations, discusses the HAM-10000 dataset, and then introduces a dataset of input-output pairs. The source wording includes the grammatical form “Let’s assuming”. It identifies \(x_i\) as the input data and \(y_i\) as the associated label, then describes an augmentation function applied to \(x_i\).

After equation (15), the paper explains that the sum operator covers 20 different transformations, \(T_j(x_i)\), with \(j\) ranging from 1 to 20; each \(T_j\) is a specific transformation applied to \(x_i\), and the sum indicates that the transformations are combined by addition. It then says the resulting \(f(x_i)\) is new input data with changes to the original, produced by putting random modifications in a particular order.

## Scope and limitations

The Section B context explicitly names HAM-10000. It does not explicitly identify the displayed formula as the later Section G set of 13 techniques, the conclusion's 20 alternative methods, or Table 2's augmented counts.

The crop function on the same printed page occurs before the `B. DATA AUGMENTATION` heading, under the preceding data-preprocessing discussion, and is numbered equation (14). Its placement and description support treating it as preprocessing on this page; the paper does not explicitly say whether it is also a member of the 20 symbolic transformations.

No transformation identities, parameter values, probabilities, selection rule, retention rule, or reproducible application order are supplied by the recovered formula. This stage does not investigate the 1,965-image discrepancy.
