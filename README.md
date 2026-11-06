# IS453 Group 7: Medical Procedure Loan Credit Scorecard

Credit scorecard for a Medical Procedure Loans product (IS453 Financial Analytics, Section 1, Group 7).
GitHub: AmateurMadman/is453-group7-credit-scorecard

## Version labels

| Label | What it is | Commit | Location |
| --- | --- | --- | --- |
| v1 | script and Dossier | `c4582a1` | `archive/v1-script/` |
| v2 | first notebook and write-up, before the validation split | `a4295cb` | `archive/v2-before-validation-split/` |
| v3 | validation update (70/15/15 split) plus later fixes. **Current version.** | `2ec24a8` and later | repository root |

## Current files (v3, use these)

| File | What it is |
| --- | --- |
| `IS453_G7_Scorecard_Combined.ipynb` | the full pipeline, executed, with outputs |
| `IS453_Group_7_Combined_Notebook_Writeup.md` | the write-up and slide plan; every number matches the executed notebook |
| `g7_*.csv`, `g7_*.png` | tables and charts saved by the notebook (the write-up and slides use these) |
| `requirements.txt` | pinned package versions |
| `IS453 Group Assignment - Application Data.csv`, `... - Bureau Data.csv` | the input data |
| `IS453 Group Assignment - Copy.docx`, `... - Data Dict.xlsx` | the assignment brief and data dictionary |

## Archive

`archive/` holds superseded versions (v1 and v2). Nothing there is current and it should not be used for slides.
See [archive/README.md](archive/README.md).

## Setup

Use **Python 3.11 or 3.12**. Python 3.13 does not work with the pinned `pandas==2.1.1` and `numpy==1.26.4`.

**Windows (PowerShell):**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**Mac / Linux (not tested by the group):**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If Python 3.11 is only available through Anaconda: `conda create -p .venv python=3.11`, activate it, then install
`requirements.txt` the same way.

## How to run

The notebook has to run on the Python and Jupyter inside `.venv`, **not on a global Python**.

- **VS Code:** open the notebook, choose "Select Kernel" and pick the `.venv` interpreter.
- **Jupyter in a browser:** activate `.venv` first, then run `python -m jupyter lab`.
- **Command line (runs every cell and saves outputs into the notebook):**

  ```powershell
  .venv\Scripts\python -m nbconvert --to notebook --execute --inplace IS453_G7_Scorecard_Combined.ipynb --ExecutePreprocessor.timeout=3600
  ```

  On Mac use `.venv/bin/python -m nbconvert ...`. The run can take 10 minutes or more.

The first notebook cell uses `%pip install`, which installs into the kernel's own environment. With `.venv` selected it
finds everything already installed.

## Troubleshooting

- **`numpy.dtype size changed, may indicate binary incompatibility`:** the notebook ran on the wrong Python (usually a
  global one with a different numpy). Check which Python the kernel uses, select `.venv`, and run from the command line
  with `.venv\Scripts\python -m nbconvert` rather than `python -m jupyter`, which can hand off to a global
  `jupyter-nbconvert` on your PATH. Do not run `%pip install` from a notebook that is attached to a global kernel.
- **`ModuleNotFoundError: pkg_resources`:** `setuptools<81` is pinned in `requirements.txt` for this reason. Reinstall the
  requirements.
- **Install errors or no wheels for pandas 2.1.1:** you are probably on Python 3.13. Recreate `.venv` with 3.11 or 3.12.
- **Kernel "IS453" or "python3" not found:** pick the `.venv` interpreter as the kernel, or register it with
  `python -m ipykernel install --user --name is453 --display-name "IS453 (.venv)"`.
- **`SettingWithCopyWarning` or `FutureWarning` messages:** harmless. The setup cell silences most of them.
- **Git says "LF will be replaced by CRLF":** harmless line-ending notice on Windows.
- **Results differ from the write-up:** check that package versions match `requirements.txt` and that the data files
  are unchanged. The key checks are a segment of 110,583 applicants, a 77,408 / 16,587 / 16,588 split, 14 predictors,
  test AUC 0.7139 and cutoff 570.
