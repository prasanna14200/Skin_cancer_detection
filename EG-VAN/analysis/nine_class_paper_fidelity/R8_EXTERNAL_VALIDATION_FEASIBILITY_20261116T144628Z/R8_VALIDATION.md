# R8 independent validation

Independent verifier process: all checks below were recomputed from the generated evidence and current read-only source files.

- Candidate records: 300 unique source-qualified rows; PH2 200 and SIIM–ISIC 2020 100. All 300 image paths exist, match their recorded SHA-256 values, and decode.
- Mapping counts: PH2 NV 80, MEL 40, unsupported 80; SIIM detailed-diagnosis NV 17, BKL 1, unknown 82. Every row remains `UNREVIEWED` for overlap and `QUARANTINED` or `EXCLUDED` for eligibility.
- Screen recomputation: 300 per-image records and 7028 relations; PH2 99 affected images/580 relations; SIIM 68 affected images/6,448 relations. All relations are perceptual candidates with minimum Hamming distance <=6; exact-hash and identifier matches are zero.
- SIIM attribution register: 100 entries; 57 CC-BY and 43 CC-BY-NC; every entry retains attribution and a source hash.
- Source evidence register: 732 files; all before/after hashes agree and independently recomputed current hashes match. This includes the frozen checkpoint, 700 candidate images, PH2 source copies, code, manifests, prior evidence, and metadata.
- Internal fingerprints: the separate pre-generation recomputation matched all 13,312 saved pHash/dHash rows under OpenCV 5.0.0, with no missing or unreadable image.
- Training and model inference were not run. No source image, label, split, checkpoint, or prior audit package was modified.
- Deliverables (excluding the manifest itself): 12 files. The final SHA-256 manifest is generated and then independently read back and checked below.
