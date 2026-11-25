# A02 Researcher Disposition — Validation Report

**Validation date:** 2026-11-23  
**Scope:** Verify the separate disposition draft for `FANCONIC_LOCAL_UNVERIFIED_VERSION`. This report records a researcher disposition only; it is not legal clearance, dataset approval, or training authorization.

## Result

**PASS — the draft covers all 845 Fanconic records, its stated reasons agree with the inspected A02 evidence, and the original evidence package and approval state remain unchanged.**

## Decision-draft validation

The separate `A02_RESEARCHER_DECISION_COMPLETED_DRAFT.md` records:

- Disposition `EXCLUDE_FROM_APPROVED_COHORT_PENDING_EVIDENCE`.
- Scope of all 845 Fanconic records.
- Zero verified upstream byte-level matches and 845 possible Kaggle version-4 path/size matches, explicitly not treated as proof of origin.
- Kaggle `licenseName=Unknown`.
- Unverified original clinical label provenance and unavailable original patient/lesion identifiers.
- 127 unadjudicated external perceptual candidate pairs involving 51 files.
- A01's declared intended use as academic research only, with an explicit statement that this does not establish licensing, copyright clearance, publication or redistribution rights, or permission to train.
- Reconsideration requirements for authoritative provenance, rights, label evidence, and required identity review.
- An explicit limitation that the disposition is not a legal determination that the images are unusable.

The A02 crosswalk contains **845 unique local image paths**, and the label/identity provenance file contains 845 corresponding rows. These establish the exact scope referenced by the draft; no source label or record was changed.

## Original A02 evidence-package integrity

The seven A02 evidence-package files that existed before this task remain unchanged:

- The six files listed in `A02_OUTPUT_SHA256.csv` recompute to the recorded SHA-256 values and sizes.
- The original `A02_OUTPUT_SHA256.csv` itself remains SHA-256 `7f7a9fee63153003fdd961ebbe3478c32ff64caa5cbdfc2d8ffc8e361637f04c`.
- The original blank `A02_RESEARCHER_DECISION_TEMPLATE.md` remains byte-identical: SHA-256 `4f4678b9beba562c18bc9b0e102ceefad5453ae1a054ae6034cb3677fe40f393`.

The existing A02 files were not edited. The decision draft, this validation report, and `A02_DECISION_SHA256.csv` are separate additions.

## Other decision and approval checks

- **A01:** The completed academic-intended-use draft remains unchanged; SHA-256 `1aaac0480dda3ac19bd7dee8dd9463a4cb57e48ef9132df486ebcb68cd969fea`.
- **Researcher decision tracker:** The file remains unchanged; SHA-256 `47ca0a2afa141b961a1faeff1c6ad808e66e0c183208c2268849079dd87d9366`. Its three Fanconic entries remain `PENDING_RESEARCHER_REVIEW`; this separate draft does not update the tracker.
- **Approval checklist:** Remains `NOT_APPROVED`, with `approved_eligible_images=0` and `approved_four_way_split=false`; SHA-256 `e9597aae3d03e3b1d549da474fc7befaa82ec2d7bf3872d0123d4a44359977be`.
- The checklist has no `training_authorized` field. Training authorization remains **not granted**: the checklist is not approved, the four-way split is false, and no training authorization was added.

## Protected data and model integrity

The existing protected-file manifest was independently compared against the workspace after the draft was created:

- Manifest entries checked: **38,906**
- Bytes hashed: **9,856,101,469**
- Missing files: **0**
- Changed files: **0**

The protected set includes the project data/model artifacts covered by that manifest. The frozen split, Stage4 source manifest, preprocessing configuration, existing checkpoints, and all 845 Fanconic image hashes also match their recorded values. No image, metadata, label, source manifest, split, checkpoint, or model file was modified.

No training, evaluation, inference, or external publication was performed or authorized.

## Validation note

One preliminary validation attempt reported a tracker-hash mismatch because its expected-value string was mistyped. The independently captured pre-edit tracker hash was rechecked and matches the current file exactly (`47ca0a2afa141b961a1faeff1c6ad808e66e0c183208c2268849079dd87d9366`). The mismatch was in the validation script's expected value, not in the tracker or project files.

## Final status

`A02_DISPOSITION_DRAFT_VALIDATED_NOT_APPROVED`

The draft records exclusion from approved-cohort consideration pending evidence. It does not declare the images legally unusable, resolve any outstanding evidence, approve the dataset, authorize training, or make a subsequent researcher decision.
