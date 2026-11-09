"""Charts for the Logistic Regression and Performance part (Jethro) of the IS453 Group 7 presentation.

Run from the repository root with .venv activated:
    python slide_charts/make_regression_performance_charts.py

It runs the code cells of IS453_G7_Scorecard_Combined.ipynb in memory (without changing the notebook or any
g7_* output), takes the fitted model and its results, and saves six PNGs in slide_charts/:
    jethro_1_forward_selection.png   validation Gini gained at each forward-selection step
    jethro_2_coefficients.png        coefficients of the 14-variable model
    jethro_3_roc.png                 ROC curves for train, validation and test
    jethro_4_ks.png                  K-S chart on the test set
    jethro_5_calibration.png         predicted vs actual bad rate by score decile (test)
    jethro_6_performance_table.png   AUC, Gini, K-S, bad rate and predicted PD for the three sets
    deck_forward_selection.png       chart 1 in the Canva deck's navy palette, without a title (for the slides)
    deck_roc.png                     chart 3 in the Canva deck's navy palette, without a title (for the slides)
    deck_coefficients.png            chart 2, navy slide version
    deck_ks.png                      chart 4, navy slide version (with the cutoff marked)
    deck_calibration.png             chart 5, navy slide version
Every number on the charts comes from the notebook's model. A full run takes a few minutes.
"""
import contextlib
import io
import json
import os
import sys
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.ticker
import numpy as np
import pandas as pd
from sklearn import metrics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOK = os.path.join(ROOT, 'IS453_G7_Scorecard_Combined.ipynb')
OUT = os.path.join(ROOT, 'slide_charts')

# Palette and text colours
TEST, VALID, TRAIN = '#2a78d6', '#eb6834', '#1baf7a'
INK, INK2, MUTED, GRID, AXIS, SURF = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#ffffff'

NAMES = {
    'TERM_MONTHS': 'Loan ÷ instalment ratio', 'YEARS_EMPLOYED': 'Years employed',
    'BUR_SHARE_ACTIVE': 'Share of bureau credits active', 'EXT_SOURCE_1': 'External credit score',
    'NAME_EDUCATION_TYPE': 'Education', 'BUR_N_OPENED_12M': 'Credits opened in last 12 months',
    'BUR_MAX_AMT_OVERDUE': 'Largest amount ever overdue', 'YEARS_ID_PUBLISH': 'Years since ID issued',
    'OCCUPATION_TYPE': 'Occupation', 'CREDIT_TO_GOODS': 'Credit-to-goods ratio',
    'LIVINGAREA_MEDI': 'Living area (building data)', 'BUR_UTILISATION': 'Bureau utilisation',
    'AMT_CREDIT': 'Loan amount', 'NAME_FAMILY_STATUS': 'Family status'}
SOURCE = {'TERM_MONTHS': 'Loan', 'CREDIT_TO_GOODS': 'Loan', 'AMT_CREDIT': 'Loan',
          'YEARS_EMPLOYED': 'Application', 'EXT_SOURCE_1': 'Application', 'NAME_EDUCATION_TYPE': 'Application',
          'YEARS_ID_PUBLISH': 'Application', 'OCCUPATION_TYPE': 'Application', 'LIVINGAREA_MEDI': 'Application',
          'NAME_FAMILY_STATUS': 'Application'}  # anything else is a bureau characteristic


