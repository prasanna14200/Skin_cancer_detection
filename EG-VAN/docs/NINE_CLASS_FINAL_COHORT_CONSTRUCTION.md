# Modified nine-class cohort construction: bounded Stage 2 evidence

Date: 2026-10-24. **Status: cohort construction in progress; no clinical training approval.** This work extends the [100-image SIIM–ISIC 2020 pilot](NINE_CLASS_SIIM2020_PILOT.md) without changing its frozen manifest, images, hashes, attribution or decisions. It does not assert an exact EG-VAN paper reproduction. The nine output indices remain `AKIEC=0, BCC=1, BKL=2, DF=3, MEL=4, NV=5, VASC=6, BENIGN=7, MALIGNANT=8`.

## Acquired evidence and conservative quarantine

The original pilot had 16 candidate-bearing images with 116 unreviewed relations. They remain quarantined. The remaining 84 were rechecked by native/90°/180°/270°/horizontal-flip/center-80%-crop pHash (distance ≤10) against the existing HAM10000 and **canonical** Fanconic fingerprints. The top three candidates per source received the existing ORB/SIFT–RANSAC check. The [recheck ledger](../analysis/nine_class_final_cohort/pilot84_transformed_candidates.csv) contains **673 further candidates**, affecting **48** of 84 images; 36 had no retrieved candidate. No pair in this recheck had coherent geometry. The wider pHash rule catches transformed images that the earlier joint pHash/dHash rule could miss, but it also retrieves generic low-texture skin. No independent sensitivity or false-positive estimate exists. All 48 are quarantined for review. The 36 are screen-level no-candidate images, **not independently established photographs or approved cases**.

