# R4 External Validation Gap Analysis

## Current status
The project contains external-validation infrastructure, but no eligible independent nine-class external cohort is established.

## Existing implementation
- `EG-VAN/src/nine_class_external_protocol.py` implements a manifest-driven overlap screen and approval gate.
- A Stage 9 synthetic verification summary confirms that this stage is software verification only.

## What is missing
- No approved external manifest.
- No external dataset established as independent and nine-class compatible.
- No external predictions, metrics or domain-shift report tied to a frozen model checkpoint.

## Legacy caveat
PH2 and legacy subsets are not valid evidence for an untouched nine-class external evaluation. They do not satisfy the independence and label compatibility requirements for a defensible external validation claim.

## Decision
Do not claim external validation until a non-overlapping, rights-cleared, versioned external cohort is approved and frozen in a single manifest. Until then, external-validation attempts remain unverified and non-evidentiary.

`EXTERNAL_VALIDATION_STATUS = GATED_INFRASTRUCTURE_IMPLEMENTED__NO_ELIGIBLE_NINE_CLASS_EXTERNAL_RESULT`
