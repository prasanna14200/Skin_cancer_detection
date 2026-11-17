# R2B Source Evidence Inventory

## Scope and source identity

This is a read-only investigation of the original paper's count definitions and processing chronology. No dataset, patient image, mask, model weight, prediction, source code, notebook, or Git state was accessed or changed.

- Paper: *EG-VAN: A Global and Local Attention-Based Dual-Branch Ensemble Network With Advanced Color Balancing for Multi-Class Skin Cancer Recognition*, IEEE Access 13 (2025), pp. 72852-72874, DOI `10.1109/ACCESS.2025.3561240`.
- Original PDF: `E:\Cancerdetection\EG-VAN_A_Global_and_Local_Attention-Based_Dual-Branch_Ensemble_Network_With_Advanced_Color_Balancing_for_Multi-Class_Skin_Cancer_Recognition.pdf`
- SHA-256: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`
- PDF: 23 viewer pages.
- Table 2: printed p. 72863, viewer p. 12, zero-based index 11; vector Form XObject 510. R2 previously isolated and visually inspected this table object; its transcription is `../R2_SOURCE_VERIFICATION_20261115T163331Z/TABLE2_SOURCE_TRANSCRIPTION.csv`.

## Direct paper evidence

Text below was recovered from the original PDF's decompressed text streams. Quotes preserve wording; PDF line-break hyphenation was joined where needed. No claim is made that the entire rendered page was visually inspected.

### Section IV-A: dataset composition

- Printed p. 72862; viewer p. 11; page content stream object 719.
- The paper describes a second source as “two classes: malignant and benign, containing over 3,200 images.”
- It states: “By combining the HAM10000 dataset with the 2-class skin cancer dataset, we created a 9-class dataset.”
- It states: “The complete details of the number of images in each class are provided in Table 2.”
- The text gives lower-bound descriptions (“over 10,000” HAM10000 images and “over 3,200” images in the second source), not exact totals or a versioned per-image manifest.

### Section IV-C: split and reported totals

- Heading: `C. IMPLEMENTATION DETAIL`; printed p. 72863; viewer p. 12; zero-based index 11; page object 475; content stream object 509 (`FlateDecode`).
- Verbatim process wording:
  > “We first divided the HAM-10000 dataset into training and testing. The testing dataset consisted of 1332 original images.”
  >
  > “To avoid the overfitting problem, we applied data augmentation technique on training dataset to improve the all the classes in the 9-class dataset. After that, we further divided the training dataset into training and validation.”
- Verbatim reported totals:
  > “The training dataset contained 37,883 images that consisted of original and augmentation images.”
  >
  > “Similarly, the validation dataset contained 6,686 images that also consisted of original and augmentation images.”
- The page footer is `72863`; page-tree traversal maps page object 475 to viewer page 12. The quoted text is from the decompressed stream, not a visual transcription of the full page.

### Augmentation and preprocessing statements elsewhere

- Printed p. 72857; viewer p. 6; stream object 122; subsection `B. DATA AUGMENTATION`: “Data augmentation is a technique that creates new data from existing data by applying random transformations.” It also says multiple techniques were employed on HAM-10000 because its classes had different image counts. A mathematical explanation refers to 20 transformations; this is not a definition of Table 2's count column.
- Printed p. 72869; viewer p. 18; stream object 182; Section G: “Finally, we employed thirteen data augmentation techniques on the 9-class dataset.”
- Printed p. 72872; viewer p. 21; stream object 534: the paper says it “additionally applied a hair-removing algorithm, color balancing method, and twenty alternative data augmentation methods.”
- The paper therefore gives different augmentation-technique counts (13 and 20) in different passages. The passages do not state whether they count different subsets/stages, and neither explains the Table 2 / Section IV-C image totals.
- Printed p. 72856; viewer p. 5; stream object 112: the paper says it performed a hair-removal process on the HAM10000 dataset before describing illumination/color preprocessing. This is image processing; no record-count reduction is stated.

## Table 2 source values

The R2 visual source transcription records the nine printed rows below. The table headings are `Original Images`, `Testing Images`, `Train images`, and `Augmented Images`. R2 reports no total row or visible explanatory footnote. The printed NV augmented cell is the literal `00`; it is not normalized here.

| Class | Original | Testing | Train | Augmented literal |
|---|---:|---:|---:|---:|
| AKIEC | 327 | 33 | 294 | 2206 |
| BCC | 514 | 51 | 463 | 2537 |
| BKL | 1099 | 110 | 989 | 7011 |
| DF | 115 | 12 | 103 | 1397 |
| MEL | 1113 | 111 | 1002 | 6998 |
| VASC | 142 | 14 | 128 | 1372 |
| NV | 6705 | 671 | 6034 | `00` |
| MALIGNANT | 1497 | 150 | 1347 | 6653 |
| BENIGN | 1800 | 180 | 1620 | 6380 |

The class-level equality `Original = Testing + Train` holds for all nine rows. That equality supports an original-image partition arithmetic; it does not define the augmented column.

## Method and limitations

The PDF SHA-256 was checked locally. Text evidence was inspected by parsing PDF objects and inflating `FlateDecode` streams with Node.js built-in `zlib`; the page tree was traversed to map page objects to viewer-page positions. Table 2 cell evidence relies on R2's isolated Form XObject visual verification. The full paper pages were not rendered for this investigation. Search results over searchable PDF text can miss content represented only as vector graphics; R2's table inspection found no table footnote.

Prior packages R1, R2, R2A, and R2A-SV1 were read-only. Their existing findings are background evidence, not substitutes for the paper: R1 leaves source lineage/split membership open; R2 records the literal NV `00`; R2A and R2A-SV1 retain the reconciliation as unresolved.
