# Final Scorecard Numbers (for the slides)

Final model: **14 variables, automatic `sc.woebin` bins, no class weighting**. All numbers come from the executed
`IS453_G7_Scorecard_Combined.ipynb` (commit "switched to automatic bins") and its `g7_*.csv` outputs. Nothing needs to
be rerun. The "Old value" column is what the write-up and earlier slides used, so you can find and replace.

## 1. Segment and split

| Item | New value | Old value |
| :--- | :--- | :--- |
| Segment size | 38,263 applicants | 110,583 |
| Segment bad rate | 7.50% | 9.09% |
| Train / validation / test | 26,784 / 5,739 / 5,740 | 77,408 / 16,587 / 16,588 |
| Screening funnel | 102 → 49 (fine IV ≥ 0.02) → 41 (coarse) → 32 → **14** | 104 → 43 → 36 → 33 → 14 |

## 2. Model performance

| Set | AUC | Gini | K-S |
| :--- | :---: | :---: | :---: |
| Train | 0.7251 | 0.4503 | 33.81% |
| Validation | 0.7194 | 0.4387 | 35.06% |
| **Test** | **0.7080** | **0.4159** | **32.12%** |

Old test values: AUC 0.7139, Gini 0.4278, K-S 30.91%. Calibration: mean predicted PD 7.57% vs 7.51% observed on test.

## 3. Scaling and scorecard

- **Scaling:** 600 points = 19:1 good:bad odds (5% PD), **PDO = 20** (unchanged).
- **Score range:** 514 to 706 (old: 497 to 676).

| Characteristic (IV) | Bin → points (bad rate) |
| :--- | :--- |
| TERM_MONTHS (0.227) | <9.0 → 36 (9.9%) · 9.0–9.5 → 48 (5.5%) · 9.5–10.5 → 64 (2.4%) · 10.5–13.0 → 32 (12.1%) · ≥13.0 → 40 (8.1%) |
| EXT_SOURCE_1 (0.164) | missing → 41 · <0.26 → 27 · 0.26–0.40 → 39 · 0.40–0.58 → 48 · 0.58–0.70 → 53 · ≥0.70 → 66 |
| BUR_SHARE_ACTIVE (0.148) | missing → 34 · <0.24 → 54 · 0.24–0.40 → 49 · 0.40–0.52 → 41 · ≥0.52 → 34 |
| YEARS_EMPLOYED (0.132) | missing → 49 · <3.5 → 37 · 3.5–5.5 → 39 · 5.5–14 → 44 · ≥14 → 53 |
| OCCUPATION_TYPE (0.077) | missing → 45 · IT/HR/accountants/high-skill tech → 48 · managers/core/medicine/etc. → 44 · labourers/sales/drivers/etc. → 39 |
| CREDIT_TO_GOODS (0.072) | <1.01 → 42 · 1.01–1.10 → 44 · 1.10–1.17 → 47 · 1.17–1.24 → 40 · ≥1.24 → 36 |
| YEARS_ID_PUBLISH (0.052) | <2 → 37 · 2–7 → 39 · 7–11.5 → 42 · ≥11.5 → 47 |
| AMT_CREDIT (0.045) | <80k → 52 · 80k–155k → 46 · 155k–165k → 36 · ≥165k → 40 |
| BUR_MAX_AMT_OVERDUE (0.044) | missing → 40 · <500 → 49 · 500–14,000 → 37 · ≥14,000 → 34 |
| BUR_UTILISATION (0.041) | missing → 42 · <0.35 → 48 · 0.35–0.70 → 45 · 0.70–0.85 → 40 · ≥0.85 → 35 |
| NAME_FAMILY_STATUS (0.041) | widow → 50 · married → 44 · separated → 42 · single / civil marriage → 38 |
| NAME_EDUCATION_TYPE (0.031) | higher education / academic degree → 51 · secondary / incomplete higher / lower secondary → 40 |
| BUR_N_OPENED_12M (0.028) | 0 → 44 · 1 → 45 · 2 → 40 · ≥3 → 29 |
| LIVINGAREA_MEDI (0.021) | missing → 40 · <0.02 → 38 · 0.02–0.05 → 42 · 0.05–0.09 → 48 · ≥0.09 → 46 |

Full table with counts and WOE: `g7_final_bins_and_points.csv`.

## 4. Cutoff (chosen on validation)

