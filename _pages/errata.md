---
layout: page
permalink: /errata/
title: errata
description: Corrections to publications and preprints.
---

This page records known errata in our publications and preprints.

## Signomial and Polynomial Optimization via Relative Entropy and Partial Dualization

Section 5. In the display labeled (Ex5), the second appearance of the coefficient 15 in the defining expression for \(g_1(x)\) should be 1.5. The published expression was based on an incorrect transcription of the problem statement from Python code.

Section 5. In the first row of Table 3, the objective value \(f(x)\) of the output of Algorithm 1L should be 11.9643, rather than 11.9600. We are not entirely sure when or how this error made its way into the paper.

- A monotonicity analysis shows that the optimal objective value is 11.9643.
- Rijckaert and Martens report an objective value of 11.91. Evaluating the objective function at the point they provide instead gives 11.96392, with a constraint violation of \(5 \times 10^{-6}\).

## Randomized Numerical Linear Algebra: A Perspective on the Field With an Eye to Software

The following correction applies to [arXiv version 2](https://arxiv.org/pdf/2302.11474).

Section 5.3, on trace estimation. Under the heading "Split, trace, and approximate" (PDF page 113; printed page 106), the description of Hutch++ is incorrect. The matrix \(Q\) should not be sampled uniformly at random from the set of \(n \times m\) column-orthonormal matrices. It should be sampled as \(Q = \operatorname{orth}(A Q_0)\), where \(Q_0\) is uniformly random among \(n \times m\) column-orthonormal matrices.
