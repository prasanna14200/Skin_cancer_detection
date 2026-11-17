# R2E Augmentation Specification Gaps

## What is specified

Section B gives a generic augmentation definition, the inline data notation \(\sum_{i=1}^{N}(x_i,y_i)\), and equation (15):

\[
f(x_i)=\sum_{j=1}^{20}T_j(x_i).
\]

The text identifies \(x_i\) as input data and \(y_i\) as the associated label; calls \(f(x_i)\) the function applied to input \(x_i\); describes the summation as combining 20 transformations by addition; and says each \(T_j\) is a specific transformation applied to \(x_i\). It supplies the index range \(j=1,\ldots,20\).

## What remains unspecified

1. **Operation identity:** None of the 20 transformations is named or individually mathematically defined. Individually identifiable operations: **0**.
2. **Transformation parameters:** No values, ranges, or formulas are given for individual \(T_j\).
3. **Application probability:** No probability, sampling distribution, or selection frequency is given.
4. **Application order:** The prose says random modifications are put in “a particular order,” but gives no order or composition rule.
5. **Meaning of addition:** The text says the transformations are combined by addition, but does not define the addition domain or implementation semantics.
6. **Data-instance bound:** \(N\) is visible in the inline notation as the upper bound for \(i\), but is not assigned a value or separately defined in prose.
7. **Selection and retention:** No rule states which transformations are selected for each image, whether every image receives all 20, how generated outputs are retained, or whether original images are retained alongside them.
8. **Partition:** The surrounding Section B discussion names HAM-10000. The formula does not specify a train/validation/test assignment or state how validation/test isolation is maintained.
9. **Count accounting:** The formula supplies no per-class output counts, augmentation factor, or relation to Table 2.
10. **Link to later references:** No direct cross-reference ties the formula to Section G's 13 techniques or the conclusion's 20 alternative methods.

## Crop-function boundary

On the same printed page, the crop function is discussed before the `B. DATA AUGMENTATION` heading, under the preceding preprocessing subsection, and is equation (14). The text says it removes needless image area and sets image size to the model. This page organization supports treating crop as a separate preprocessing operation; the paper does not explicitly say whether crop is also included in the symbolic \(T_j\) family.

## Reproducibility assessment

Recovering equation (15) does not make the augmentation procedure reproducible. The identities, settings, probabilities, selection/retention policy, and execution semantics remain absent. No standard transformations have been substituted for the unnamed \(T_j\).