| Item | New value | Old value |
| :--- | :--- | :--- |
| **Recommended cutoff** | **565** | 570 |
| Test approval rate | 89.2% (5,118 of 5,740) | 78.4% |
| Bad rate among approved (test) | 6.17% | 6.12% |
| Bad rate if everyone is approved (test) | 7.51% | 9.10% |
| K-S maximum (test) | 32.12% at score 581 | |

**Confusion matrix at 565 (test, positive = good payer):**

| | Predicted good | Predicted default |
| :--- | :---: | :---: |
| Actual good | TP 4,802 | FN 507 |
| Actual default | FP 316 | TN 115 |

Accuracy 85.66% · Error rate 14.34% · Sensitivity 90.45% · Specificity 26.68% · Precision 93.83% · F1 92.11%.

## 5. Profitability (assumptions unchanged: 15% APR, 5% cost of funds, 70% LGD, 24-month term)

| Policy (test set) | Approved | Defaults | Bad rate | Revenue | Losses | **Profit** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cutoff 565** | 5,118 | 316 | 6.17% | 90.7m | 37.9m | **52.8m** |
| Approve everyone | 5,740 | 431 | 7.51% | 101.4m | 53.0m | 48.5m |

Old values: 226.8m vs 170.3m. The new figures are smaller because the test set and the loans are both smaller. The
gain over approving everyone is about 9%, against 33% before.

**Profit by cutoff (test):** 540 → 49.5m · 550 → 50.1m · 560 → 53.0m · **565 → 52.8m** · 570 → 53.1m · 580 → 52.0m ·
590 → 44.8m · 600 → 35.2m · 620 → 17.1m. The curve is flat between 560 and 580; 565 is the maximum on validation, so it
is the one we report.

**Sensitivity of the best cutoff (validation):**

| Term | LGD 50% | LGD 70% | LGD 90% |
| :--- | :---: | :---: | :---: |
| 12 months | 580 | 585 | 595 |
| 24 months | 555 | **565** | 580 |
| 36 months | 540 | 550 | 565 |

## 6. Pricing (score bands from validation)

| Band | Score | Applicants | Bad rate | Break-even APR | Indicative APR | Origination check |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| Tier 1 (Prime) | 625+ | 905 | 1.66% | 6.1% | 9.5% | Standard documents; verify clinic before payment |
| Tier 2 (Near prime) | 605–624 | 1,202 | 3.24% | 7.1% | 10.5% | Standard documents and verified clinic quote |
| Tier 3 (Standard) | 585–604 | 1,646 | 5.53% | 8.8% | 12.0% | Income and clinic-plan checks |
| Tier 4 (Higher risk) | 565–584 | 1,348 | 11.80% | 13.5% | 16.5% | Full income and verified clinic plan |
| Decline | below 565 | 638 | 19.75% | 20.4% | n/a | Decline, or refer for co-signer or security |

- Every approved band breaks even below the 15% product rate; below 565 would need about 20.4%, so those are declined.
- **Flat 15%: 52.8m** vs **tiered rates: 29.2m** (old: 127.2m) vs approve everyone: 48.5m → keep one 15% rate, bands only
  set the checks.

## 7. Walkthrough applicants (test set, 10th / 50th / 90th percentile)

| Characteristic | 190847 | 388013 | 319977 |
| :--- | :---: | :---: | :---: |
| TERM_MONTHS | 40 | 40 | 64 |
| YEARS_EMPLOYED | 44 | 49 | 37 |
| BUR_SHARE_ACTIVE | 34 | 34 | 54 |
| EXT_SOURCE_1 | 41 | 53 | 48 |
| NAME_EDUCATION_TYPE | 40 | 40 | 40 |
| BUR_N_OPENED_12M | 44 | 44 | 44 |
| BUR_MAX_AMT_OVERDUE | 40 | 40 | 40 |
| YEARS_ID_PUBLISH | 39 | 42 | 47 |
| OCCUPATION_TYPE | 39 | 45 | 39 |
| CREDIT_TO_GOODS | 42 | 40 | 42 |
| LIVINGAREA_MEDI | 40 | 48 | 48 |
| BUR_UTILISATION | 42 | 42 | 42 |
| AMT_CREDIT | 40 | 40 | 46 |
| NAME_FAMILY_STATUS | 38 | 38 | 42 |
| **Total** | **563 → Decline** | **595 → Approve** | **633 → Approve** |
| Actual outcome | repaid | repaid | repaid |

Old example scores: 558 / 588 / 619. Applicant 190847 misses the cutoff by 2 points but repaid: the cost of a cutoff.
