# R2D: Relationship Among the Three Numerical References

## Comparison

| Reference | Source wording | Locator | What is counted | Named operations / settings |
|---|---|---|---|---|
| A. Section B | “20” transformations represented by \(T_j\), with \(j=1,\ldots,20\); surrounding discussion says each \(T_j\) represents a specific transformation. The generic definition is: “Data augmentation is a technique that creates new data from existing data by applying random transformations.” | Section B, printed p. 72857; viewer 6; index 5; page object 47 / stream 122 | Symbolic transformation terms in the formula | No individual operation names or per-operation settings verified |
| B. Section G | “Finally, we employed thirteen data augmentation techniques on the 9-class dataset.” | Section G, printed p. 72869; viewer 18; index 17; page object 181 / stream 182 | 13 data augmentation techniques | No individual methods, parameters, or probabilities given; exact sentence is text-stream verified but not independently legible in the available visual view |
| C. Conclusion | “To enhance the discriminative features of data and expand the training dataset, we additionally applied a hair-removing algorithm, color balancing method, and twenty alternative data augmentation methods.” | Section VI, printed p. 72872; viewer 21; index 20; page object 469 / stream 534 | 20 alternative data augmentation methods | No augmentation methods individually listed or parameterized |

## Direct comparison and classification

**Classification: `POSSIBLY_RELATED`.**

Section G and the conclusion both explicitly describe data augmentation in the same paper and nine-class study, but the paper does not state whether 13 and 20 refer to the same set, different stages, subsets, or a revision. The word “alternative” does not by itself define a distinct set. Section B's 20 symbolic transformations are a third reference: its HAM-10000 context and formula do not explicitly connect it to either later passage.

No explicit cross-reference among A, B, and C was identified in the prior complete-paper search or in the surrounding inspected passages. The common topic and the repeated number 20 do not establish identity. The available evidence does not justify `SAME_CONCEPT_EXPLICIT`, `DIFFERENT_CONCEPT_EXPLICIT`, or `CONTRADICTORY`.

## Visual-source qualification

Printed pages 72857, 72869, and 72872 were visually inspected. The Section G page was viewed, but the exact 13-technique sentence could not be independently transcribed at the available image scale. Its exact quotation above is therefore attributed to the PDF text stream, not visual confirmation. The conclusion's 20-method wording was visible in the p. 72872 text crop.

## Dataset and Table 2 relation

Section B names HAM-10000 in its surrounding discussion. Section G expressly names the 9-class dataset. The conclusion says the methods were applied to expand the training dataset. None explicitly links its method count to Table 2's `Augmented Images` cells or supplies a class-wise image-count rule.
