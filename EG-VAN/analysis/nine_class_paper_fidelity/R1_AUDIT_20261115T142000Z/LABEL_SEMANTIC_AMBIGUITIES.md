# Label Semantic Ambiguities

## 1. What the paper supports

Section IV-A (printed p. 72862) describes an aggregate nine-class task made from seven HAM10000 diagnoses and a separate two-class skin-cancer dataset described as benign and malignant. Section IV-D (printed p. 72864) discusses the seven HAM abbreviations and the BENIGN and MALIGNANT outputs. This supports the paper's high-level output construction.

The local Stage 4 implementation preserves the HAM `dx` string as its diagnosis class and preserves the local binary folder labels as two additional output names. It marks the binary source `FANCONIC_LOCAL_UNVERIFIED_VERSION`; the binary image, lesion, and patient identifiers are blank. This is a local, source-conditioned encoding, not evidence that the paper used that exact package or that its folder labels have verified clinical derivation.

## 2. ISIC 2017 source-name conflict

The existing project transcription of Table 2 assigns the two binary rows to “ISIC 2017.” The primary paper's searchable Section IV-A instead describes a two-class collection and cites references [45] and [54]; the Table 2 body is not text-extractable in this audit. The transcription therefore does not independently establish the paper's source column.

The official ISIC 2017 Task 3 page describes two separate binary tasks over three diagnoses: melanoma versus nevus/seborrheic keratosis, and seborrheic keratosis versus melanoma/nevus. It lists 2,000 training images (374 melanoma, 254 seborrheic keratosis, 1,372 nevi). The official data page lists 2,000 train, 150 validation, and 600 test images. Those official task labels are not a single generic BENIGN-versus-MALIGNANT label pair, and the complete official release total does not equal the 3,297 binary images in the project transcription.

Accordingly:

- The claim that EG-VAN's binary source was the complete official ISIC 2017 Task 3 release with its official labels is contradicted by the official release description and counts.
- The claim that Table 2 says “ISIC 2017” is present in the project transcription but is not independently verified from the primary table.
- The exact EG-VAN binary package, subset, version, original image IDs, and label derivation remain unresolved. It could not be substituted with Fanconic, official ISIC Task 3, or another source without author/source evidence.

No undocumented mapping from ISIC task labels to generic BENIGN/MALIGNANT was created.

## 3. Broad labels are not mutually exclusive diagnosis synonyms

The paper presents BENIGN and MALIGNANT as separate output classes alongside the seven HAM diagnoses. It does not provide a rule for reconciling broad binary labels with clinically overlapping diagnoses. For example, this audit does not move a HAM diagnosis into BENIGN or MALIGNANT, and does not infer a class from a diagnosis's perceived medical meaning.

Treating a source-conditioned label as a separate model target does not prove that the nine labels are mutually exclusive clinical concepts. It may also create source-identification shortcuts if the two added classes come from a different image collection. The paper does not document a control for this issue in the inspected methods.

## 4. Table 2 and augmentation accounting

The local CSV transcription reports 13,312 original images, including 3,297 binary-source images, and reports class-wise train/test and augmented counts. Its augmented column sums to 34,554 according to the existing project evidence snapshot, while the paper text reports 37,883 training and 6,686 validation images including augmentation. The project completion plan records this accounting as unreconciled.

Because Table 2's cells were not available in searchable text and were not visually inspected for this audit, the transcribed counts and source column remain secondary evidence. No reconciliation or correction is inferred here.

## 5. Split, overlap, and identity

Section IV-C (printed p. 72863) gives aggregate split and augmentation counts. The searchable paper text did not disclose an image-level manifest, random seed, duplicate policy, patient/lesion grouping rule, or cross-source overlap method. A text-layer search did not find the terms duplicate, overlap, patient ID, lesion ID, or random seed. This is a statement about the inspected paper text, not proof that no additional author-side record exists.

The paper's reported counts cannot reconstruct which images were in each partition or whether related records crossed partitions. The project Stage 4 gate remains blocked and no approved split is present; this audit does not change that status.

## 6. Required resolution for stronger claims

To establish exact paper-source fidelity, obtain an author-confirmed binary-source name and version, an original image-ID/checksum manifest, original label definitions and derivation, Table 2 source/cell clarification, split membership and augmentation lineage, and the duplicate/patient/lesion grouping policy. Until then, retain source labels, describe the nine outputs as source-conditioned, and do not claim exact reproduction or clinical exclusivity.