The [version-1 candidate plan](../analysis/nine_class_final_cohort/candidate_manifest_v1.csv) preserved the 100 pilot IDs and proposed additional distinct-patient, officially benign (`target=0`) records. The first 100-image incremental tranche was limited to selection ranks 101–200. One selected record, `ISIC_3746471`, had Challenge metadata lesion ID `0` while its [official Archive record](https://api.isic-archive.com/api/v2/images/ISIC_3746471/) gave `IL_0983669`; patient IDs matched. No image was downloaded for this unresolved record. The [source discrepancy evidence](../analysis/nine_class_final_cohort/source_identifier_conflict_evidence_v1.json) and original plan are preserved. The [version-2 plan](../analysis/nine_class_final_cohort/candidate_manifest_v2.csv) replaced it deterministically with `ISIC_7854457`, retained 1,200 distinct recorded patients, and did not alter either source label or lesion ID. Selection uses SHA-256 rank of `siim2020-final-v1:42:<image_id>`, skips both ends of official duplicate-list pairs, and selects at most one image per patient. `0` is excluded as a missing/sentinel lesion ID in the corrected plan. The v2 plan and its [selection record](../analysis/nine_class_final_cohort/candidate_selection_record_v2.json) are frozen by hash. **The remaining 1,000 planned images have not been downloaded or screened.**

The 99 unconflicted tranche images and one replacement were acquired from each [official ISIC Archive API record](https://api.isic-archive.com/api/docs/swagger/) and its `files.full` URL. All 100 new files decoded, were SHA-256 recorded, and matched the current S3 object ETag as local MD5. The new tranche totals 79,089,230 bytes and has 57 image-level `CC-BY` and 43 `CC-BY-NC` records. Across the original pilot plus tranche, **200 images** are acquired from **200 distinct recorded patient IDs**, with 114 `CC-BY` and 86 `CC-BY-NC` image-level records. The [combined attribution ledger](../analysis/nine_class_final_cohort/acquired_source_attribution_v1.csv) retains image IDs, local and official paths, image-level rights, attribution, and downloaded SHA-256. The [official Challenge release](https://challenge.isic-archive.com/data/#2020) has aggregate CC BY-NC 4.0 terms and requires the SIIM–ISIC 2020 dataset citation; the [ISIC FAQ](https://www.isic-archive.com/blank-1) also requires image-specific rights and attribution. Do not redistribute or use commercially outside the applicable terms. Current Archive objects have not been proven byte-identical to the fixed Challenge JPEG ZIP.

## 200-image photographic screen

The [acquired relation ledger](../analysis/nine_class_final_cohort/acquired_overlap_evidence_v1.csv) reuses the first pilot's 116 candidates and the 84-image transformed recheck, then screens the new 100 against 10,015 HAM and 3,297 canonical Fanconic images. It also compares all 200 acquired SIIM cases with one another. SHA-256, image-level pHash/dHash, transformed-image retrieval and bounded geometric evidence are recorded separately. Patient and lesion IDs remain source metadata, **not** image identity judgments. The full [screen summary](../analysis/nine_class_final_cohort/acquired_screen_summary_v1.json) reports:

| Evidence | Result |
| --- | ---: |
| Exact SHA-256 cross-source or within-SIIM matches | 0 |
| Cross-source perceptual candidate relations | 3,147 (2,456 HAM; 691 Fanconic) |
| Within-SIIM perceptual candidate relations | 121 |
| All candidate relations | 3,268 |
| Coherent geometric relations, **automated probable only** | 4, all within SIIM |
| Other uncertain relations | 3,264 |
| Acquired images with any candidate relation, quarantined | 121 |
| Acquired images with no candidate under the rule | 79 |
| Human-reviewed / approved images | 0 / 0 |

The four coherent within-SIIM pairs are `ISIC_1412350`–`ISIC_3463384`, `ISIC_1163624`–`ISIC_2840727`, `ISIC_2846882`–`ISIC_8159474`, and `ISIC_2523776`–`ISIC_8159474`. Their recorded patient IDs differ. Coherent local geometry supports a possible photographic relationship; it does not independently prove same photo, same lesion or metadata error. These pairs need priority inspection at original resolution. The [gallery](../analysis/nine_class_final_cohort/acquired_review_gallery_v1.html) shows up to three closest relations per image with links to originals; the CSV retains **every** relation. No automated status is called a human decision.

The [version-2 decision manifest](../analysis/nine_class_final_cohort/candidate_decision_manifest_v2.csv) explicitly marks **121 acquired images as quarantine**, **79 as preliminary no-candidate and unapproved**, and **1,000 as not acquired or screened**. The [quarantine manifest](../analysis/nine_class_final_cohort/exclusion_quarantine_manifest_v2.csv) excludes these records from planning assignments without deleting image files. No-candidate results cannot prove patient independence, especially because Fanconic patient identifiers and cross-source identity bridges are unavailable. Unlisted duplicates, crops, color/illumination changes and different views of the same lesion can escape the screen. The pHash threshold is not calibrated with independently verified nonmatches; its large generic-skin queue should be triaged before acquiring many more images.

## Scientifically useful target and four-way preview

For a *proposed* BENIGN cohort, the minimum design target is **400 independently eligible patient groups**, allowing approximately **280 train / 40 validation / 40 calibration / 40 protected test** groups. Forty per held-out partition provides a modest class-specific sample; it is not a statistical guarantee of precision or model accuracy. The present automated no-candidate rate is 79/200 = **39.5%**, which would imply about 1,013 candidates to yield 400 if that rate held. The frozen **1,200-record planning cap** adds a margin for further exclusions and group conflicts; this is a planning estimate, not a claim that 1,200 records will yield 400 eligible cases. Continue only in at-most-100-image acquisition tranches after triaging the current evidence. No additional full-source download is proposed.

The [four-way planning inventory](../analysis/nine_class_final_cohort/four_way_planning_inventory_v1.csv) uses only screen-level no-candidate SIIM cases, Stage 4 HAM records not already quarantined by protected Fanconic test links, and provisional Fanconic MALIGNANT records. It omits all Fanconic BENIGN, candidate-bearing SIIM images, and earlier proposed exclusions. The [four-way assignment preview](../analysis/nine_class_final_cohort/four_way_planning_assignment_v1.csv) is deterministic by seed 42 and groups existing HAM/Fanconic overlap components, HAM lesion IDs, SIIM patient IDs, and known exact/photo candidate relations by quarantining the latter. Publisher-source `test` records remain in `test`. Its separate [train](../analysis/nine_class_final_cohort/four_way_train_PLANNING_ONLY_v1.csv), [validation](../analysis/nine_class_final_cohort/four_way_validation_PLANNING_ONLY_v1.csv), [calibration](../analysis/nine_class_final_cohort/four_way_calibration_PLANNING_ONLY_v1.csv), and [test](../analysis/nine_class_final_cohort/four_way_test_PLANNING_ONLY_v1.csv) CSVs are **planning artifacts, not executable approved splits**. Every row has `approval_status=NOT_APPROVED`; they do not use the Stage 6 `split`/`APPROVED_ELIGIBLE` contract. The [feasibility report](../analysis/nine_class_final_cohort/four_way_feasibility_report_v1.json) found zero known group crossings and zero protected source-test boundary violations within the preview. This cannot establish unknown cross-source patient independence.

| Class | Train | Validation | Calibration | Test |
| --- | ---: | ---: | ---: | ---: |
| AKIEC | 223 | 42 | 30 | 32 |
| BCC | 371 | 49 | 44 | 50 |
| BKL | 754 | 108 | 122 | 115 |
| DF | 86 | 9 | 10 | 10 |
| MEL | 629 | 84 | 85 | 85 |
| NV | 4,347 | 629 | 627 | 627 |
| VASC | 103 | 15 | 13 | 11 |
| BENIGN (SIIM source-defined) | 55 | 8 | 8 | 8 |
| MALIGNANT (Fanconic provisional) | 512 | 84 | 84 | 165 |

These are **candidate preview counts, not eligible class counts**. All nine labels appear numerically in each partition, but **zero are independently approved**, the BENIGN held-out counts are far below the proposed 40, and rare HAM classes (especially DF/VASC) would have imprecise class estimates. The 165 MALIGNANT publisher-test images are unadjudicated and forced to the preview test; Fanconic source version, image-level rights, binary-label derivation and patient IDs remain unresolved. A four-way trainable cohort has therefore **not** been constructed.

An opt-in [four-way T4 config](../config/nine_class_training_t4_four_way_v2.json) and versioned `four_way_v1` split gate now allow a separate calibration partition **only** when a genuine approval record declares that partition frozen and separate from model selection. The gate retains source-inventory/split hashes, image-byte checks, original labels, known overlap/patient/lesion grouping, and publisher test isolation. The original three-way approval path remains unchanged and still rejects calibration rows. The dataset loader applies deterministic evaluation preprocessing to calibration; the evaluation command can save calibration logits for future temperature fitting. The new path was checked with synthetic fixtures, including cross-partition and publisher-test rejection. **Neither production protocol accepts the planning preview:** its rows are unapproved and intentionally lack the approved split schema.

## Explicit approval checklist

All items are currently **OPEN**, as recorded in the [approval checklist](../analysis/nine_class_final_cohort/approval_checklist_v1.json):

1. **Source and label policy:** researcher records that SIIM 2020 `benign,target=0` is a source-defined alternative `BENIGN` output, not a clinical synonym for all benign HAM diagnoses or a verified Fanconic label. Retain original labels and nine-class indices.
2. **Rights and provenance:** verify permitted noncommercial use, aggregate citation, each selected image-level license/attribution, fixed release versus Archive object qualification, and Fanconic MALIGNANT source/version/rights before including that class.
3. **Identity review:** independently inspect the four priority within-SIIM geometric pairs and the candidate-bearing images, using original resolution; record SAME_PHOTO, SAME_LESION, DISTINCT, or UNCERTAIN with reviewer ID, date and evidence. No automated no-match or geometry failure is an approval.
4. **Screening rule:** establish an independently checked sample of hard negatives and transformed positives to bound the pHash/geometric retrieval behavior. Resolve or quarantine all high-risk cross-source and within-source relations before partitioning. Merge confirmed same-photo/lesion groups; exclude unresolved relations from protected evaluation.
5. **Eligible numbers:** acquire later at-most-100-image tranches only as needed, verify identifiers and hashes, and demonstrate at least the declared BENIGN patient-group counts in each partition plus defensible counts for all eight other outputs. Do not silently use the quarantined Fanconic BENIGN publisher test.
6. **Versioned four-way production gate:** software is implemented and synthetically tested. Supply a real, independently approved four-way inventory/split and approval record with `split_protocol=four_way_v1`, `calibration_partition_frozen=true`, and `calibration_separate_from_model_selection=true`. Freeze a distinct calibration set; never fit temperature on validation or test by accident.
7. **Approval record:** a named researcher signs an actual eligible source inventory, four-way split, rights and adjudication references, protected-test policy, preprocessing hash and file hashes. Run the production validator on that exact approved version before enabling clinical training.

## Conditional Colab procedure

The measured T4 setup remains [microbatch 8 × accumulation 4, FP16, Adamax, frozen BatchNorm running statistics](NINE_CLASS_FINAL_TRAINING_READINESS.md). It is a computational starting configuration; no clinical outcome is implied. After every checklist item is substantiated, upload the approved inventory/split/approval files and this versioned config to Drive. Run the CUDA/torchvision preflight, verify hashes, and run the four-way `--validate-only` gate before a bounded approved-data smoke or full run. Save `last.pt`/`best.pt` to Drive; resume only with identical configuration and cohort hashes. Use validation for checkpoint selection, calibration only for temperature fitting, and the protected test once for final evaluation. The current planning files must **never** be supplied as approved inputs. These commands intentionally depend on genuine approved files that do not yet exist:

```bash
cd /content/drive/MyDrive/EG-VAN
export PYTHONPATH=src
CONFIG=config/nine_class_training_t4_four_way_v2.json
INVENTORY=/absolute/path/to/approved_source_inventory.csv
APPROVED_SPLIT=/absolute/path/to/approved_four_way_split.csv
APPROVAL=/absolute/path/to/genuine_four_way_approval.json
RUNS_ROOT=/content/drive/MyDrive/EG-VAN/analysis/nine_class_stage6/runs
python src/nine_class_training.py --root "$PWD" --config "$CONFIG" --inventory "$INVENTORY" --approved-split "$APPROVED_SPLIT" --approval "$APPROVAL" --runs-root "$RUNS_ROOT" --validate-only
python src/nine_class_training.py --root "$PWD" --config "$CONFIG" --inventory "$INVENTORY" --approved-split "$APPROVED_SPLIT" --approval "$APPROVAL" --runs-root "$RUNS_ROOT"
python src/nine_class_evaluation.py --root "$PWD" --inventory "$INVENTORY" --approved-split "$APPROVED_SPLIT" --approval "$APPROVAL" --checkpoint "$RUNS_ROOT/ACTUAL_RUN_DIR/best.pt" --split calibration --batch-size 8 --output-dir "$RUNS_ROOT/ACTUAL_RUN_DIR/calibration_predictions"
```

The full training and calibration commands above are **conditional instructions, not authorization to execute now**. A short approved-data training smoke would require a separate versioned one-epoch config and must not reuse the full-run checkpoint. Final test evaluation additionally requires `--split test --final-test` after model selection and calibration are frozen.

On a fresh copy of the source inputs and before the versioned output files exist, reproduce the completed evidence from the repository root with:

```powershell
python src/nine_class_final_cohort.py rescreen-pilot84
python src/nine_class_final_cohort.py plan-acquisition
python src/nine_class_final_cohort.py revise-plan
python src/nine_class_final_cohort.py acquire-interval --rank-start 101 --rank-end 199
python src/nine_class_final_cohort.py acquire-interval --rank-start 200 --rank-end 200
python src/nine_class_final_cohort.py screen-acquired
python src/nine_class_final_cohort.py write-decisions
python src/nine_class_final_cohort.py plan-four-way
python -m pytest tests/test_nine_class_final_cohort.py tests/test_nine_class_siim2020_pilot.py -q
```

The first three commands refuse to overwrite frozen selection versions. `acquire-interval` accepts at most 100 new records and checks official per-image identifiers and rights before download; completed matching images are reused. The source-conflict exception and its v1 plan are retained. The final screening and planning commands create evidence only. No model training, final split approval, clinical-label edit, architecture change, commit or push occurred.

Focused synthetic and artifact tests for the pilot/cohort planning, existing Stage 6, Stage 8 and opt-in four-way protocol returned **28 passed** locally. The local Windows torchvision installation emitted its pre-existing optional image-extension warning; no GPU or clinical training test was run in this turn.
