# New Test Files Created

This document lists all the new LaTeX test files created with their corresponding result files.

## Test Files Using $$ Notation (20 files)

### Simple Tests
1. **simple-fraction.tex** - Basic fraction: a/b = c/d
2. **pythagorean.tex** (using \[\]) - Pythagorean theorem: a² + b² = c²
3. **euler-identity.tex** (using \[\]) - Euler's identity: e^(iπ) + 1 = 0

### Moderate Complexity
4. **quadratic-formula.tex** - Quadratic formula with square root
5. **greek-letters.tex** - Greek alphabet symbols (α, β, γ, etc.)
6. **nested-fractions.tex** - Continued fractions
7. **integral-calculus.tex** - Integrals and derivatives
8. **matrix-simple.tex** - 2x2 matrix
9. **binomial-theorem.tex** - Summation with binomial coefficients
10. **limits-calculus.tex** - Limit expressions
11. **product-notation.tex** - Product notation (∏)
12. **chain-rule.tex** (using \[\]) - Derivative chain rule
13. **bayes-theorem.tex** (using \[\]) - Bayes' theorem
14. **wave-equation.tex** (using \[\]) - Wave equation PDE
15. **geometric-series.tex** (using \[\]) - Geometric series sum

### Complex Tests
16. **complex-expression.tex** - Gaussian/Normal distribution
17. **fourier-series.tex** - Fourier series with coefficients
18. **matrix-3x3.tex** - 3x3 determinant matrix
19. **taylor-series.tex** - Taylor series expansion of e^x
20. **cauchy-riemann.tex** - Partial differential equations
21. **stirling-approximation.tex** - Stirling's factorial approximation
22. **arrows-relations.tex** - Arrow symbols and relations
23. **overline-underline.tex** - Text decorations
24. **riemann-zeta.tex** (using \[\]) - Riemann zeta function
25. **laplace-transform.tex** (using \[\]) - Laplace transforms
26. **cauchy-integral.tex** (using \[\]) - Cauchy integral formula

### Very Complex Tests
27. **einstein-field.tex** - Einstein field equations (general relativity)
28. **schrodinger.tex** - Schrödinger equation (quantum mechanics)
29. **vector-calculus.tex** - Vector calculus identities with del operator
30. **maxwell-equations.tex** (using \[\]) - Maxwell's equations (electromagnetism)

## Result Files

Each .tex file has a corresponding .result.txt file containing the expected UTF-8 output:
- simple-fraction.result.txt
- quadratic-formula.result.txt
- greek-letters.result.txt
- nested-fractions.result.txt
- integral-calculus.result.txt
- matrix-simple.result.txt
- binomial-theorem.result.txt
- limits-calculus.result.txt
- complex-expression.result.txt
- einstein-field.result.txt
- fourier-series.result.txt
- product-notation.result.txt
- matrix-3x3.result.txt
- taylor-series.result.txt
- cauchy-riemann.result.txt
- schrodinger.result.txt
- vector-calculus.result.txt
- stirling-approximation.result.txt
- arrows-relations.result.txt
- overline-underline.result.txt
- pythagorean.result.txt
- euler-identity.result.txt
- chain-rule.result.txt
- riemann-zeta.result.txt
- laplace-transform.result.txt
- cauchy-integral.result.txt
- bayes-theorem.result.txt
- maxwell-equations.result.txt
- wave-equation.result.txt
- geometric-series.result.txt

## Testing Coverage

The test suite now covers:
- Basic fractions and operations
- Greek letters (α, β, γ, δ, ε, ζ, η, θ, π, Σ, etc.)
- Square roots and radicals
- Superscripts and subscripts
- Summation (Σ) and product (∏) notation
- Integration (∫) and derivatives
- Limits
- Matrices (2x2 and 3x3)
- Binomial coefficients (choose notation)
- Complex nested expressions
- Partial derivatives (∂)
- Vector calculus (∇)
- Both $$ and \[ \] display math delimiters
- Various arrow symbols (→, ⇒, ↔)
- Relations (≤, ≥, ≠, ≈)
- Overlines and underlines
- Left/right delimiters with automatic sizing

All result files were generated using the original tex2utf.pl script and verified to match the output of the refactored run.pl script.
