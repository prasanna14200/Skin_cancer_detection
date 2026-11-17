# R2E Equation Transcription

## Evidence basis

Section B, printed p. 72857, viewer page 6, zero-based index 5, page object 47 / content stream 122 (`FlateDecode`). The equation below is reconstructed from the PDF's original text-show operators, font encoding/ToUnicode references, and a text-only visual crop. The source equation number `(15)` is present.

## Inline dataset notation

The text immediately before equation (15) contains this inline summation notation:

\[
\sum_{i=1}^{N}(x_i,y_i)
\]

It appears in the sentence beginning “Let’s assuming” and preceding “are a dataset of input-output pairs”. The PDF text stream records \(x_i\) and \(y_i\) separately, with the comma glyph; their positions and font encodings place \(N\) as the upper limit and \(i=1\) as the lower index. The prose identifies \(x_i\) as input data and \(y_i\) as its associated label. The paper does not separately explain the meaning or value of \(N\).

## Equation (15)

\[
f(x_i)=\sum_{j=1}^{20}T_j(x_i)
\tag{15}
\]

### Glyph-by-glyph evidence

| Printed element | Recovery evidence | Status |
|---|---|---|
| \(f\) | T1_6 italic glyph in the source text-show sequence | VERIFIED |
| \((x_i)\) | T1_7 parenthesis glyphs plus T1_6 italic \(x\) and subscript \(i\); matches the visual crop | VERIFIED |
| \(=\) | T1_5 code `D`, mapped to U+003D by ToUnicode object 34 | VERIFIED |
| \(\sum\) | T1_8 code `X` (88); BLEX Encoding object 515 names code 88 `/summationdisplay`; visual crop shows the summation operator | VERIFIED |
| Upper limit \(20\) | T1_4 digit glyphs positioned above/right of the summation operator | VERIFIED |
| Lower index \(j=1\) | T1_6 \(j\), T1_5 equality glyph, and T1_4 digit \(1\), positioned below the summation operator | VERIFIED |
| \(T_j(x_i)\) | T1_6 italic glyphs and subscript/parenthesis positions in the source sequence | VERIFIED |
| Equation label `(15)` | Source text-show operator and visual crop | VERIFIED |

## Exact source explanation, transcribed from the text stream

> “Here, \(f(x_i)\) represents the function applied to the input \(x_i\). The sum operator \(\sum\) signifies the summation over 20 different transformations denoted by \(T_j(x_i)\), where \(j\) ranges from 1 to 20. Each \(T_j\) represents a specific transformation applied to \(x_i\), and the sum indicates that these transformations are combined by addition. After applying these augmentation techniques, we produced new input data \(f(x_i)\) that are identical to the original data but with some changes by putting these random modifications in a particular order.”

The quotation preserves the paper's wording except that typeset mathematical glyphs are represented in mathematical notation. It is not a claim that the described operation is fully specified or reproducible.

## Unresolved notation

- \(N\) is visible as the upper bound in the inline dataset notation, but its explicit prose definition is absent.
- \(j\) is explicitly stated to range from 1 to 20; no transformation name is associated with any particular value of \(j\).
- The paper says the transformations are combined by addition, but does not state whether this is pixel-wise addition, an abstract aggregation, or another implementation convention.
- “In a particular order” does not provide an actual order or an operation-composition rule.