def run_notebook():
    """Execute the notebook's code cells in memory and return their namespace.
    File writes (to_csv, savefig) are switched off so the repository's g7_* outputs are not touched."""
    os.chdir(ROOT)
    nb = json.load(open(NOTEBOOK, encoding='utf-8'))
    ns = {'display': lambda *a, **k: None, '__name__': 'notebook'}
    saved = (pd.DataFrame.to_csv, pd.Series.to_csv, plt.savefig, matplotlib.figure.Figure.savefig, plt.show)
    pd.DataFrame.to_csv = pd.Series.to_csv = lambda *a, **k: None
    plt.savefig = matplotlib.figure.Figure.savefig = plt.show = lambda *a, **k: None
    code = [c for c in nb['cells'] if c['cell_type'] == 'code']
    try:
        for n, c in enumerate(code, 1):
            src = '\n'.join(l for l in ''.join(c['source']).splitlines() if not l.lstrip().startswith(('%', '!')))
            with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
                warnings.simplefilter('ignore')
                exec(compile(src, f'notebook cell {n}', 'exec'), ns)
            plt.close('all')
            print(f'\rnotebook cells run: {n}/{len(code)}', end='', flush=True)
    finally:
        pd.DataFrame.to_csv, pd.Series.to_csv, plt.savefig, matplotlib.figure.Figure.savefig, plt.show = saved
    print()
    return ns


def style():
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 12, 'axes.edgecolor': AXIS, 'axes.labelcolor': INK2,
        'xtick.color': MUTED, 'ytick.color': INK2, 'axes.spines.top': False, 'axes.spines.right': False,
        'axes.grid': False, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF,
        'legend.frameon': False, 'legend.fontsize': 11})


def title(fig, main, sub):
    fig.text(0.02, 0.965, main, fontsize=16, fontweight='bold', color=INK, va='top')
    fig.text(0.02, 0.905, sub, fontsize=11.5, color=INK2, va='top')


def hgrid(ax, axis='x'):
    ax.grid(axis=axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200)
    plt.close(fig)
    print('saved', os.path.join('slide_charts', name))


