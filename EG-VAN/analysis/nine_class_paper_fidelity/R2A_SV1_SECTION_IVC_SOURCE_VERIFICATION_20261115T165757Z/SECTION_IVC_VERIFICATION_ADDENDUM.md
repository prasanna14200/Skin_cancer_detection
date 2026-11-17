# R2A-SV1 Section IV-C Source Verification Addendum

## Conclusion

- `SECTION_IVC_SOURCE_STATUS = VERIFIED`
- `TABLE2_SECTION_IVC_RECONCILIATION = UNRESOLVED`
- `OVERALL_R2A_STATUS = PARTIALLY_VERIFIED`

This addendum verifies the Section IV-C count statements against the original paper PDF. It does not resolve the numerical relationship between Section IV-C and Table 2.

## Source identity and locator

- Paper: *EG-VAN: A Global and Local Attention-Based Dual-Branch Ensemble Network With Advanced Color Balancing for Multi-Class Skin Cancer Recognition*
- DOI: `10.1109/ACCESS.2025.3561240`
- Original PDF: `E:\Cancerdetection\EG-VAN_A_Global_and_Local_Attention-Based_Dual-Branch_Ensemble_Network_With_Advanced_Color_Balancing_for_Multi-Class_Skin_Cancer_Recognition.pdf`
- SHA-256: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`
- Section heading: `C. IMPLEMENTATION DETAIL`
- Printed page: 72863
- PDF viewer page: 12 (one-based)
- Zero-based PDF page index: 11
- Page object: 475
- Text stream object: 509
- Stream filter: `FlateDecode`
- Page tree: Catalog object 754 points to Pages root object 48; recursive page-tree traversal places page object 475 at position 12 of 23 pages.
- The footer text in the page content stream is `72863`.

The locator and both source quotations are independently reproduced in `SOURCE_LOCATOR_DETAILS.csv`.

## Source wording

The following are verbatim text recovered from the original PDF's decompressed text content stream. Text fragments from PDF text-show operators were joined in reading order; this is not a visual transcription of the rendered page.

> “The training dataset contained 37,883 images that consisted of original and augmentation images.”

> “Similarly, the validation dataset contained 6,686 images that also consisted of original and augmentation images.”

## Directly observed surrounding context

The same text stream states:

> “We first divided the HAM-10000 dataset into training and testing. The testing dataset consisted of 1332 original images. To avoid the overfitting problem, we applied data augmentation technique on training dataset to improve the all the classes in the 9-class dataset. After that, we further divided the training dataset into training and validation.”

This context is verbatim as recovered from the PDF text operators. No additional inference about the relationship between the reported counts and Table 2 is made.

## Method and limitations

The original PDF bytes were inspected read-only. The PDF object for page 475 identifies content stream 509 and its `FlateDecode` filter. Node.js with its built-in `zlib` decompressed that content stream; the two count sentences and the page footer were present in the decoded text. The PDF page tree was traversed to establish the viewer-page mapping.

The full PDF page was not visually inspected. No patient image, dataset, model weight, review queue, or prediction was accessed. The printed `00` in Table 2 and the Table 2-to-Section IV-C count reconciliation remain unresolved.

## Preservation

All existing R1, R2, and R2A artifacts were treated as read-only. This addendum is a separate, timestamped output; no existing audit file, source transcription, dataset, notebook, or Git metadata was changed.
