# R2F Validation

## Source and input-package checks

- Original PDF SHA-256: `bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3` — matched expected.
- R1, R2, R2A, R2A-SV1, R2B, R2C, R2D and R2E manifests: all listed entries verified against SHA-256; each manifest was present.
- Manifest-file SHA-256 values at synthesis:
  - R1 `420d5aff50c787c3cbc9707fdc8dedf8676c61c27aad1950d760f5db34085276`
  - R2 `61541501198a0a02a4db6c48a6f0db564bfb1a10d24b6e9c3012682124829f51`
  - R2A `bd5c2378de4643200956d376c32c30e7c702bb566c4e1e5cf75cf51536d82ca0`
  - R2A-SV1 `cc174372e809b9892d08119e3e9414602b395a26bd2ea3fa14c71ac1127f45e7`
  - R2B `da864f93f581a70f8af82673c255010184b3642c2dcfa8411bc9c9d09fb48ef8`
  - R2C `1d993335e3b8b36b717a360ded4602ec6b1c0fd025a44646b56c1c2e391e71ae`
  - R2D `7f9729c6998a8bb10ff9c49351aada0958119febf85a3d00259c2582fedfae92`
  - R2E `5ce9d323de2369b35767e35c2a64a647e9b377e5acdfa076b4d45804323ac69b`
- All substantive files in the prior packages were read for this synthesis. Package contents were treated as evidence only at their verified scope; no package status was upgraded merely through repetition.

## Evidence/content checks

- Required domains are represented in `R2F_MASTER_FIDELITY_MATRIX.csv`; every row contains a source locator or an explicit statement that no locator was established, an evidence package/file, a permitted verification status, a confidence value, an implementation-proceed value and a next action.
- R2E's equation, seven verified symbol/index roles, partial N, and zero individually identified transformations are retained.
- Table 2 NV remains literal `00`. Conditional totals and 1,965 difference remain conditional/unresolved.
- R2D's visual limitation for the exact Section G sentence is retained separately from its text-stream evidence.
- Project implementation assertions are not treated as independently verified code or dataset readiness.
- The cross-audit report addresses all seven required consistency checks; unresolved questions and implementation assumptions are explicitly listed.
- No unsupported claim of faithful reproduction, clinical readiness, or measured project accuracy is made.

## Deliverable and structural checks

- Expected files: seven substantive deliverables plus `R2F_MANIFEST.sha256`.
- Both CSV files parse with consistent field counts; required master/decision columns are present.
- Every evidence path in the CSVs resolves to an existing prior audit file, and every source locator identifies a paper section/page/object/stream where available; unreviewed claims are explicitly marked as lacking a locator.
- All eight R2F files are nonempty.
- R2F manifest hashes exactly the seven substantive deliverables; all hashes verify.
- Original PDF and prior package manifest hashes were rechecked after R2F creation; previous packages remain unchanged.

## Scope limits

R2F is a read-only consolidation. No source code, data files, patient images, masks, model weights, predictions, training, inference, evaluation, or Git commands were used. A checksum match verifies file identity, not scientific validity or reproducibility.