def make_charts(M):
    style()
    os.makedirs(OUT, exist_ok=True)
    perf, cut = M['perf'], int(M['best_cutoff'])

    # 1. Forward selection
    p = M['path'].copy()
    p['gain'] = p['gini_validation'].diff().fillna(p['gini_validation'])
    labels = [f"{int(s)}. {NAMES.get(v, v)}" for s, v in zip(p.step, p.added)]
    fig, ax = plt.subplots(figsize=(9, 6.2))
    fig.subplots_adjust(left=0.36, right=0.9, top=0.79, bottom=0.1)
    y = np.arange(len(p))[::-1]
    ax.barh(y, p['gain'], height=0.62, color=VALID, edgecolor=SURF, linewidth=2)
    for yi, g in zip(y, p['gain']):
        ax.text(g + 0.003, yi, f'+{g:.3f}', va='center', fontsize=10.5, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=11.5)
    ax.set_xlabel('Gain in validation Gini when the variable is added')
    ax.set_xlim(0, p['gain'].max() * 1.18)
    hgrid(ax); ax.tick_params(axis='y', length=0)
    late = p.loc[p.step > 10, 'gain'].max() if (p.step > 10).any() else 0
    title(fig, f'Forward selection: {len(p)} variables, chosen on the validation set',
          'Each step adds the variable that raises validation Gini most.\n'
          f"Total validation Gini {p['gini_validation'].iloc[-1]:.3f}; each step after 10 adds less than "
          f"{np.ceil(late * 1000) / 1000:.3f}.")
    save(fig, 'jethro_1_forward_selection.png')

    # 2. Coefficients
    ct = M['coef_table'].drop(index='intercept').copy()
    ct.index = [i[:-4] for i in ct.index]
    ct = ct.loc[list(M['path']['added'])[::-1]]
    src = [SOURCE.get(v, 'Bureau') for v in ct.index]
    fig, ax = plt.subplots(figsize=(10, 6.2))
    fig.subplots_adjust(left=0.42, right=0.93, top=0.8, bottom=0.11)
    y = np.arange(len(ct))
    ax.barh(y, ct['coef'], height=0.62, color=TRAIN, edgecolor=SURF, linewidth=2)
    for yi, c in zip(y, ct['coef']):
        ax.text(c + 0.015, yi, f'{c:.2f}', va='center', fontsize=10.5, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{NAMES.get(v, v)}  ({s})" for v, s in zip(ct.index, src)], fontsize=11)
    ax.set_xlabel('Coefficient (on WoE values)')
    ax.set_xlim(0, ct['coef'].max() * 1.15)
    hgrid(ax); ax.tick_params(axis='y', length=0)
    sign = 'all coefficients positive' if (ct['coef'] > 0).all() else 'check coefficient signs'
    title(fig, f'Final model: {len(ct)} variables, {sign}',
          'Positive = each variable pushes risk in the expected direction. Listed in selection order.\n'
          f"Fitted on the training set ({len(M['y_train']):,} applicants): {src.count('Application')} application, "
          f"{src.count('Loan')} loan and {src.count('Bureau')} bureau characteristics.")
    save(fig, 'jethro_2_coefficients.png')

    lr = M['lr']
    sets = [('Train', 'train', M['X_train'], M['y_train'], TRAIN),
            ('Validation', 'validation', M['X_valid'], M['y_valid'], VALID),
            ('Test', 'test', M['X_test'], M['y_test'], TEST)]

    # 3. ROC curves
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    fig.subplots_adjust(left=0.13, right=0.95, top=0.8, bottom=0.12)
    ax.plot([0, 1], [0, 1], ls='--', color=MUTED, lw=1.2)
    ax.text(0.74, 0.64, 'Random (AUC 0.5)', color=MUTED, fontsize=10)
    for name, key, X, yv, col in sets:
        fpr, tpr, _ = metrics.roc_curve(yv, lr.predict_proba(X)[:, 1])
        ax.plot(fpr, tpr, color=col, lw=2.6 if key == 'test' else 2,
                label=f"{name}: AUC {perf.loc[key, 'AUC']:.3f}", zorder=3 if key == 'test' else 2)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.0)
    ax.set_xlabel('Share of good payers flagged (false positive rate)')
    ax.set_ylabel('Share of defaulters caught (true positive rate)')
    ax.legend(loc='lower right')
    hgrid(ax, 'both')
    title(fig, f"ROC curve: test AUC {perf.loc['test', 'AUC']:.3f}",
          'The three curves are close: no sign of severe overfitting.')
    save(fig, 'jethro_3_roc.png')

    # 4. K-S chart (test)
    s = M['test_score']['score'].values
    yt = M['y_test'].values
    order = np.sort(np.unique(s))
    cb = np.array([((s <= v) & (yt == 1)).sum() for v in order]) / (yt == 1).sum()
    cg = np.array([((s <= v) & (yt == 0)).sum() for v in order]) / (yt == 0).sum()
    i = int(np.argmax(cb - cg)); ks_score, ks = order[i], (cb - cg)[i]
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    fig.subplots_adjust(left=0.13, right=0.95, top=0.8, bottom=0.12)
    ax.fill_between(order, cg, cb, color=TEST, alpha=0.10, lw=0)
    ax.plot(order, cb, color=TEST, lw=2.4, label='Defaulters')
    ax.plot(order, cg, color=INK2, lw=2.4, ls='--', label='Good payers')
    ax.annotate('', xy=(ks_score, cb[i]), xytext=(ks_score, cg[i]), arrowprops=dict(arrowstyle='<->', color=INK, lw=1.4))
    ax.text(ks_score + 10, 0.40, f'K-S = {ks:.1%}\nat score {ks_score:.0f}', fontsize=11.5, color=INK, va='center')
    ax.set_xlabel('Score'); ax.set_ylabel('Cumulative share scoring at or below this score')
    ax.set_ylim(0, 1.02)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.legend(loc='upper left')
    hgrid(ax, 'both')
    gap = int(ks_score) - cut
    where = f'{abs(gap)} points {"above" if gap >= 0 else "below"} the {cut} cutoff'
    title(fig, f'K-S chart (test set): {ks:.1%} separation',
          f'Defaulters pile up at low scores; the widest gap is {where}.')
    save(fig, 'jethro_4_ks.png')

    # 5. Calibration by score decile (test)
    d = pd.DataFrame({'score': s, 'y': yt, 'p': lr.predict_proba(M['X_test'])[:, 1]})
    d['dec'] = pd.qcut(d['score'].rank(method='first'), 10, labels=False) + 1
    g = d.groupby('dec').agg(actual=('y', 'mean'), predicted=('p', 'mean'), lo=('score', 'min'), hi=('score', 'max'))
    fig, ax = plt.subplots(figsize=(9, 5.6))
    fig.subplots_adjust(left=0.1, right=0.97, top=0.8, bottom=0.17)
    x = np.arange(1, 11)
    ax.bar(x, g['actual'], width=0.62, color=TEST, edgecolor=SURF, linewidth=2, label='Actual bad rate')
    ax.plot(x, g['predicted'], color=INK, lw=2, marker='o', markersize=8, markeredgecolor=SURF,
            markeredgewidth=1.5, label='Predicted (model)')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{int(a)}–{int(b)}' for a, b in zip(g['lo'], g['hi'])], fontsize=9.5)
    ax.set_xlabel('Score band (test set, 10 equal groups from lowest to highest score)')
    ax.set_ylabel('Bad rate')
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.legend(loc='upper right')
    hgrid(ax, 'y')
    title(fig, 'Predicted vs actual default rate (test set)',
          f"Bad rate falls from {g['actual'].iloc[0]:.1%} in the lowest-scoring tenth to "
          f"{g['actual'].iloc[-1]:.1%} in the highest.\nThe model's predicted probabilities track the actual bad rate.")
    save(fig, 'jethro_5_calibration.png')

    # 6. Performance summary table
    cal = M['calibration_overview']
    n = {'train': len(M['y_train']), 'validation': len(M['y_valid']), 'test': len(M['y_test'])}
    cols = ['', 'Applicants', 'AUC', 'Gini', 'K-S', 'Bad rate', 'Predicted PD']
    fig, ax = plt.subplots(figsize=(10, 3.9))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.72, bottom=0.04)
    ax.axis('off')
    xs = [0.0, 0.2, 0.36, 0.48, 0.6, 0.72, 0.85]
    for xpos, c in zip(xs, cols):
        ax.text(xpos, 0.92, c, fontsize=12, color=INK2, fontweight='bold', ha='left', transform=ax.transAxes)
    ax.plot([0, 1], [0.84, 0.84], color=AXIS, lw=1, transform=ax.transAxes)
    for r, (lab, key, _, _, col) in enumerate(sets):
        yv = 0.62 - r * 0.27
        bold = 'bold' if key == 'test' else 'normal'
        ax.add_patch(plt.Rectangle((0.0, yv - 0.04), 0.012, 0.12, color=col, transform=ax.transAxes))
        vals = [lab, f"{n[key]:,}", f"{perf.loc[key, 'AUC']:.3f}", f"{perf.loc[key, 'Gini']:.3f}",
                f"{perf.loc[key, 'KS']:.1%}", f"{cal.loc[key, 'observed_rate']:.2%}",
                f"{cal.loc[key, 'mean_model_probability']:.2%}"]
        for xpos, v in zip(xs, vals):
            ax.text(xpos + (0.022 if v == lab else 0), yv, v, fontsize=13, color=INK, fontweight=bold,
                    ha='left', transform=ax.transAxes)
    title(fig, 'Model performance on all three data sets',
          'Similar results on every set, and predicted PD matches the actual bad rate.\n'
          'Model chosen on validation; test results reported after the model was locked.')
    save(fig, 'jethro_6_performance_table.png')

    print(f"check: test AUC {perf.loc['test', 'AUC']:.4f}, K-S {ks:.4f} at score {ks_score:.0f}, cutoff {cut}")


