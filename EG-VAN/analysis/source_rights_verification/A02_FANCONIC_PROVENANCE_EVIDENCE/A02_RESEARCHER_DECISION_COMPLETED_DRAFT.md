# A02 Fanconic Researcher Disposition — Completed Draft

**Status:** Separate draft recording the researcher-supplied disposition. This does not change the existing decision tracker, eligibility matrix, approval checklist, or any dataset record.

## Researcher disposition

- **Disposition:** `EXCLUDE_FROM_APPROVED_COHORT_PENDING_EVIDENCE`
- **Scope:** All **845** records identified as `FANCONIC_LOCAL_UNVERIFIED_VERSION` in the existing exploratory split and listed individually in `A02_UPSTREAM_IDENTITY_CROSSWALK.csv`.
- **Decision:** Exclude all 845 Fanconic records from approved-cohort consideration until their provenance, rights, and original label evidence are resolved.
- **Researcher identity / signature:** Not supplied in the instructions for this draft.
- **Decision date:** Not supplied in the instructions for this draft.

## Evidence basis

The disposition is based on the A02 evidence package:

1. **Upstream byte-level identity:** **0 verified** upstream byte matches. All 845 records have possible Kaggle version 4 path-and-size matches, but path/name and size do not prove origin, acquisition authenticity, or byte identity.
2. **License:** Kaggle reports `licenseName=Unknown`. No per-image contributor-license or attribution mapping is established.
3. **Original labels:** The local label is `malignant`, but original clinical label provenance and diagnostic criteria are unverified.
4. **Patient and lesion identity:** Original patient and lesion identifiers are unavailable for all 845 records.
5. **Overlap evidence:** 127 external perceptual candidate pairs involving 51 of the files remain unadjudicated. These are candidates, not confirmed duplicate findings.

The file-level evidence, limitations, and references are in `A02_FANCONIC_PROVENANCE_REPORT.md`, `A02_LOCAL_FILE_HASH_INVENTORY.csv`, `A02_UPSTREAM_IDENTITY_CROSSWALK.csv`, `A02_LABEL_AND_IDENTITY_PROVENANCE.csv`, and `A02_EVIDENCE_REFERENCE_REGISTER.csv`.

## Intended-use boundary

A01 records the researcher's declared intended use as **academic research only**. That declaration does not establish licensing, copyright clearance, publication rights, redistribution rights, or permission to train. It does not resolve any Fanconic source or image rights.

## Reconsideration requirements

Reconsideration of these records for approved-cohort consideration requires, at minimum:

- Authoritative upstream provenance, exact version, and acquisition evidence.
- Reliable file-level identity evidence linking local files to an authoritative package or records.
- Applicable dataset and per-image rights evidence, including attribution requirements.
- Authoritative original label source, definitions, and per-image label provenance.
- Required independent identity review of relevant duplicate and perceptual candidates, with no identity inferred from filenames or automated similarity alone.

Until those requirements are resolved and reviewed through the project's formal process, retain the exclusion. This is a conservative research-data eligibility disposition; **it is not a legal determination that the images are unusable**.

## Limits of this disposition

This draft does not mark the Fanconic source or any record approved. It does not modify source labels, images, metadata, identity decisions, manifests, or partitions. It does not authorize training, evaluation, inference, or external publication, and it does not decide any other researcher decision.
