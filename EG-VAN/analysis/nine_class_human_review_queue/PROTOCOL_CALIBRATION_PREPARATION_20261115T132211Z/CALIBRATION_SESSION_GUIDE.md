# Fictional Text-Only Calibration Session Guide

## Purpose and limits

This is a facilitator guide for a future calibration session with two reviewers and one adjudicator. The scenarios are invented teaching exercises, not real image decisions, validated medical examples, or evidence about any dataset. Do not use them to diagnose, infer patient or lesion identity, relabel data, approve a cohort, or approve a split. No real review batch is created by this guide.

## Materials and blinding

The facilitator may access `CALIBRATION_SCENARIOS.csv`. Its answer-key fields are facilitator-only. **Never send the full CSV or show its answer-key columns to either reviewer before both reviewers have independently completed and locked all scenario responses.** Prepare separate reviewer copies that contain only scenario ID, fictional observations, and blank response fields. Do not include the intended decisions, evidence rationale, misleading-cue notes, or confidence recommendation.

The reviewers work independently and must not see each other's responses. The adjudicator facilitates the session and does not reveal the answer key until both individual response sets are locked. The answer key is a teaching aid for these fictional descriptions only; it is not ground truth for actual image pairs. No AI, automated similarity, source-label, filename, hash, patient, or lesion-identity evidence is used.

## Session sequence

1. **Orient (10–15 minutes).** Explain the five categories:
   - `SAME_PHOTO`: the same original photographic capture, including transformed versions.
   - `SAME_LESION_DIFFERENT_PHOTO`: separately captured photographs with convincing lesion-specific correspondence.
   - `DISTINCT`: evidence supports different lesions; mere visual difference is insufficient.
   - `UNCERTAIN`: both observations are usable, but evidence cannot resolve the relationship.
   - `NOT_COMPARABLE`: at least one observation cannot be examined or is unusable for comparison.
   
   Reinforce that this is not diagnosis or identity determination. Explain HIGH/MODERATE/LOW confidence and require a concise evidence-based rationale plus limitations.
2. **Independent exercise.** Give each reviewer the blinded fictional scenarios in a separately controlled copy. Each independently records one category, confidence, rationale, limitations, and completion time for every scenario. No discussion or answer-key access is allowed during this step.
3. **Lock responses.** The facilitator obtains both completed response sets before any discussion. Preserve each original response set unchanged. Corrections, if needed, are separate dated entries; never overwrite initial responses.
4. **Compare agreement.** Build a five-category confusion table and report raw and per-category agreement. Separately summarize confidence agreement and rationale quality. Keep `UNCERTAIN` and `NOT_COMPARABLE` in all relevant denominators.
5. **Discuss disagreements.** Review differences without rewriting the locked responses. Ask what evidence each reviewer relied on, what remained ambiguous, and whether a misleading cue influenced the decision. Record discussion separately from original answers.
6. **Reveal facilitator key and clarify.** After discussion, the adjudicator may reveal the facilitator-only key and explain the intended evidence boundary. The key is specific to fictional scenario wording; it does not establish general correctness or validate visual skill.
7. **Second fictional round, if needed.** If the first round reveals recurring ambiguity (especially same-photo versus same-lesion, uncertain versus not-comparable, or unsupported DISTINCT decisions), the facilitator should draft or select a new, clearly fictional practice round under a separately controlled procedure. Keep its answer key hidden until responses are locked. Do not convert real queue pairs into practice examples.
8. **Readiness discussion.** Apply the checklist in `REVIEWER_READINESS_CHECKLIST.csv`. Record each criterion as NOT_ASSESSED until actual evidence exists. Text-only scenarios cannot establish readiness for visual comparison. Any readiness decision requires a separately authorized, documented process; do not infer readiness from high scenario agreement.

## Reviewer response expectations

For each invented scenario, record:

- one decision category;
- confidence in the evidence assessment;
- a short rationale tied only to the fictional visible details or stated access limitation;
- what evidence is missing or limiting the decision.

Do not cite diagnoses, filenames, labels, hashes, AI outputs, assumed patient or lesion identifiers, or presumed source. A resemblance is not distinctive correspondence. A crop or orientation change alone does not prove a new photograph or a different lesion. If evidence does not support a reliable category, choose `UNCERTAIN`; if a side is unavailable or unusable, choose `NOT_COMPARABLE`.

## Adjudicator role

The adjudicator enforces blinding and independent completion, preserves the original response sets, facilitates discussion, and clarifies rubric language. The adjudicator must not force consensus. If reviewers disagree or evidence is insufficient, record the unresolved status rather than manufacturing a definitive answer. The fictional key must not be used to overwrite a reviewer’s initial response.

## Completion record

The facilitator should document session date, participant roles, which fictional scenario version was used, whether independent responses were locked before discussion, observed terminology ambiguities, any second-round need, and the outcome of the readiness-criteria discussion. Do not include real pair IDs, image paths, or real review decisions.
