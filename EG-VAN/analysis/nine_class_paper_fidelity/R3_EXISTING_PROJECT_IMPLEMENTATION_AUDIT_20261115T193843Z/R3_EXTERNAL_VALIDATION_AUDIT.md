# R3 External Validation Audit

## Nine-class implementation and saved runs

`src/nine_class_external_protocol.py` implements a source/version/rights/mapping manifest, hash checks, internal/external overlap candidate screening, and explicit researcher approval gates. `src/nine_class_external_evaluation.py` requires an approved internal split, frozen checkpoint, matching preprocessing/provenance hashes, an approved external manifest and a completed overlap review. It reports either full-nine-class metrics or explicitly subset-conditioned metrics; no class is silently remapped.

The Stage 9 manifest template contains headers only. `analysis/nine_class_stage9/synthetic_verification_summary.json` records software verification only, with no approved external manifest, no trained nine-class checkpoint used and `external_clinical_validation_performed=false`. No nine-class external predictions or metrics were found. The Stage 9 statement that no external cohort was downloaded is scoped to this gated nine-class workflow; it does not mean the separate PH2 package is absent.

## PH2 package present, but not nine-class validation

The local PH2 manifest has 200 source-labelled images: 80 common nevus, 80 atypical nevus and 40 melanoma. The legacy `src/external_eval.py` maps common nevus to seven-class `nv`, melanoma to `mel`, and explicitly excludes atypical nevus; its nominal included subset is 120 images. It is a seven-class checkpoint follow-up protocol, not a nine-class EG-VAN evaluation. No PH2 predictions or metrics for the nine-class checkpoint exist.

The PH2 metadata records a secondary Kaggle version-2 package and a narrow use-scoped determination for non-commercial research/education with citation required and redistribution/commercial use prohibited. The exact byte-level linkage to the secondary mirror is not independently established, and the Kaggle `Other` field is not a license grant. The frozen Stage23 documentation says PH2 was previously used for an earlier classifier, so it is not an untouched external confirmation cohort.

## Historical seven-class registry is not an external result

`models/frozen_stage23/model_registry.json` contains validation-only values for a historical seven-class EG-VAN+ checkpoint: accuracy 0.8296146, macro-F1 0.6712538, balanced accuracy 0.6574260, on 986 HAM validation cases (selected epoch 14). The registry and freeze manifest reference `experiments/stage23_resnet50_imagenet_init_exp1/run/best_checkpoint.pt` and its metrics/predictions, but those referenced files are absent from this checkout. The registry values are therefore recorded as historical claims, not independently verifiable current artifacts, and are not nine-class or external-validation results.

## Status

- Nine-class external-validation software: **implemented, synthetic-tested per saved reports**.
- Eligible independent nine-class cohort: **none established**.
- PH2: **present and metadata-audited for narrow research use; legacy two-label subset only**.
- Nine-class external inference/predictions/metrics/domain-shift analysis: **not executed**.
- Clinical external validation: **none**.

No external image contents were opened or evaluated during this audit.