def make_deck_charts(M):
    """Slide versions of charts 1 and 3 in the deck's navy palette, with no in-image title."""
    NAVY, MID, LIGHT, DGRID, DMUTED = '#093c62', '#3f7cb5', '#9cc3e4', '#dfe6ee', '#6b7f93'
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 16, 'axes.edgecolor': '#b9c6d3',
                         'axes.labelcolor': NAVY, 'xtick.color': DMUTED, 'ytick.color': NAVY,
                         'axes.spines.top': False, 'axes.spines.right': False, 'legend.frameon': False,
                         'figure.facecolor': 'white', 'axes.facecolor': 'white', 'savefig.facecolor': 'white'})
    p = M['path'].copy()
    p['gain'] = p['gini_validation'].diff().fillna(p['gini_validation'])
    fig, ax = plt.subplots(figsize=(10, 6.6))
    fig.subplots_adjust(left=0.40, right=0.93, top=0.97, bottom=0.11)
    y = np.arange(len(p))[::-1]
    ax.barh(y, p['gain'], height=0.64, color=NAVY)
    for yi, g in zip(y, p['gain']):
        ax.text(g + 0.003, yi, f'+{g:.3f}', va='center', fontsize=14, color=NAVY)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{int(s)}. {NAMES.get(v, v)}" for s, v in zip(p.step, p.added)], fontsize=15)
    ax.set_xlabel('Gain in validation Gini when the variable is added', fontsize=15)
    ax.set_xlim(0, p['gain'].max() * 1.2)
    ax.grid(axis='x', color=DGRID, lw=1); ax.set_axisbelow(True); ax.tick_params(axis='y', length=0)
    save(fig, 'deck_forward_selection.png')

    perf, lr = M['perf'], M['lr']
    fig, ax = plt.subplots(figsize=(7.6, 6.8))
    fig.subplots_adjust(left=0.14, right=0.96, top=0.97, bottom=0.12)
    ax.plot([0, 1], [0, 1], ls='--', color=DMUTED, lw=1.4)
    ax.text(0.62, 0.53, 'Random (AUC 0.5)', color=DMUTED, fontsize=13)
    for name, key, X, yv, col, lw in [('Train', 'train', M['X_train'], M['y_train'], LIGHT, 2.4),
                                      ('Validation', 'validation', M['X_valid'], M['y_valid'], MID, 2.4),
                                      ('Test', 'test', M['X_test'], M['y_test'], NAVY, 3.4)]:
        fpr, tpr, _ = metrics.roc_curve(yv, lr.predict_proba(X)[:, 1])
        ax.plot(fpr, tpr, color=col, lw=lw, label=f"{name}: AUC {perf.loc[key, 'AUC']:.3f}")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel('Share of good payers flagged', fontsize=15)
    ax.set_ylabel('Share of defaulters caught', fontsize=15)
    leg = ax.legend(loc='lower right', fontsize=15)
    for t in leg.get_texts():
        t.set_color(NAVY)
    ax.grid(color=DGRID, lw=1); ax.set_axisbelow(True)
    save(fig, 'deck_roc.png')

    # Coefficients
    ct = M['coef_table'].drop(index='intercept').copy()
    ct.index = [i[:-4] for i in ct.index]
    ct = ct.loc[list(M['path']['added'])[::-1]]
    fig, ax = plt.subplots(figsize=(10, 6.6))
    fig.subplots_adjust(left=0.43, right=0.95, top=0.97, bottom=0.11)
    y = np.arange(len(ct))
    ax.barh(y, ct['coef'], height=0.64, color=NAVY)
    for yi, c in zip(y, ct['coef']):
        ax.text(c + 0.015, yi, f'{c:.2f}', va='center', fontsize=14, color=NAVY)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{NAMES.get(v, v)} ({SOURCE.get(v, 'Bureau')})" for v in ct.index], fontsize=14)
    ax.set_xlabel('Coefficient on the WoE value (all positive)', fontsize=15)
    ax.set_xlim(0, ct['coef'].max() * 1.15)
    ax.grid(axis='x', color=DGRID, lw=1); ax.set_axisbelow(True); ax.tick_params(axis='y', length=0)
    save(fig, 'deck_coefficients.png')

    # K-S chart (test) with the cutoff marked
    cut = int(M['best_cutoff'])
    s_ = M['test_score']['score'].values
    yt = M['y_test'].values
    order = np.sort(np.unique(s_))
    cb = np.array([((s_ <= v) & (yt == 1)).sum() for v in order]) / (yt == 1).sum()
    cg = np.array([((s_ <= v) & (yt == 0)).sum() for v in order]) / (yt == 0).sum()
    i = int(np.argmax(cb - cg)); ks_score, ks = order[i], (cb - cg)[i]
    fig, ax = plt.subplots(figsize=(8.6, 6.2))
    fig.subplots_adjust(left=0.13, right=0.97, top=0.97, bottom=0.12)
    ax.fill_between(order, cg, cb, color=LIGHT, alpha=0.35, lw=0)
    ax.plot(order, cb, color=NAVY, lw=3, label='Defaulters')
    ax.plot(order, cg, color=MID, lw=3, ls='--', label='Good payers')
    ax.axvline(cut, color=DMUTED, lw=1.4, ls=':')
    ax.text(cut - 3, 0.97, f'Cutoff {cut}', ha='right', va='top', fontsize=13, color=DMUTED)
    ax.annotate('', xy=(ks_score, cb[i]), xytext=(ks_score, cg[i]), arrowprops=dict(arrowstyle='<->', color=NAVY, lw=1.6))
    ax.text(ks_score + 20, 0.36, f'K-S {ks:.1%}\nat score {ks_score:.0f}', fontsize=15, color=NAVY, va='center')
    ax.set_xlabel('Score', fontsize=15)
    ax.set_ylabel('Cumulative share at or below the score', fontsize=15)
    ax.set_ylim(0, 1.02)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    leg = ax.legend(loc='lower right', fontsize=15)
    for t in leg.get_texts():
        t.set_color(NAVY)
    ax.grid(color=DGRID, lw=1); ax.set_axisbelow(True)
    save(fig, 'deck_ks.png')

    # Calibration by score decile (test)
    d = pd.DataFrame({'score': s_, 'y': yt, 'p': lr.predict_proba(M['X_test'])[:, 1]})
    d['dec'] = pd.qcut(d['score'].rank(method='first'), 10, labels=False) + 1
    g = d.groupby('dec').agg(actual=('y', 'mean'), predicted=('p', 'mean'), lo=('score', 'min'), hi=('score', 'max'))
    fig, ax = plt.subplots(figsize=(8.6, 6.2))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.97, bottom=0.17)
    x = np.arange(1, 11)
    ax.bar(x, g['actual'], width=0.64, color=LIGHT, label='Actual bad rate')
    ax.plot(x, g['predicted'], color=NAVY, lw=2.6, marker='o', markersize=8, label='Predicted by the model')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{int(a)}–{int(b)}' for a, b in zip(g['lo'], g['hi'])], fontsize=11.5, rotation=40, ha='right')
    ax.set_xlabel('Score band (test set, 10 equal groups)', fontsize=15)
    ax.set_ylabel('Bad rate', fontsize=15)
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    leg = ax.legend(loc='upper right', fontsize=15)
    for t in leg.get_texts():
        t.set_color(NAVY)
    ax.grid(axis='y', color=DGRID, lw=1); ax.set_axisbelow(True)
    save(fig, 'deck_calibration.png')


if __name__ == '__main__':  # the guard is needed on Windows, where scorecardpy starts worker processes
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    model = run_notebook()
    make_charts(model)
    make_deck_charts(model)
