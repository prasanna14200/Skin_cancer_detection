# A06 — Approval-Gate Audit

**Generated:** 2026-11-23  
**Current checklist:** `NOT_APPROVED`; approved eligible images = **0**; `approved_four_way_split=false`  
**Actual-image training authorization:** **NO**

## Audit scope

Inspected the A05 central launcher `src/nine_class_authorized_training.py`, its synthetic test suite, the legacy Stage 6 entry point `src/nine_class_training.py`, its approved-split validator, the current approval checklist, and the A05 readiness report. No production training code or approval evidence was changed. A06 added synthetic-only tests in `tests/test_nine_class_authorized_training.py`.

## Central A05 launcher checks

| Authorization condition | Code-level result | Synthetic test evidence |
|---|---|---|
| Checklist must be approved and all checklist gates resolved | Fail-closed: accepts only approved statuses and rejects unresolved checklist items | `test_not_approved_checklist_fails_first` |
| Approved eligible image count must be positive and match partition records | Fail-closed on zero/invalid count and count mismatch | `test_zero_approved_count_and_unapproved_split_are_rejected` |
| Four-way split must be approved | Fail-closed when false | `test_zero_approved_count_and_unapproved_split_are_rejected` |
| Approved source IDs must be present and each source must have established rights/identity, zero pending decisions, and evidence | Fail-closed for empty source list or unresolved source row | `test_empty_source_and_partition_authorization_is_rejected`; `test_pending_decisions_or_unresolved_source_block` |
| Approved record IDs must be present in train, validation, calibration, and test | Each partition list is required and nonempty | `test_each_approved_partition_requires_record_ids` |
| All configured required decisions must exist, be resolved, and include outcomes/evidence | Fail-closed on pending configuration or unresolved required decision | `test_pending_decisions_or_unresolved_source_block`; `test_decision_register_must_resolve_every_required_item` |
| Training, validation, calibration, and test records/identities must not overlap | Fail-closed on partition-ID or identity overlap | `test_test_or_calibration_record_cannot_be_added_to_training`; `test_cross_partition_identity_overlap_is_rejected` |
| Calibration/test entries cannot enter the training list | Record-ID partition intersection is rejected | `test_test_or_calibration_record_cannot_be_added_to_training` |
| Split records must match approved inventory/source and be marked approved eligible | Fail-closed on unapproved rows or inventory mismatch | `test_unapproved_record_or_inventory_mismatch_is_rejected` |
| Approval record must bind current configuration, checklist, split, inventory, source and decision-register hashes | Fail-closed on stale evidence hash | `test_approval_record_must_bind_current_authorization_inputs` |

The focused command was run in `project_showcase\.venv\Scripts\python.exe`:

```text
python -m unittest discover -s tests -p test_nine_class_authorized_training.py
Ran 12 tests ... OK
```

The first attempt used a different Python interpreter without NumPy and failed during import. It was not counted as a test pass; rerunning in the project environment passed all 12 synthetic-only tests. No package was installed and no actual dataset image or metadata was opened by the tests.

## Direct Stage 6 entry-point gap

`src/nine_class_training.py` can be invoked directly, outside the A05 launcher. Its own validator checks the approved split, researcher approval JSON, input hashes, source inventory, image bytes, class mapping, and split leakage. It does **not** consult the central A05 checklist, source-eligibility register, or researcher decision register.

The A06 test `test_direct_stage6_validate_only_does_not_consult_central_decision_gates` builds only temporary synthetic byte files and synthetic CSV/JSON fixtures, then calls the legacy entry point with `--validate-only`. It returns success without any central checklist/source/decision-register inputs. The test stops before model construction or image decoding; it validates configuration and may construct a transform object, but applies no transformation to any image. This demonstrates a code-path bypass, not valid approval and not actual training.

**Risk:** future execution could bypass the central policy layer by calling Stage 6 directly with a self-constructed approval record. Hash matching binds supplied files to one another; it does not establish that the researcher, rights evidence, source eligibility, or decisions are authentic. The bypass is documented, not repaired in A06, because the task limited code changes to explicitly justified safety tests. Do not treat the direct runner as an authorized entry point.

**Required engineering follow-up before any future training:** enforce the central authorization contract inside the Stage 6 training path or make the launch path require a verifiable authorization artifact that cannot be substituted by a manually created approval JSON. Add a regression test that direct training refuses without this authority. Do not weaken existing checks.

## Current state and stop conditions

- The real checklist still reads `NOT_APPROVED`, with zero approved images and no approved four-way split.
- All 11 tracker decisions, 12 HAM decisions, and 7 checklist items remain open; the proposed Fanconic exclusion remains an exclusion assumption, not approval.
- The A05 proposed config has empty approved source and record ID lists and 23 pending decision IDs.
- The exploratory split is not an approved split. No actual-image training, inference, evaluation, preprocessing, augmentation, or A04/A05 execution occurred in A06.
- The central A05 launcher’s positive path was tested only with a synthetic authorization fixture. That passing fixture is not research approval.

**Verdict:** central launcher gates fail closed under the tested synthetic cases, but a separate direct Stage 6 entry point bypasses those central source/decision checks. Current actual-image training remains **NOT AUTHORIZED**. Researcher decisions, external rights/provenance evidence, a new approved cohort, and a technical fix to the direct entry point are required before training.
