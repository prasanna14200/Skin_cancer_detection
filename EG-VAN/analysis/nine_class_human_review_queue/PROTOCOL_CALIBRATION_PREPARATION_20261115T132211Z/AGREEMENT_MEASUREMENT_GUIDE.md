# Agreement Measurement Guide

## Scope

Use these measures to describe agreement between two independent reviewers on the same set of cases. Agreement is not ground truth and does not prove that a decision is correct. Keep `SAME_PHOTO`, `SAME_LESION_DIFFERENT_PHOTO`, `DISTINCT`, `UNCERTAIN`, and `NOT_COMPARABLE` as five nominal categories unless a separate, justified measurement design says otherwise.

## Measures

### Raw percentage agreement

Let `N` be all cases with both reviewers' initial decisions recorded, and `A` be the number of cases where the two categories match:

`Raw agreement = A / N`

Report numerator and denominator. Do not omit `UNCERTAIN` or `NOT_COMPARABLE`. If a decision is missing, report its count separately and define whether the case is outside the paired-decision denominator; never silently drop it.

### Per-category agreement and confusion matrix

Create a 5-by-5 table with Reviewer 1's category as rows and Reviewer 2's category as columns. Publish cell counts and, if useful, row-normalized proportions. The diagonal shows exact category agreement; off-diagonal cells show the disagreements that overall agreement can hide.

For a symmetric per-category positive agreement summary, for each category compute:

`2a / (2a + b + c)`

where `a` is the number both reviewers assigned that category, `b` is Reviewer 1 only, and `c` is Reviewer 2 only. State the denominator; if it is zero, report the measure as undefined rather than zero. Also report each reviewer's category counts so prevalence is visible.

### Cohen's kappa

For two reviewers assigning nominal categories to the same cases:

`kappa = (Po - Pe) / (1 - Pe)`

`Po` is observed agreement (`A/N`). `Pe` is chance-expected agreement from the category marginals: `sum_k (row_total_k / N) * (column_total_k / N)`. Report the confusion matrix, marginals, N, and kappa together. If `1 - Pe` is zero, report kappa as undefined.

Kappa is sensitive to category prevalence and marginal distributions; a low or high value should not be interpreted without the counts. Small calibration samples make all agreement estimates unstable. Do not use kappa as a pass/fail criterion without a separately justified rationale and explicit project decision.

### Weighted kappa

The five relationship outcomes are not inherently ordinal. Do not compute weighted kappa unless a defensible ordinal ordering and weights have been explicitly justified and approved for a specific analysis. Do not impose an order on the five categories merely to obtain a weighted statistic.

### Confidence agreement

Report confidence separately from category agreement: each reviewer’s HIGH/MODERATE/LOW counts, a cross-tabulation of the three confidence levels, and exact confidence agreement (`matching confidence ratings / cases with both ratings`). Confidence is ordinal, but this guide does not prescribe a weighted confidence statistic. Confidence agreement is not decision correctness.

### Adjudication and unresolved rates

Define denominators before analysis and report counts as well as rates:

- **Initial disagreement rate:** cases with different initial categories divided by cases with two recorded initial categories.
- **Adjudication rate:** cases sent to adjudication divided by cases with two recorded initial reviews. Also report cases escalated for LOW confidence or inadequate rationale even when categories match.
- **Unresolved rate:** cases whose final status remains `UNCERTAIN` or `NOT_COMPARABLE` divided by all cases with a recorded final disposition. Report each unresolved category separately.

Adjudication does not erase the original pair of decisions. Preserve both initial decisions, confidence ratings, rationales, and timestamps; store adjudicator identity, outcome, rationale, and timestamp separately. Report unresolved cases rather than excluding them.

## Interpretation limits

- Twelve fictional text scenarios are a teaching exercise, not a validated reliability study or proof of visual-review readiness.
- Small samples yield unstable estimates; include counts and avoid overinterpretation.
- High agreement does not prove correctness or eliminate shared bias.
- Kappa can be affected by category prevalence and reviewer marginals.
- `UNCERTAIN` and `NOT_COMPARABLE` are meaningful outcomes and must not be silently excluded or recoded.
- Do not set a numerical passing threshold without a justified rationale and explicit project decision.
- These measures do not establish clinical validity, patient-level independence, dataset provenance, cohort eligibility, or split approval.

## Reporting template

For each completed exercise, report: sample description; number assigned; number with paired initial decisions; missing-response count; five-category confusion matrix; each reviewer’s category counts; raw agreement with numerator/denominator; per-category agreement with denominators; Cohen's kappa with marginals and limitations (or reason undefined/not computed); confidence cross-tab and exact agreement; disagreement and adjudication counts/rates; unresolved `UNCERTAIN` and `NOT_COMPARABLE` counts/rates; and a statement that agreement is not ground truth. Any threshold must cite its rationale and explicit approval. Do not claim reviewer readiness from agreement statistics alone.
