# Archive

Older versions, kept for reference. Nothing here is current. The current version (v3) is in the repository root.

Version labels used across the repository: **v1** = script and Dossier, **v2** = first notebook and write-up,
**v3** = validation update plus later fixes (current).

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

## When v3 is replaced
Do not delete it. Copy it into a new folder named `archive/v3-<short-description>/`, the same way v2 was archived: copy
the notebook (or take it from git with `git show <commit>:IS453_G7_Scorecard_Combined.ipynb`), the write-up and the
`g7_*` charts, then add a section here with the source commit, the headline results and the "Superseded" line.
