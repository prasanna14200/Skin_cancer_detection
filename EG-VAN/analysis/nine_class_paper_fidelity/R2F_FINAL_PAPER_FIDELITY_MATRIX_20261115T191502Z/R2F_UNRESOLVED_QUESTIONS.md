# R2F Unresolved Questions

These are evidence gaps, not invitations to infer standard practices. Until resolved, no exact nine-class reproduction or eligible test set is established.

## Cohort, labels, rights and split

1. What exact version/package and per-image manifest supplied the two BENIGN/MALIGNANT classes?
2. How were its labels assigned, and are they mutually exclusive with the seven HAM-derived diagnoses?
3. What are the stable image, patient and lesion identifiers, source lineage, and license/permission terms for every record?
4. Does the current local cohort match the paper's nine-class image IDs and counts? R1 says the local binary source is version-unverified.
5. What are the train/test/validation image memberships and group-disjointness rules? Were patient/lesion groups kept together?
6. What duplicate and cross-source overlap checks were performed, and what records/groups were excluded?
7. Does Section IV-C's use of “HAM-10000 dataset” mean the combined nine-class cohort or only HAM10000?

## Table 2 and numerical reconciliation

8. What does each Table 2 `Augmented Images` cell count: generated items, distinct transformed files, retained images, or an inclusive target?
9. What is the intended NV augmented value printed as `00`?
10. Are augmented values training-only, and are originals included? Can a source image produce several retained descendants?
11. What per-class, per-source ledger maps Table 2 to the 37,883 training and 6,686 validation totals?
12. What documented operation, if any, explains the conditional 1,965 difference? Shared stage/cohort equivalence is not established.

## Augmentation and preprocessing

13. What are the identities and exact definitions of all \(T_j\), \(j=1,\ldots,20\), in Eq. (15)?
14. What does “combined by addition” mean operationally, and what is the actual transformation order/composition?
15. What probabilities, parameter ranges, randomization rules, selection rules, retention rules and partition placement apply?
16. What is \(N\)'s intended definition/value in the inline data notation?
17. How do the Section B 20 symbolic transformations relate, if at all, to Section G's 13 techniques and the conclusion's 20 alternative methods?
18. What are the precise hair-removal, color-balancing, Gray World/Retinex and crop/resize algorithms/settings?

## Model, training and evaluation

19. What exact branch topology, SCGA/non-local/MFF definitions, initialization and parameter count constitute the paper model?
20. What optimizer, loss, schedule, batch/accumulation, epochs, precision, random seeds and stopping/checkpoint rules produced the paper results?
21. What exact test cohort and metric protocol produced the reported 96.68% F1 and 98.20% accuracy? Are these claims based on an independent, group-disjoint test partition?
22. Was an external cohort or clinical validation performed? R1-R2E do not establish either.

## Minimum author/source request

Request one versioned evidence bundle from the paper authors/source maintainer: permitted source packages and record-level provenance; label derivation; stable image/patient/lesion IDs; exclusions and duplicate/overlap results; frozen split manifests; augmentation operation list, parameters and output-count ledger; Table 2 definitions including NV `00`; and a mapping from those records/stages to Section IV-C and the reported metrics. Without this bundle, a faithful data pipeline and defensible split cannot be approved. Any experiment using substitute operations or cohorts must be explicitly labeled as a deviation, not reproduction.
