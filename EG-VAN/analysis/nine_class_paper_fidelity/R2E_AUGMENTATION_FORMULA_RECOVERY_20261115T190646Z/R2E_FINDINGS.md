# R2E Findings

## Outcome

- **Equation recovered:** Yes. Equation (15) is \(f(x_i)=\sum_{j=1}^{20}T_j(x_i)\).
- **Inline data notation recovered:** \(\sum_{i=1}^{N}(x_i,y_i)\).
- **Individually identifiable transformations:** 0 of 20.
- **Symbols with verified definitions:** 7 symbol roles are directly specified or bounded by the source: \(f\), \(x_i\), \(y_i\), \(\sum\), \(T_j\), and indices \(i\) and \(j\). \(N\) remains an unexplained upper-bound symbol. This count includes the index roles but not numeric constants/bounds.
- **Parameters/probabilities:** None specified for the transformations.
- **Reproducible from the paper alone:** No.
- **Direct link to Section G's 13 or conclusion's 20:** None established.
- **Crop function:** Presented as equation (14) before Section B, in the preceding preprocessing subsection; not explicitly identified as one of the \(T_j\).

## Evidence

The original PDF hash matched the expected value. Page 47 / content stream 122 was decompressed and inspected. Equation glyphs were recovered from source text-show operations and cross-checked against the page's font dictionaries, ToUnicode CMaps, and BLEX encoding Differences. The summation and equality signs were verified; subscript and superscript placement matches the text-only visual crop. The equation label `(15)` was also verified.

The prose explains \(x_i\), \(y_i\), \(f(x_i)\), \(\sum\), the generic role of \(T_j\), and the range \(j=1,\ldots,20\). It does not provide names or individual formulas for any \(T_j\). It says the transformations are combined by addition and mentions random modifications applied in a particular order, but gives no order or operational definition of that phrase.

## Relationship and scope

The Section B discussion names HAM-10000. No explicit text connects this formula to Section G's 13 techniques, the conclusion's 20 alternative methods, or Table 2. The R2C `POSSIBLY_RELATED` status is preserved; R2E does not force these references to be equivalent. The 1,965-image discrepancy was outside this stage's scope.

## Limitations

The page's unrelated figure region was excluded from visual inspection to respect the no-patient-image constraint. Verification was limited to text/math crops and PDF object/font evidence. The equation is recoverable, but its transformation identities, parameters, probabilities, selection/retention policy, application order, and implementation semantics are not.
