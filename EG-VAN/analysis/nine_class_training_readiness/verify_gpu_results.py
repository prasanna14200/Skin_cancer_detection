"""Validate saved synthetic T4 smoke reports and write a traceable summary."""

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = (
    ("analysis/nine_class_gpu_smoke/t4_batch1_001/smoke_result.json", (1,)),
    ("analysis/nine_class_gpu_smoke/t4_batch2_001/smoke_result.json", (1, 2)),
    ("analysis/nine_class_gpu_smoke/t4_batch4_8_001/smoke_result.json", (4, 8)),
)


def verify(path: Path, expected_batches: tuple[int, ...]) -> dict:
    data = path.read_bytes()
    report = json.loads(data)
    assert report["schema_version"] == "nine_class_gpu_smoke_v1"
    assert report["gpu_name"] == "Tesla T4" and report["torch_version"] == "2.11.0+cu130"
    assert report["device"].startswith("cuda") and report["status"] == "PASSED"
    assert report["synthetic_only"] and not report["clinical_dataset_accessed"]
    assert not report["checkpoint_created"] and report["batchnorm_policy"] == "freeze_running_stats"
    assert tuple(result["batch_size"] for result in report["results"]) == expected_batches
    assert tuple(report["supported_batch_sizes_observed"]) == expected_batches
    rows = []
    for result in report["results"]:
        batch = result["batch_size"]
        assert result["status"] == "PASSED" and result["input_shape"] == [batch, 3, 384, 384]
        assert result["logits_shape"] == [batch, 9] and result["cuda_fp16_autocast"]
        assert result["cuda_grad_scaler"] and result["classifier_parameters_updated"]
        assert result["gradient_reset"] and not result["batchnorm_running_stats_changed"]
        assert result["batchnorm_policy"] == "freeze_running_stats"
        assert all(math.isfinite(result[key]) for key in ("focal_loss", "gradient_norm",
                                                     "duration_seconds_step_only"))
        assert result["gradient_norm"] > 0 and result["duration_seconds_step_only"] > 0
        assert 0 < result["peak_allocated_bytes"] <= result["peak_reserved_bytes"]
        rows.append({key: result[key] for key in ("batch_size", "focal_loss", "gradient_norm",
                    "duration_seconds_step_only", "peak_allocated_mib", "peak_reserved_mib",
                    "classifier_parameters_updated", "batchnorm_running_stats_changed")})
    return {"source_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(data).hexdigest(), "timestamp_utc": report["timestamp_utc"],
            "memory_free_before_bytes": report["memory_free_before_bytes"], "results": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("gpu_benchmark_verified.json"))
    args = parser.parse_args()
    verified = [verify(ROOT / path, sizes) for path, sizes in REPORTS]
    report = json.loads((ROOT / REPORTS[-1][0]).read_text(encoding="utf-8"))
    assert report["recommended_microbatch"]["batch_size"] == 8
    assert report["memory_free_before_bytes"] - report["results"][-1]["peak_reserved_bytes"] >= report["recommended_microbatch"]["required_headroom_bytes"]
    output = args.output
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = {"status": "VERIFIED_SAVED_SYNTHETIC_REPORTS", "gpu_name": "Tesla T4",
               "torch_version": "2.11.0+cu130", "reports": verified,
               "recommended_microbatch": 8, "proposed_accumulation_steps": 4,
               "nominal_effective_batch": 32,
               "clinical_training_approved": False,
               "note": "One synthetic optimizer step per batch; no full-epoch or clinical-data capacity measured"}
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
