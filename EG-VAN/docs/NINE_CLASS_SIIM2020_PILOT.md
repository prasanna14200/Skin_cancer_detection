# SIIM–ISIC 2020 bounded BENIGN image pilot

Date: 2026-10-24. **Pilot complete; no clinical cohort approved.** This tests a possible source-defined `BENIGN` pool for a **modified nine-class** EG-VAN study. It does not establish the original paper's binary source or authorize training, splitting, calibration, or protected testing. Stage 6 eligibility gates and the quarantined Fanconic BENIGN source-test records were not changed.

## Source and rights

The [official 2020 Challenge data page](https://challenge.isic-archive.com/data/#2020) publishes 33,126 training images, metadata v2 with patient and lesion IDs, a 425-pair duplicate list, and an aggregate **CC BY-NC 4.0** license. Its required dataset attribution is:

> International Skin Imaging Collaboration. SIIM-ISIC 2020 Challenge Dataset. International Skin Imaging Collaboration. https://doi.org/10.34970/2020-ds01 (2020).

The [official ISIC Archive API](https://api.isic-archive.com/api/docs/swagger/) provides an individual image's public record, full-image URL, license, and attribution; its [FAQ](https://www.isic-archive.com/blank-1) requires checking and attributing image-level rights. This pilot retrieved **only 100 full images** from the URLs in those official records. The 23 GB fixed 2020 Challenge JPEG ZIP was not acquired. The selected Archive IDs, patient IDs, and lesion IDs all matched the Challenge metadata v2 when checked against the 100 per-image API records. Image-level licenses were 57 `CC-BY` and 43 `CC-BY-NC`; apply the aggregate Challenge `CC BY-NC` conditions and retain the image-specific attribution in [attribution.csv](../analysis/nine_class_siim2020_pilot/attribution.csv). This research pilot assumes noncommercial use. Any later distribution must preserve the required attributions and obey both aggregate and image-level terms.

The Archive API's `files.full.size` differed from the number of bytes served for **all 100** selected URLs. The served bytes were valid decodable JPEGs; the [acquisition ledger](../analysis/nine_class_siim2020_pilot/acquisition.csv) records both sizes, dimensions, URL, license, attribution, and local SHA-256 for each file. Official S3 object `ETag` and `Content-Length` values were checked separately by `HEAD`: **100/100** ETags were plain 32-digit values matching local MD5 and all `HEAD` lengths matched the received files. The [source object checksums](../analysis/nine_class_siim2020_pilot/source_object_checksums.csv) record the evidence. This supports identity to the **current S3 objects**; it is not an authoritative checksum for the fixed 2020 Challenge JPEG ZIP. No authoritative package checksum was established, so Archive-served image bytes have **not** been proven byte-identical to that fixed ZIP. Local SHA-256 hashes identify precisely the files used in this pilot. The [acquisition and attribution record](../analysis/nine_class_siim2020_pilot/acquisition_and_attribution_record.json) freezes these source qualifications and the dataset citation.

## Deterministic selection and acquisition

The [frozen manifest](../analysis/nine_class_siim2020_pilot/pilot_manifest.csv) was written **before image retrieval**. It contains 100 officially labeled benign (`target=0`) records from **100 distinct patient IDs**. Each has its original lesion ID, original detailed diagnosis, Challenge metadata source, official duplicate-component ID and size, selection seed, source CSV hashes, API URL, and intended local path. Every image named in the official 425-pair duplicate list was excluded before selection; all chosen components are singletons. This protects the pilot from those **listed** duplicate pairs only. It is not complete photographic deduplication.

Selection is reproducible: require nonblank patient/lesion IDs and official benign target; exclude both endpoints of each listed duplicate pair; sort by SHA-256 of `siim2020-pilot-v1:42:<image_id>`; retain the first image per patient until 100 are selected. The deterministic seed is **42**. The source metadata SHA-256 is `a1c7c97c59e5f49232dfe3b6f6817efaaee5dbf9bc4ce584c1889e641be5c4e`; duplicate-list SHA-256 is `ddfd6c2d42430bd3581f3b2116bdb1433462a7109c715a02bf7f51115fcfabce`. The manifest SHA-256 is `b9b29fb423863ecec9e73084490f98284cb79f2a3b053f2defa42fe1883fdd93`. Original detailed diagnoses in this bounded draw are 82 `unknown`, 17 `nevus`, and 1 `seborrheic keratosis`; **none was relabeled**. The source-defined benign field means negative for the 2020 melanoma-detection task; it is not interchangeable with every benign HAM diagnosis or with the unverified Fanconic `BENIGN` label.

All 100 selected images were acquired (73,425,929 bytes total), decoded without changing their bytes, and stored under [images/](../analysis/nine_class_siim2020_pilot/images/). [Archive metadata verification](../analysis/nine_class_siim2020_pilot/archive_metadata_verification.csv) matched the Challenge patient and lesion IDs, image-level license, attribution, and full-image URL for **100/100** records. The official duplicate list does contain other relationships and eight known lesion-ID-discordant links in the full source; those records were excluded from this pilot rather than interpreted as separate lesions.

## Overlap screen

The pilot reused the existing Stage 4 canonical source manifest and fingerprints, covering **10,015 HAM10000** images and **3,297 canonical Fanconic** images at `data/isic/data/`. The mirrored Fanconic tree was not used. Local pilot SHA-256 values were compared to the canonical source manifest's SHA-256 values. The [canonical integrity check](../analysis/nine_class_siim2020_pilot/canonical_source_integrity.json) verifies that the manifest hashes still describe the local source image bytes. Existing pHash64 and dHash64 were computed with the repository's fingerprint code. A candidate was retrieved when **both** Hamming distances were at most 10; this bounded rule avoids very large candidate queues caused by generic low-texture dHash matches. It is **not** a calibrated sensitivity threshold. The five closest candidates per pilot image were additionally checked with the existing ORB/SIFT plus RANSAC geometric tool. A failed geometry result is never evidence of distinct identity; candidates beyond that rank remain explicitly untested geometrically.

The [candidate ledger](../analysis/nine_class_siim2020_pilot/overlap_candidates.csv), [per-image outcomes](../analysis/nine_class_siim2020_pilot/overlap_by_image.csv), and [summary](../analysis/nine_class_siim2020_pilot/overlap_summary.json) record the results:

| Measure | Result |
| --- | ---: |
| SHA-256-identical pilot-to-HAM/Fanconic pairs | 0 |
| Perceptual candidate pairs | 116 |
| Candidate pairs against HAM | 94 |
| Candidate pairs against canonical Fanconic | 22 |
| Pilot images with at least one candidate | 16 |
| Candidate pairs with coherent geometric evidence | 0 |
| Candidate pairs with unreliable geometric result | 45 |
| Candidate pairs without geometric check due to rank cap | 71 |
| Automated `confirmed` / `probable` image outcomes | 0 / 0 |
| Automated `uncertain` image outcomes | 16 |
| `no_candidate` under the stated rule | 84 |

All 116 candidate relations are **unreviewed and uncertain**. The [HTML gallery](../analysis/nine_class_siim2020_pilot/review_gallery.html) shows each original pilot and comparison image side by side, with a link to open each original at full resolution. It shows hashes and geometric evidence without making clinical or human identity decisions. Reviewer inspection should prioritize the 16 affected pilot images, especially the closest HAM candidates and all 22 Fanconic relations. The 71 geometrically untested pairs remain uncertain, as do the 45 with unreliable geometric results. No candidate under this rule means **no retrieved candidate**, not verified distinctness or patient independence. Crop, rotation, illumination, and low-texture cases can escape the rule; no independent detector false-negative rate has been established.

The provisional screen-level upper bound is **84/100** images with no retrieved candidate, spanning 84 of the 100 distinct sampled patient groups. This is **not 84 approved training images**. The other 16 patient groups remain quarantined pending relation review. Even the 84 need stronger photographic-overlap screening and a source/label approval decision before eligibility. Shared patients across HAM, SIIM, and Fanconic cannot be ruled out from these records; Fanconic has no verified patient-ID bridge.

## Nine-class implications and next gate

The output contract remains `AKIEC=0, BCC=1, BKL=2, DF=3, MEL=4, NV=5, VASC=6, BENIGN=7, MALIGNANT=8`. The seven HAM diagnostic labels and any Fanconic labels remain untouched. Here, candidate `BENIGN` examples come from the **SIIM–ISIC 2020 melanoma-detection training source**, whereas the paper's binary-label derivation/version is unverified. A modified nine-class experiment would need to name this difference prominently and report source-stratified results; it could learn source artifacts instead of diagnostic distinctions. This 100-image pilot is too small to justify a nine-class train/validation/calibration/test cohort or protected BENIGN test count.

The source appears **promising enough for a focused review** because 100 officially labeled images with 100 source patient IDs were acquired under recorded rights and 84 had no candidate at the bounded rule. That is a feasibility signal only. The smallest next action is to review the 16 candidate-bearing images in the gallery, refine screening for visually transformed overlap, and approve a versioned source/label policy. Only then select a larger bounded BENIGN cohort, verify each selected image's rights and attribution, reconcile duplicate/patient/lesion groups, and demonstrate all-nine-class protected split feasibility. Keep Stage 6 gates closed until an independent approval ledger and frozen eligible cohort exist. The original-paper route still requires author-confirmed source and protocol evidence.

## Reproduction

From the repository root, with `opencv-python`, `numpy`, `requests`, and project dependencies installed:

```powershell
python src/nine_class_siim2020_pilot.py select
python src/nine_class_siim2020_pilot.py acquire
python src/nine_class_siim2020_pilot.py verify-archive
python src/nine_class_siim2020_pilot.py verify-s3
python src/nine_class_siim2020_pilot.py verify-source
python src/nine_class_siim2020_pilot.py screen
python src/nine_class_siim2020_pilot.py finalize
python -m pytest tests/test_nine_class_siim2020_pilot.py -q
```

`select` refuses to replace an existing manifest. `acquire` is bounded by that manifest, verifies its frozen hash, and resumes already matching images without overwriting them. `screen` reads only the acquired pilot files and the two canonical source trees; it writes evidence, not eligibility approvals. The focused synthetic and artifact tests passed **3/3** locally. No training, split creation, dataset-gate change, image transformation, checkpoint creation, commit, or push occurred.
