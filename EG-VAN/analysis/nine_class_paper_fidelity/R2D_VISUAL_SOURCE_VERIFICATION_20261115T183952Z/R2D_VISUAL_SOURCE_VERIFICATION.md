# R2D Visual Source Verification

## Scope and source identity

This is a read-only inspection of the original paper PDF and prior audit packages. The PDF SHA-256 was recalculated before inspection and matched the expected value:

`bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`

The PDF contains 23 pages. Viewer numbering is one-based; the zero-based index is viewer page minus one. The object/stream locators below are inherited from the verified R2/R2C page-tree and stream analysis. They were not independently rediscovered by visual rendering.

## Page inspection log

| Printed page | Viewer page | Index | Section/content | Visual result |
|---|---:|---:|---|---|
| 72856 | 5 | 4 | A. Data Preprocessing, color enhancement | Text-region view inspected. No claim that every sentence was transcribed visually. |
| 72857 | 6 | 5 | B. Data Augmentation, generic definition and symbolic transformation discussion | Text-region view inspected. Individual transformation names are not visibly enumerated in the available evidence. |
| 72863 | 12 | 11 | Table 2 and C. Implementation Detail | Table 2 crop visually inspected; NV augmented cell reads literally `00`. Section IV-C count sentences were previously checked by text-stream extraction, not independently visually transcribed here. |
| 72869 | 18 | 17 | G. Impact of Preprocessing Steps | Page and text column visually inspected. The exact “thirteen” sentence is not legible enough at the available view scale for independent visual transcription; its wording remains text-stream evidence. |
| 72872 | 21 | 20 | VI. Conclusion and Future Work | Conclusion text crop visually inspected; the “twenty alternative data augmentation methods” sentence is visible. |

The screenshots/crops used for visual review were transient tool outputs and are not included in this package; the required output set is exactly the nine named deliverables.

## Evidence locators and wording

### A. Section B: symbolic transformations

- Printed page 72857; viewer page 6; zero-based index 5.
- Page object 47; content stream object 122 (`FlateDecode`).
- Exact recoverable definition: “Data augmentation is a technique that creates new data from existing data by applying random transformations.”
- The surrounding text discusses augmentation on HAM-10000 and a formula involving 20 transformations, denoted \(T_j\), with \(j=1,\ldots,20\). Individual operation names, per-operation parameters, and probabilities are not established by this text.
- Visual inspection did not establish a list of named operations.

### B. Section G: thirteen techniques

- Printed page 72869; viewer page 18; zero-based index 17.
- Page object 181; content stream object 182 (`FlateDecode`).
- Text-stream wording: “Finally, we employed thirteen data augmentation techniques on the 9-class dataset. This augmentation process introduced subtle variations in the Dermoscopic images, making the model more robust to different perspectives and reducing the risk of overfitting. The integration of these techniques in the current study suggests that their combination was effective in addressing color and data imbalances and also enhancing the quality of the Dermoscopic images.”
- The number modifies “data augmentation techniques”; no individual techniques are named in this passage.
- The source wording is text-stream evidence. The exact sentence could not be visually confirmed at the available scale and is therefore not marked visually verified.

### C. Conclusion: twenty alternative methods

- Printed page 72872; viewer page 21; zero-based index 20.
- Page object 469; content stream object 534 (`FlateDecode`).
- Exact text-stream wording: “To enhance the discriminative features of data and expand the training dataset, we additionally applied a hair-removing algorithm, color balancing method, and twenty alternative data augmentation methods.”
- The number modifies “alternative data augmentation methods”; the sentence relates them to expanding the training dataset. It provides no itemized list or parameters.
- The conclusion text crop was visually inspected.

## Table 2 and Section IV-C

- Table 2 is on printed page 72863 / viewer page 12 / index 11. R2 identifies page object 475 and text stream 509; Table 2 itself is vector Form XObject 510.
- Visual comparison with the R2 transcription supports the printed NV `Augmented Images` cell as the literal `00`. It is not converted to numeric zero.
- No visual footnote or explanatory note was identified for the augmented-count column.
- Section IV-C reports 37,883 training images and 6,686 validation images, each described as consisting of original and augmentation images. Its text-stream locator is page object 475 / stream 509.
- Visual inspection did not produce new evidence defining the Table 2 count convention or bridging Table 2 to Section IV-C.

## Preservation and limits

Prior R1, R2, R2A, R2A-SV1, R2B, and R2C packages were read only. The R2C textual evidence was treated as a locator and transcription baseline, not a substitute for visual confirmation. No images, masks, model weights, predictions, datasets, or unrelated project files were accessed. No training, inference, evaluation, or Git operation was performed.

The p. 72869 sentence-level visual limitation is explicit. No operation list, augmentation-count definition, or explanation for the conditional 1,965-image difference is inferred from incomplete visual evidence.
