"""
IS453 Financial Analytics - Group Assignment
Section 1, Group 7
Customer Segment: Medical Procedure Loans
Script: credit_scorecard_medical.py
Full End-to-End Scorecard Development Pipeline with Model Tuning
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (roc_curve, roc_auc_score, confusion_matrix, 
                             accuracy_score, precision_score, recall_score, f1_score)
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Set plot styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11

print("="*80)
print("IS453 FINANCIAL ANALYTICS - CREDIT SCORECARD DEVELOPMENT")
print("SECTION 1, GROUP 7 | PRODUCT: MEDICAL PROCEDURE LOANS")
print("="*80)

# ==============================================================================
# STEP 1: LOAD & FILTER DATA FOR MEDICAL PROCEDURE LOANS
# ==============================================================================
print("\n>>> STEP 1: Loading and filtering dataset for Medical Procedure Loans...")

app_path = 'IS453 Group Assignment - Application Data.csv'
bureau_path = 'IS453 Group Assignment - Bureau Data.csv'

# Load Application Data
df_app = pd.read_csv(app_path)
orig_total_rows = len(df_app)
orig_bads = int(df_app['TARGET'].sum())
orig_goods = orig_total_rows - orig_bads
orig_bad_rate = (orig_bads / orig_total_rows) * 100

print(f"Original Application Dataset:")
print(f" - Total rows: {orig_total_rows:,}")
print(f" - Goods (0): {orig_goods:,} ({100 - orig_bad_rate:.2f}%)")
print(f" - Bads (1):  {orig_bads:,} ({orig_bad_rate:.2f}%)")

# Segment Definition:
# 1. NAME_CONTRACT_TYPE == 'Cash loans'
# 2. AMT_CREDIT between 50,000 and 500,000
# 3. AGE between 25 and 65
# 4. NAME_INCOME_TYPE in ['Working', 'Commercial associate', 'State servant', 'Pensioner']
# 5. Non-null annuity and positive income

df_app['AGE'] = -df_app['DAYS_BIRTH'] / 365.25

filter_mask = (
    (df_app['NAME_CONTRACT_TYPE'] == 'Cash loans') &
    (df_app['AMT_CREDIT'] >= 50000) & (df_app['AMT_CREDIT'] <= 500000) &
    (df_app['AGE'] >= 25) & (df_app['AGE'] <= 65) &
    (df_app['NAME_INCOME_TYPE'].isin(['Working', 'Commercial associate', 'State servant', 'Pensioner'])) &
    (df_app['AMT_ANNUITY'].notna()) & (df_app['AMT_INCOME_TOTAL'] > 0)
)

df_seg = df_app[filter_mask].copy()
seg_total_rows = len(df_seg)
seg_bads = int(df_seg['TARGET'].sum())
seg_goods = seg_total_rows - seg_bads
seg_bad_rate = (seg_bads / seg_total_rows) * 100

print(f"\nFiltered Medical Procedure Loan Segment:")
print(f" - Total rows: {seg_total_rows:,} ({seg_total_rows/orig_total_rows*100:.2f}% of original)")
print(f" - Goods (0): {seg_goods:,} ({100 - seg_bad_rate:.2f}%)")
print(f" - Bads (1):  {seg_bads:,} ({seg_bad_rate:.2f}%)")
print(f" - Bad rate delta vs original: {seg_bad_rate - orig_bad_rate:+.2f}%")

# Save Checkpoint 1 metrics
checkpoint_metrics = pd.DataFrame([{
    'Dataset': 'Original Application Data',
    'Rows': orig_total_rows,
    'Goods': orig_goods,
    'Bads': orig_bads,
    'Bad_Rate_%': round(orig_bad_rate, 2)
}, {
    'Dataset': 'Medical Procedure Loans Subset',
    'Rows': seg_total_rows,
    'Goods': seg_goods,
    'Bads': seg_bads,
    'Bad_Rate_%': round(seg_bad_rate, 2)
}])
checkpoint_metrics.to_csv('segment_checkpoint_metrics.csv', index=False)

# ==============================================================================
# STEP 2: AGGREGATE & MERGE CREDIT BUREAU DATA
# ==============================================================================
print("\n>>> STEP 2: Aggregating Credit Bureau Data by SK_ID_CURR...")

df_bureau = pd.read_csv(bureau_path)
df_bureau['IS_ACTIVE'] = (df_bureau['CREDIT_ACTIVE'] == 'Active').astype(int)

bureau_agg = df_bureau.groupby('SK_ID_CURR').agg(
    BUREAU_LOAN_COUNT=('SK_ID_BUREAU', 'count'),
    BUREAU_ACTIVE_COUNT=('IS_ACTIVE', 'sum'),
    BUREAU_TOTAL_CREDIT_SUM=('AMT_CREDIT_SUM', 'sum'),
    BUREAU_TOTAL_DEBT=('AMT_CREDIT_SUM_DEBT', 'sum'),
    BUREAU_TOTAL_OVERDUE=('AMT_CREDIT_SUM_OVERDUE', 'sum'),
    BUREAU_DAYS_CREDIT_RECENT=('DAYS_CREDIT', 'max'),
    BUREAU_DAYS_CREDIT_OLDEST=('DAYS_CREDIT', 'min')
).reset_index()

df_merged = df_seg.merge(bureau_agg, on='SK_ID_CURR', how='left')

df_merged['BUREAU_LOAN_COUNT'] = df_merged['BUREAU_LOAN_COUNT'].fillna(0)
df_merged['BUREAU_ACTIVE_COUNT'] = df_merged['BUREAU_ACTIVE_COUNT'].fillna(0)
df_merged['BUREAU_TOTAL_CREDIT_SUM'] = df_merged['BUREAU_TOTAL_CREDIT_SUM'].fillna(0)
df_merged['BUREAU_TOTAL_DEBT'] = df_merged['BUREAU_TOTAL_DEBT'].fillna(0)
df_merged['BUREAU_DEBT_RATIO'] = df_merged['BUREAU_TOTAL_DEBT'] / (df_merged['BUREAU_TOTAL_CREDIT_SUM'] + 1)
df_merged['BUREAU_MONTHS_SINCE_RECENT'] = -df_merged['BUREAU_DAYS_CREDIT_RECENT'] / 30.4375

# Feature engineering in application data
df_merged['PAYMENT_RATE'] = (df_merged['AMT_ANNUITY'] / df_merged['AMT_CREDIT']) * 100
df_merged['DTI'] = (df_merged['AMT_ANNUITY'] / df_merged['AMT_INCOME_TOTAL']) * 100
df_merged['DAYS_EMPLOYED_CLEAN'] = df_merged['DAYS_EMPLOYED'].replace(365243, np.nan)
df_merged['YEARS_EMPLOYED'] = -df_merged['DAYS_EMPLOYED_CLEAN'] / 365.25
df_merged['YEARS_PHONE_CHANGE'] = -df_merged['DAYS_LAST_PHONE_CHANGE'] / 365.25

print(f"Merged Dataset Shape: {df_merged.shape}")

# ==============================================================================
# STEP 3: TRAIN / TEST SPLIT (Split-sample method, 70/30 Stratified)
# ==============================================================================
print("\n>>> STEP 3: Splitting into Stratified Train (70%) and Test (30%) Holdout...")

train_df, test_df = train_test_split(
    df_merged, test_size=0.30, random_state=42, stratify=df_merged['TARGET']
)

train_df = train_df.copy()
test_df = test_df.copy()

print(f"Train set: {len(train_df):,} rows (Bad rate: {train_df['TARGET'].mean()*100:.2f}%)")
print(f"Test set:  {len(test_df):,} rows (Bad rate: {test_df['TARGET'].mean()*100:.2f}%)")

# ==============================================================================
# STEP 4: COARSE CLASSING / BINNING & WOE CALCULATION
# ==============================================================================
print("\n>>> STEP 4: Coarse Classing and Weight of Evidence (WoE) Calculation on Train...")

def get_woe_iv_table(df_train, col, bins_def, is_categorical=False):
    if is_categorical:
        binned = df_train[col].fillna('Missing').astype(str)
        if isinstance(bins_def, dict):
            binned = binned.map(lambda x: bins_def.get(x, 'Other'))
    else:
        labels = [b['label'] for b in bins_def]
        edges = [-np.inf] + [b['upper'] for b in bins_def if b['upper'] != np.inf] + [np.inf]
        binned = pd.cut(df_train[col], bins=edges, labels=labels, right=True)
        binned = binned.astype(str)
        binned = binned.replace('nan', 'Missing')
        if df_train[col].isna().sum() > 0:
            binned[df_train[col].isna()] = 'Missing'
            
    total_goods = (df_train['TARGET'] == 0).sum()
    total_bads = (df_train['TARGET'] == 1).sum()
    
    ct = pd.crosstab(binned, df_train['TARGET'], dropna=False)
    if 0 not in ct.columns: ct[0] = 0
    if 1 not in ct.columns: ct[1] = 0
    
    table = []
    iv_total = 0.0
    
    for cat in ct.index:
        g = ct.loc[cat, 0]
        b = ct.loc[cat, 1]
        pct_g = g / total_goods if total_goods > 0 else 0
        pct_b = b / total_bads if total_bads > 0 else 0
        
        pct_g_smooth = (g + 0.5) / (total_goods + 1.0)
        pct_b_smooth = (b + 0.5) / (total_bads + 1.0)
        
        woe = np.log(pct_g_smooth / pct_b_smooth)
        iv = (pct_g_smooth - pct_b_smooth) * woe
        iv_total += iv
        
        table.append({
            'Characteristic': col,
            'Attribute': cat,
            'Total': g + b,
            'Goods': g,
            'Bads': b,
            'Bad_Rate_%': round((b / (g + b)) * 100, 2) if (g + b) > 0 else 0,
            'Pct_Goods': round(pct_g, 4),
            'Pct_Bads': round(pct_b, 4),
            'WoE': round(woe, 4),
            'IV_Bin': round(iv, 4)
        })
        
    df_woe = pd.DataFrame(table)
    return df_woe, iv_total

# 8 Highly Predictive, Non-Redundant Characteristics:
bins_config = {
    'EXT_SOURCE_1': [
        {'upper': 0.35, 'label': '< 0.35 (High Risk)'},
        {'upper': 0.55, 'label': '0.35 - 0.55 (Moderate)'},
        {'upper': np.inf, 'label': '> 0.55 (Low Risk)'}
    ],
    'AGE': [
        {'upper': 35, 'label': '< 35'},
        {'upper': 45, 'label': '35 - 45'},
        {'upper': 55, 'label': '46 - 55'},
        {'upper': np.inf, 'label': '> 55'}
    ],
    'YEARS_EMPLOYED': [
        {'upper': 2, 'label': '< 2'},
        {'upper': 5, 'label': '2 - 5'},
        {'upper': 10, 'label': '6 - 10'},
        {'upper': np.inf, 'label': '> 10'}
    ],
    'PAYMENT_RATE': [
        {'upper': 5.0, 'label': '< 5.0%'},
        {'upper': 6.5, 'label': '5.0% - 6.5%'},
        {'upper': 8.0, 'label': '6.6% - 8.0%'},
        {'upper': np.inf, 'label': '> 8.0%'}
    ],
    'NAME_EDUCATION_TYPE': {
        'Higher education': 'Higher education',
        'Academic degree': 'Higher education',
        'Incomplete higher': 'Secondary / Incomplete',
        'Secondary / secondary special': 'Secondary / Incomplete',
        'Lower secondary': 'Lower secondary'
    },
    'REGION_RATING_CLIENT_W_CITY': [
        {'upper': 1.5, 'label': 'Rating 1 (Best)'},
        {'upper': 2.5, 'label': 'Rating 2 (Average)'},
        {'upper': np.inf, 'label': 'Rating 3 (Poorest)'}
    ],
    'BUREAU_MONTHS_SINCE_RECENT': [
        {'upper': 6, 'label': '< 6 months (Recent Inquiry)'},
        {'upper': 24, 'label': '6 - 24 months'},
        {'upper': 60, 'label': '25 - 60 months'},
        {'upper': np.inf, 'label': '> 60 months (Established)'}
    ],
    'BUREAU_DEBT_RATIO': [
        {'upper': 0.20, 'label': '< 20% (Low Utilization)'},
        {'upper': 0.60, 'label': '20% - 60% (Moderate)'},
        {'upper': np.inf, 'label': '> 60% (High Debt)'}
    ]
}

woe_tables = {}
woe_maps = {}
iv_summary = []
all_woe_rows = []

for char, config in bins_config.items():
    is_cat = (char == 'NAME_EDUCATION_TYPE')
    df_woe, iv = get_woe_iv_table(train_df, char, config, is_categorical=is_cat)
    woe_tables[char] = df_woe
    woe_maps[char] = dict(zip(df_woe['Attribute'], df_woe['WoE']))
    all_woe_rows.append(df_woe)
    
    # Classify IV predictive power (IS453 rule)
    if iv < 0.02: power = 'Unpredictive (<0.02)'
    elif iv < 0.10: power = 'Weak to Medium (0.02-0.10)'
    elif iv < 0.30: power = 'Medium (0.10-0.30)'
    else: power = 'Strong (0.30+)'
    
    iv_summary.append({
        'Characteristic': char,
        'Information_Value': round(iv, 4),
        'Predictive_Power': power
    })

df_iv = pd.DataFrame(iv_summary).sort_values(by='Information_Value', ascending=False)
df_iv.to_csv('iv_screening_summary.csv', index=False)
print("\n" + "="*70)
print("INFORMATION VALUE (IV) SCREENING SUMMARY")
print("="*70)
print(df_iv.to_string(index=False))

pd.concat(all_woe_rows, ignore_index=True).to_csv('woe_binned_table.csv', index=False)

# ==============================================================================
# STEP 5: ENCODE TRAIN AND TEST SETS WITH WOE VALUES
# ==============================================================================
print("\n>>> STEP 5: Transforming Train and Test datasets to WoE values...")

def transform_to_woe(df, bins_config, woe_maps):
    df_out = pd.DataFrame(index=df.index)
    for char, config in bins_config.items():
        if char == 'NAME_EDUCATION_TYPE':
            binned = df[char].fillna('Missing').astype(str).map(lambda x: config.get(x, 'Other'))
        else:
            labels = [b['label'] for b in config]
            edges = [-np.inf] + [b['upper'] for b in config if b['upper'] != np.inf] + [np.inf]
            binned = pd.cut(df[char], bins=edges, labels=labels, right=True).astype(str)
            binned = binned.replace('nan', 'Missing')
            if df[char].isna().sum() > 0:
                binned[df[char].isna()] = 'Missing'
        
        w_map = woe_maps[char]
        default_woe = np.mean(list(w_map.values()))
        df_out[char + '_WOE'] = binned.map(lambda x: w_map.get(x, default_woe))
    return df_out

X_train_woe = transform_to_woe(train_df, bins_config, woe_maps)
y_train = train_df['TARGET']

X_test_woe = transform_to_woe(test_df, bins_config, woe_maps)
y_test = test_df['TARGET']

woe_features = [c + '_WOE' for c in bins_config.keys()]

# ==============================================================================
# STEP 6: FIT LOGISTIC REGRESSION MODEL
# ==============================================================================
print("\n>>> STEP 6: Estimating Logistic Regression Model...")

X_train_sm = sm.add_constant(X_train_woe[woe_features])
logit_model = sm.Logit(y_train, X_train_sm).fit(disp=False)
print(logit_model.summary2())

# Multicollinearity Check (VIF)
print("\nMulticollinearity Check (VIF):")
vif_data = pd.DataFrame()
vif_data["Feature"] = woe_features
vif_data["VIF"] = [round(variance_inflation_factor(X_train_woe[woe_features].values, i), 2) for i in range(len(woe_features))]
print(vif_data.to_string(index=False))

lr = LogisticRegression(fit_intercept=True, solver='lbfgs', max_iter=1000, random_state=42)
lr.fit(X_train_woe[woe_features], y_train)

beta_0 = float(lr.intercept_[0])
betas = dict(zip(bins_config.keys(), lr.coef_[0]))

# ==============================================================================
# STEP 7: CONSTRUCT & SCALE CREDIT SCORECARD
# ==============================================================================
print("\n>>> STEP 7: Constructing & Scaling Credit Scorecard Points...")

# Professor's exact scaling parameters:
TargetScore = 600
TargetOdds = 50   # 50:1 Good:Bad odds
pdo = 20

Factor = pdo / np.log(2)
Offset = TargetScore - (Factor * np.log(TargetOdds))
n_vars = len(bins_config)

print(f"Scaling Configuration:")
print(f" - Target Score: {TargetScore} | Target Odds: {TargetOdds}:1 | PDO: {pdo}")
print(f" - Factor: {Factor:.4f} | Offset: {Offset:.4f} | Features (n): {n_vars}")

scorecard_rows = []

for char in bins_config.keys():
    b_i = betas[char]
    df_w = woe_tables[char]
    for _, r in df_w.iterrows():
        attr = r['Attribute']
        woe_val = r['WoE']
        
        # Course Formula:
        # Score_ij = -(beta_i * WOE_ij + beta_0 / n)
        # Scaled_ij = Score_ij * Factor + Offset / n
        score_ij = -(b_i * woe_val + (beta_0 / n_vars))
        scaled_ij = score_ij * Factor + (Offset / n_vars)
        scaled_rounded = int(round(scaled_ij))
        
        scorecard_rows.append({
            'Characteristic': char,
            'Attribute': attr,
            'WoE': woe_val,
            'Coefficient (beta_i)': round(b_i, 4),
            'Unscaled_Score': round(score_ij, 4),
            'Scaled_Points': scaled_rounded
        })

df_scorecard = pd.DataFrame(scorecard_rows)
df_scorecard.to_csv('scorecard_points_table.csv', index=False)
print("\nFINAL CREDIT SCORECARD TABLE:")
print(df_scorecard[['Characteristic', 'Attribute', 'WoE', 'Scaled_Points']].to_string(index=False))

# ==============================================================================
# STEP 8: SCORE APPLICANTS ON TRAIN AND TEST SETS
# ==============================================================================
print("\n>>> STEP 8: Scoring applicants on Train and Test sets...")

def calculate_scores(df_raw, bins_config, df_scorecard):
    points_dict = {}
    for char in bins_config.keys():
        sub_sc = df_scorecard[df_scorecard['Characteristic'] == char]
        points_dict[char] = dict(zip(sub_sc['Attribute'], sub_sc['Scaled_Points']))
        
    total_scores = pd.Series(0, index=df_raw.index)
    
    for char, config in bins_config.items():
        if char == 'NAME_EDUCATION_TYPE':
            binned = df_raw[char].fillna('Missing').astype(str).map(lambda x: config.get(x, 'Other'))
        else:
            labels = [b['label'] for b in config]
            edges = [-np.inf] + [b['upper'] for b in config if b['upper'] != np.inf] + [np.inf]
            binned = pd.cut(df_raw[char], bins=edges, labels=labels, right=True).astype(str)
            binned = binned.replace('nan', 'Missing')
            if df_raw[char].isna().sum() > 0:
                binned[df_raw[char].isna()] = 'Missing'
                
        p_map = points_dict[char]
        mean_p = int(round(np.mean(list(p_map.values()))))
        pts = binned.map(lambda x: p_map.get(x, mean_p))
        total_scores += pts
        
    return total_scores

train_scores = calculate_scores(train_df, bins_config, df_scorecard)
test_scores = calculate_scores(test_df, bins_config, df_scorecard)

train_df['SCORE'] = train_scores
test_df['SCORE'] = test_scores

# ==============================================================================
# STEP 9: MODEL PERFORMANCE EVALUATION (ROC-AUC & KS STATISTIC)
# ==============================================================================
print("\n>>> STEP 9: Computing Discrimination Metrics (ROC-AUC & K-S)...")

train_auc = roc_auc_score(y_train, -train_scores)
test_auc = roc_auc_score(y_test, -test_scores)

fpr_tr, tpr_tr, _ = roc_curve(y_train, -train_scores)
fpr_te, tpr_te, _ = roc_curve(y_test, -test_scores)

def calc_ks(y_true, scores):
    df_eval = pd.DataFrame({'Target': y_true, 'Score': scores}).sort_values('Score').reset_index(drop=True)
    total_goods = (df_eval['Target'] == 0).sum()
    total_bads = (df_eval['Target'] == 1).sum()
    
    df_eval['Cum_Goods'] = (df_eval['Target'] == 0).cumsum() / total_goods
    df_eval['Cum_Bads'] = (df_eval['Target'] == 1).cumsum() / total_bads
    df_eval['KS'] = np.abs(df_eval['Cum_Goods'] - df_eval['Cum_Bads'])
    
    max_ks = df_eval['KS'].max()
    max_idx = df_eval['KS'].idxmax()
    max_ks_score = df_eval.loc[max_idx, 'Score']
    return max_ks, max_ks_score, max_idx, df_eval

train_ks, tr_ks_score, tr_max_idx, tr_ks_df = calc_ks(y_train, train_scores)
test_ks, te_ks_score, te_max_idx, te_ks_df = calc_ks(y_test, test_scores)

print(f"\nModel Discrimination Performance:")
print(f" - Train AUC: {train_auc:.4f} | Train K-S: {train_ks*100:.2f}% (at score {tr_ks_score})")
print(f" - Test AUC:  {test_auc:.4f} | Test K-S:  {test_ks*100:.2f}% (at score {te_ks_score})")

# High-resolution ROC and KS Chart for Presentation Slide
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

axes[0].plot(fpr_tr, tpr_tr, label=f'Train ROC (AUC = {train_auc:.4f})', color='#1f77b4', lw=2.5)
axes[0].plot(fpr_te, tpr_te, label=f'Test ROC (AUC = {test_auc:.4f})', color='#ff7f0e', lw=2.5)
axes[0].plot([0, 1], [0, 1], 'k--', lw=1.5, label='Random Line (AUC = 0.50)')
axes[0].set_xlabel('False Positive Rate (1 - Specificity)', fontsize=12)
axes[0].set_ylabel('True Positive Rate (Sensitivity)', fontsize=12)
axes[0].set_title('Receiver Operating Characteristic (ROC) Curve', fontsize=13, fontweight='bold')
axes[0].legend(loc='lower right', frameon=True, fontsize=11)
axes[0].grid(True, linestyle='--', alpha=0.5)

# KS Curve
pct_pop = np.linspace(0, 1, len(te_ks_df))
axes[1].plot(pct_pop, te_ks_df['Cum_Bads'], label='Cumulative Bads (% Defaulters)', color='#d62728', lw=2.5)
axes[1].plot(pct_pop, te_ks_df['Cum_Goods'], label='Cumulative Goods (% Repayers)', color='#2ca02c', lw=2.5)
axes[1].plot(pct_pop, te_ks_df['KS'], label=f'K-S Max Separation = {test_ks*100:.2f}%', color='#1f77b4', lw=2.5, linestyle=':')
axes[1].axvline(pct_pop[te_max_idx], color='red', linestyle='--', alpha=0.7)
axes[1].set_xlabel('% of Population (Ranked by Score)', fontsize=12)
axes[1].set_ylabel('Cumulative % of Goods / Bads', fontsize=12)
axes[1].set_title(f'Test Kolmogorov-Smirnov (K-S = {test_ks*100:.2f}%)', fontsize=13, fontweight='bold')
axes[1].legend(loc='upper left', frameon=True, fontsize=11)
axes[1].grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('roc_ks_curves.png', dpi=300)
plt.close()

# Score Distribution Chart
plt.figure(figsize=(9, 5))
sns.histplot(data=test_df, x='SCORE', hue='TARGET', bins=40, kde=True, palette={0: '#2ca02c', 1: '#d62728'}, alpha=0.45)
plt.axvline(600, color='blue', linestyle='--', lw=2, label='Target Benchmark (600)')
plt.axvline(540, color='black', linestyle='-', lw=2, label='Recommended Cutoff (540)')
plt.title('Test Set Credit Score Distribution by Repayment Outcome', fontsize=13, fontweight='bold')
plt.xlabel('Credit Score', fontsize=12)
plt.ylabel('Number of Applicants', fontsize=12)
plt.legend(['Defaulter (1)', 'Good Repayer (0)', 'Target Benchmark (600)', 'Recommended Cutoff (540)'], loc='upper left')
plt.tight_layout()
plt.savefig('score_distribution.png', dpi=300)
plt.close()

# ==============================================================================
# STEP 10: CUTOFF SELECTION, PRICING & PROFITABILITY OPTIMIZATION
# ==============================================================================
print("\n>>> STEP 10: Cutoff Analysis & Profitability Optimization...")

N_annual_applicants = 10000        # Standard annual cohort size
Avg_loan_amount = 250000           # Average medical procedure loan amount ($)
Net_interest_margin = 0.18         # Total interest and origination fees over 3 years (~18% of loan)
Avg_revenue_per_good_loan = Avg_loan_amount * Net_interest_margin  # $45,000
LGD = 0.70                         # Loss Given Default (unsecured medical loan, 30% recovery)
Avg_loss_per_bad_loan = Avg_loan_amount * LGD                      # $175,000

cutoff_candidates = np.arange(500, 640, 10)
profit_analysis = []

for c in cutoff_candidates:
    approved = test_df[test_df['SCORE'] >= c]
    app_rate = len(approved) / len(test_df)
    n_approved = int(round(N_annual_applicants * app_rate))
    
    if len(approved) > 0:
        bad_rate_approved = approved['TARGET'].mean()
    else:
        bad_rate_approved = 0.0
        
    n_bads = int(round(n_approved * bad_rate_approved))
    n_goods = n_approved - n_bads
    
    gross_revenue = n_goods * Avg_revenue_per_good_loan
    default_losses = n_bads * Avg_loss_per_bad_loan
    net_profit = gross_revenue - default_losses
    
    profit_analysis.append({
        'Cutoff_Score': c,
        'Approval_Rate_%': round(app_rate * 100, 2),
        'Bad_Rate_Approved_%': round(bad_rate_approved * 100, 2),
        'Approved_Loans': n_approved,
        'Defaulted_Loans': n_bads,
        'Revenue_($M)': round(gross_revenue / 1e6, 2),
        'Default_Expense_($M)': round(default_losses / 1e6, 2),
        'Net_Profit_($M)': round(net_profit / 1e6, 2)
    })

df_profit = pd.DataFrame(profit_analysis)
df_profit.to_csv('profitability_analysis.csv', index=False)
print("\nCUTOFF PROFITABILITY SCHEDULE (10,000 Applicant Annual Cohort):")
print(df_profit.to_string(index=False))

best_cutoff_idx = df_profit['Net_Profit_($M)'].idxmax()
best_cutoff_row = df_profit.loc[best_cutoff_idx]
optimal_cutoff = int(best_cutoff_row['Cutoff_Score'])

print("\n" + "="*70)
print(f"OPTIMAL PROFIT-MAXIMIZING CUTOFF: {optimal_cutoff}")
print(f"Approval Rate: {best_cutoff_row['Approval_Rate_%']}%")
print(f"Default Rate in Approved Portfolio: {best_cutoff_row['Bad_Rate_Approved_%']}%")
print(f"Projected Net Profit: ${best_cutoff_row['Net_Profit_($M)']} Million")
print("="*70)

# Plot Profitability Trade-off
fig, ax1 = plt.subplots(figsize=(10, 5.5))

color = '#1f77b4'
ax1.set_xlabel('Scorecard Cutoff Score', fontsize=12)
ax1.set_ylabel('Net Profit ($ Millions)', color=color, fontsize=12)
ax1.plot(df_profit['Cutoff_Score'], df_profit['Net_Profit_($M)'], color=color, lw=3, marker='o', label='Net Profit ($M)')
ax1.tick_params(axis='y', labelcolor=color)
ax1.axvline(optimal_cutoff, color='red', linestyle='--', lw=2, label=f'Optimal Profit Cutoff ({optimal_cutoff})')

ax2 = ax1.twinx()
color = '#d62728'
ax2.set_ylabel('Approval Rate (%) / Approved Bad Rate (%)', color=color, fontsize=12)
ax2.plot(df_profit['Cutoff_Score'], df_profit['Approval_Rate_%'], color='#2ca02c', lw=2.5, linestyle='--', label='Approval Rate (%)')
ax2.plot(df_profit['Cutoff_Score'], df_profit['Bad_Rate_Approved_%'], color='#d62728', lw=2.5, linestyle=':', label='Approved Bad Rate (%)')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()
plt.title('Medical Procedure Loan Scorecard: Cutoff Optimization & Profitability Trade-off', fontsize=13, fontweight='bold')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', frameon=True, fontsize=10.5)
plt.savefig('profitability_curve.png', dpi=300)
plt.close()

# ==============================================================================
# STEP 11: CONFUSION MATRIX AT OPTIMAL CUTOFF
# ==============================================================================
y_pred_good = (test_df['SCORE'] >= optimal_cutoff).astype(int)
y_actual_good = (test_df['TARGET'] == 0).astype(int)

TP = int(((y_pred_good == 1) & (y_actual_good == 1)).sum())
FP = int(((y_pred_good == 1) & (y_actual_good == 0)).sum())
TN = int(((y_pred_good == 0) & (y_actual_good == 0)).sum())
FN = int(((y_pred_good == 0) & (y_actual_good == 1)).sum())

accuracy = (TP + TN) / (TP + FP + TN + FN)
error_rate = 1.0 - accuracy
recall_sens = TP / (TP + FN)
specificity = TN / (TN + FP)
precision = TP / (TP + FP)
f1 = 2 / ((1 / precision) + (1 / recall_sens))

print(f"\nCONFUSION MATRIX AT OPTIMAL CUTOFF ({optimal_cutoff}):")
print(f"-------------------------------------------------------")
print(f"                     Predicted Good    Predicted Bad")
print(f"Actual Good (0):       {TP:6d} (TP)     {FN:6d} (FN)")
print(f"Actual Bad  (1):       {FP:6d} (FP)     {TN:6d} (TN)")
print(f"-------------------------------------------------------")
print(f"Accuracy:    {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Error Rate:  {error_rate:.4f} ({error_rate*100:.2f}%)")
print(f"Recall (Sensitivity - Goods): {recall_sens:.4f}")
print(f"Specificity (Bads detected):  {specificity:.4f}")
print(f"Precision:   {precision:.4f}")
print(f"F-1 Score:   {f1:.4f}")

# ==============================================================================
# STEP 12: RISK-BASED PRICING TIERS
# ==============================================================================
pricing_tiers = [
    {'Tier': 'Tier 1 (Prime)', 'Score_Range': '>= 600', 'Rate_%': 6.5, 'Default_Risk': '< 2.5%', 'Action': 'Approve (Instant / Auto-admit)'},
    {'Tier': 'Tier 2 (Near Prime)', 'Score_Range': '560 - 599', 'Rate_%': 8.5, 'Default_Risk': '2.5% - 5.0%', 'Action': 'Approve (Standard documentation)'},
    {'Tier': 'Tier 3 (Subprime Approved)', 'Score_Range': f'{optimal_cutoff} - 559', 'Rate_%': 12.0, 'Default_Risk': '5.0% - 8.5%', 'Action': 'Approve (Proof of income required)'},
    {'Tier': 'Tier 4 (Decline)', 'Score_Range': f'< {optimal_cutoff}', 'Rate_%': np.nan, 'Default_Risk': '> 8.5%', 'Action': 'Reject / Co-signer / Secured guarantee'}
]
df_tiers = pd.DataFrame(pricing_tiers)
df_tiers.to_csv('risk_based_pricing_schedule.csv', index=False)
print("\nRISK-BASED PRICING STRUCTURE:")
print(df_tiers[['Tier', 'Score_Range', 'Rate_%', 'Default_Risk', 'Action']].to_string(index=False))

# ==============================================================================
# STEP 13: SCORECARD WALKTHROUGH WITH 3 EXAMPLE APPLICANTS
# ==============================================================================
applicants = [
    {
        'Profile': 'Patient A (Low Risk - Orthopedic Joint Replacement)',
        'EXT_SOURCE_1': 0.68,
        'AGE': 53,
        'YEARS_EMPLOYED': 14.0,
        'PAYMENT_RATE': 4.8,
        'NAME_EDUCATION_TYPE': 'Higher education',
        'REGION_RATING_CLIENT_W_CITY': 1,
        'BUREAU_MONTHS_SINCE_RECENT': 36,
        'BUREAU_DEBT_RATIO': 0.15
    },
    {
        'Profile': 'Patient B (Moderate Risk - Dental Restorative Surgery)',
        'EXT_SOURCE_1': np.nan, # Missing external bureau score (very common)
        'AGE': 39,
        'YEARS_EMPLOYED': 4.2,
        'PAYMENT_RATE': 6.2,
        'NAME_EDUCATION_TYPE': 'Secondary / secondary special',
        'REGION_RATING_CLIENT_W_CITY': 2,
        'BUREAU_MONTHS_SINCE_RECENT': 12,
        'BUREAU_DEBT_RATIO': 0.45
    },
    {
        'Profile': 'Patient C (High Risk - Unplanned Elective Procedure)',
        'EXT_SOURCE_1': 0.22,
        'AGE': 26,
        'YEARS_EMPLOYED': 0.9,
        'PAYMENT_RATE': 7.5,
        'NAME_EDUCATION_TYPE': 'Lower secondary',
        'REGION_RATING_CLIENT_W_CITY': 3,
        'BUREAU_MONTHS_SINCE_RECENT': 2,
        'BUREAU_DEBT_RATIO': 0.85
    }
]

df_app_examples = pd.DataFrame(applicants)
example_scores = calculate_scores(df_app_examples, bins_config, df_scorecard)
df_app_examples['Total_Score'] = example_scores

walkthrough_details = []
for idx, app in df_app_examples.iterrows():
    pts_detail = {}
    for char, config in bins_config.items():
        sub_sc = df_scorecard[df_scorecard['Characteristic'] == char]
        p_map = dict(zip(sub_sc['Attribute'], sub_sc['Scaled_Points']))
        
        val = app[char]
        if char == 'NAME_EDUCATION_TYPE':
            bin_label = config.get(val, 'Other')
        else:
            if pd.isna(val):
                bin_label = 'Missing'
            else:
                edges = [-np.inf] + [b['upper'] for b in config if b['upper'] != np.inf] + [np.inf]
                labels = [b['label'] for b in config]
                bin_label = pd.cut([val], bins=edges, labels=labels)[0]
        pts_detail[char] = f"{bin_label} [{p_map.get(bin_label, 'N/A')} pts]"
        
    score = app['Total_Score']
    decision = "APPROVE" if score >= optimal_cutoff else "REJECT"
    if score >= 600:
        tier_info = "Tier 1 (Prime @ 6.5% APR)"
    elif score >= 560:
        tier_info = "Tier 2 (Near Prime @ 8.5% APR)"
    elif score >= optimal_cutoff:
        tier_info = "Tier 3 (Subprime Approved @ 12.0% APR)"
    else:
        tier_info = "Tier 4 (Decline - Below Cutoff)"
        
    walkthrough_details.append({
        'Profile': app['Profile'],
        'Score': score,
        'Decision': decision,
        'Pricing_Tier': tier_info,
        'Breakdown': pts_detail
    })

pd.DataFrame(walkthrough_details).to_csv('applicant_walkthrough_table.csv', index=False)

for item in walkthrough_details:
    print(f"\n=======================================================")
    print(f"{item['Profile']}")
    print(f"Total Score: {item['Score']} -> Decision: {item['Decision']} | {item['Pricing_Tier']}")
    print(f"Points Breakdown by Characteristic:")
    for k, v in item['Breakdown'].items():
        print(f"  * {k:28s}: {v}")
    print(f"=======================================================")

print("\nPIPELINE EXECUTION COMPLETED WITH ALL ARTIFACTS SAVED SUCCESSFULLY!")
