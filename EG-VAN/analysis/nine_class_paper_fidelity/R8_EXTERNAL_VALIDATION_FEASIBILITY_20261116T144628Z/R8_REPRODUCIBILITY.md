# Reproducibility record

- Package timestamp: `20261116T144628Z`.
- Project root: `E:\Cancerdetection\EG-VAN`.
- Existing screening implementation: `src\nine_class_external_protocol.py` and `src\nine_class_similarity_audit.py`; neither was modified.
- Runtime for the candidate screen: Python 3.13, OpenCV 5.0.0, NumPy 2.1.3. OpenCV was installed only in the session temporary directory to invoke the existing helper; no project dependency or source file was changed.
- Internal Stage 4 inventory and fingerprints each contain 13,312 rows. Their hashes, along with checkpoint, code, provenance, source image, and prior-audit hashes, are in `R8_SOURCE_EVIDENCE_REGISTER.csv`.
- Frozen exploratory checkpoint: `analysis\nine_class_exploratory\runs\EXPLORATORY_ONLY_20261108T193315Z_d50a9c07\best.pt`; SHA-256 `3336df387025a0d7438b444d10236f846eed1327910117635bbae38601133e08`. It was not loaded.
- Candidate records and image hashes: `R8_QUARANTINED_CANDIDATE_SCREEN_INPUT.csv`.
- Overlap results: `overlap_screen\overlap_report.json` and `overlap_screen\overlap_candidates.csv`.
- No images are copied into this package.

To replay only the candidate retrieval with Python, NumPy, OpenCV, and the project source available, run this from PowerShell:

```powershell
@'
import sys
from pathlib import Path
sys.path.insert(0, r'E:\Cancerdetection\EG-VAN\src')
from nine_class_external_protocol import screen_external
root = Path(r'E:\Cancerdetection\EG-VAN')
package = root / r'analysis\nine_class_paper_fidelity\R8_EXTERNAL_VALIDATION_FEASIBILITY_20261116T144628Z'
screen_external(
    root,
    package / 'R8_QUARANTINED_CANDIDATE_SCREEN_INPUT.csv',
    root / r'analysis\nine_class_stage4\nine_class_source_manifest.csv',
    root / r'analysis\nine_class_similarity\fingerprints.csv',
    package / 'replay_screen',
    stage3_evidence=root / r'analysis\nine_class_recovery\stage3i\ai_pair_review.csv',
)
'@ | python -
```

Replaying the screen does not run inference and cannot approve a cohort. It may create a different `replay_screen` output; the frozen evidence for this package is under `overlap_screen`.
