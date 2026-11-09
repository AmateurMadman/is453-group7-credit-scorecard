# Archive

Older versions, kept for reference. Nothing here is current. The current version (v4) is in the repository root.

Version labels used across the repository:
- **v1** = script and Dossier.
- **v2** = first notebook and write-up.
- **v3** = 50k-500k segment with adjusted bins (`2ec24a8` to `4f1d6a4`).
- **v4** = 250k segment with automatic bins (`c995c86` and later). **Current.**

## v1-script/ (v1)
The original script-based version of the Medical Procedure Loans scorecard: `credit_scorecard_medical.py`, its Dossier
and the CSV and PNG outputs it produced.
- Source commit: `c4582a1`
- Headline results: cutoff 530, test AUC 0.684, 600 points = 50:1 odds scaling.
- Superseded. Kept for reference; do not use for slides.

## v2-before-validation-split/ (v2)
Copies of the combined notebook, its write-up and the three `g7_*.png` charts as they stood before the
train/validation/test split was added.
- Source commit: `a4295cb`
- Headline results: 15 variables, cutoff 580, test AUC 0.707.
- Superseded. Kept for reference; do not use for slides.

## v3-500k-adjusted-bins/ (v3)
The notebook, write-up, README and every `g7_*.csv` and `g7_*.png` as they stood at the end of the 500k version, with the
70/15/15 split and adjusted monotonic bins.
- Source commit: `4f1d6a4`
- Headline results: 50k-500k segment, 14 variables, adjusted monotonic bins, test AUC 0.7139, K-S 30.91%, cutoff 570,
  test profit 226.8m vs 170.3m if all approved.
- Superseded. Kept for reference; do not use for slides.

## When v4 is replaced
Do not delete it. Copy it into a new folder named `archive/v4-<short-description>/`, the same way v3 was archived: copy
the notebook (or take it from git with `git show <commit>:IS453_G7_Scorecard_Combined.ipynb`), the write-up and the
`g7_*` charts, then add a section here with the source commit, the headline results and the "Superseded" line.
