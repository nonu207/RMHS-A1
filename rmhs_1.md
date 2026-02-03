# Documentation: rmhs_1.py

This document explains what the script [rmhs_1.py](rmhs_1.py) does, and details each method used for tabulation and plotting (what it uses, inputs, and outputs).

## Summary
- Script: [rmhs_1.py](rmhs_1.py)
- Purpose: Load a household survey CSV, filter for Odisha regions, perform cleaning and feature engineering, produce summary tables and save them to `odisha_analysis_tables.txt`, and generate 6 plot PNG files.
- Dependencies: `pandas`, `numpy`, `matplotlib`, `seaborn`.

## Data loading & filtering
- The script attempts to read `dataset_assignment1.csv` using `pd.read_csv`.
- It filters rows where `NSS_Region` is in [211, 212, 213] to produce `odisha_df` (Odisha sample).

Files produced:
- Tables: [odisha_analysis_tables.txt](odisha_analysis_tables.txt)
- Graphs: `graph1_prevalence_econ_sector.png`, `graph2_seeking_rate.png`, `graph3_expenditure_boxplot.png`, `graph4_prevalence_social_group.png`, `graph5_prevalence_family_size.png`, `graph6_source_finance.png` (all saved in the working directory).

## Data cleaning & feature engineering (sections A–G in code)

**A. Handling Missing Values**
- Columns `prop_spells_treated` and `Major_source_of_finance` are filled with 0 via `DataFrame.fillna(0)`.

**B. [CRITICAL FIX] Filter Invalid Expenditure & Create Economic Status**
- Step 1: Remove rows with `Household_usual_consumer_expendi` <= 100 (treated as unrealistic) creating `valid_exp_df`.
- Step 2: Compute 99th percentile (`exp_cap`) on the valid data and cap expenditure values using `np.where`, storing result in `Household_usual_consumer_expendi_clean`.
- Step 3: Create quartiles using `pd.qcut` on the capped, valid expenditures with labels `['Poorest', 'Lower Middle', 'Upper Middle', 'Richest']` stored in `Economic_Status`.
- The script then replaces `odisha_df` with `valid_exp_df`, so all subsequent analysis uses the cleaned sample.

**C. Sector (Rural vs Urban)**
- Maps numeric `Sector` codes (1=Rural, 2=Urban) to `Sector_Label` via `Series.map`.

**D. Family Size Bins**
- Uses `pd.cut` on `Household_size` with bins [0, 3, 6, 20] giving labels `'Small (1-3)'`, `'Medium (4-6)'`, `'Large (7+)'` stored in `Family_Size_Bin`.

**E. [CLEANING] Social Group Label**
- Filters `Social_group` to only keep standard codes [1, 2, 3, 9] using `.isin()`, removing rows with undefined/nonstandard codes.
- Maps remaining codes to labels: 1=ST, 2=SC, 3=OBC, 9=Others, stored in `Social_Group_Label`.
- Prints the new sample size after this cleaning step.

**F. Source of Finance Label**
- Maps `Major_source_of_finance` codes to human-readable labels: 0=None, 1=Income/Savings, 2=Borrowings, 3=Sale of Assets, 4=Friends/Family, 9=Other, stored in `Finance_Label`.

**G. Define Prevalence**
- Creates `Has_Ailment` binary indicator (1 if `spells_count` > 0 else 0) via `apply(lambda x: 1 if x > 0 else 0)`.
- Creates `sick_households` subset where `Has_Ailment == 1` (used in treatment- and expenditure-related analyses).

## Tabulation methods and tables

Helper function: `create_summary_table(group_col)`
- What it does: For a group column (e.g., `Economic_Status`) it computes two metrics:
  - `Prevalence (%)`: group-wise mean of `Has_Ailment` multiplied by 100 (i.e., share of households with any ailment in that group).
  - `Treatment Rate (%)`: among `sick_households`, group-wise mean of `prop_spells_treated` multiplied by 100 (average % of spells treated) — uses `sick_households` so only households with ailments are considered.
- Implementation details: uses `DataFrame.groupby(group_col, observed=True)` and `.mean()` to compute proportions; returns a `pd.DataFrame` with the two columns.

Tables generated in the script:
- `table1` — Analysis by `Economic_Status` (from `create_summary_table('Economic_Status')`).
- `table2` — Analysis by `Sector_Label` (Rural vs Urban).
- `table3` — Analysis by `Social_Group_Label`.
- `table4` — Analysis by `Family_Size_Bin`.
- `table5` — Cross-tabulation of `sick_households` by `Economic_Status` (rows) vs `Finance_Label` (columns): uses `pd.crosstab(..., normalize='index') * 100` so each row sums to 100 (shows distribution of financing sources within each economic status).

Note: In the code the written header for table 5 is `"--- TABLE 5: SOURCE OF FINANCE (% of Sick HH) ---"`, i.e., the crosstab shows percent distribution of sources among sick households within each economic status.

Writing tables to file:
- The script writes formatted text into `odisha_analysis_tables.txt` and uses `DataFrame.round(2).to_string()` to write human-readable tables (rounded to 2 decimals). The file includes headers for each table.

## Plotting methods — file-by-file explanation

**Global settings:** `sns.set_theme(style="whitegrid")` sets Seaborn theme for consistent styling.

**Note:** After the cleaning steps (particularly section E), the script prints the new sample size ("Cleaned Social Groups. New Sample Size: ...") so all outputs and plots reflect the filtered sample.

- Graph 1: `graph1_prevalence_econ_sector.png`
  - Plot type: `sns.barplot`
  - Data: `odisha_df`
  - x: `Economic_Status`, y: `Has_Ailment` (proportion), hue: `Sector_Label` (Rural/Urban)
  - Palette: `Blues_d`, `errorbar=None` (no error bars plotted)
  - Notes: Barplot shows prevalence (proportion of households with ailments) across economic quartiles, split by sector.

- Graph 2: `graph2_seeking_rate.png`
  - Plot type: `sns.barplot` using precomputed `table1` (treatment rates per economic status).
  - x: `table1.index` (Economic Status categories), y:`table1['Treatment Rate (%)']`
  - Palette: `Greens_d`, `hue=table1.index` used but `legend=False` (keeps colors distinct but no legend)
  - Notes: Visualizes average % of spells treated by income group (treatment-seeking behavior).

- Graph 3: `graph3_expenditure_boxplot.png`
  - Plot type: `sns.boxplot`
  - Data: `spenders` — subset of `sick_households` with `outpatient_expenditure_total_Rs` > 0.
  - x: `Economic_Status`, y: `outpatient_expenditure_total_Rs`, hue: `Economic_Status`
  - Palette: `Set2`, `legend=False`
  - Scale: `plt.yscale('log')` applied to show expenditures on a log scale (helps with skew and outliers).
  - Notes: Boxplots show medical expenditure distribution per economic status. The script subsets `spenders = sick_households[sick_households['outpatient_expenditure_total_Rs'] > 0]` before plotting to exclude zero-expenditure households.

- Graph 4: `graph4_prevalence_social_group.png`
  - Plot type: `sns.barplot`
  - Data: `odisha_df` (already filtered to valid social groups in section E)
  - x: `Social_Group_Label`, y: `Has_Ailment` (proportion), hue: `Social_Group_Label` (legend disabled)
  - Palette: `viridis`, estimator: `np.mean` (explicitly set), `errorbar=None`
  - Notes: Compares prevalence across social groups (ST, SC, OBC, Others only). The code comment marks this as "Cleaned" since invalid social group codes were already filtered out.

- Graph 5: `graph5_prevalence_family_size.png`
  - Plot type: `sns.barplot`
  - Data: `odisha_df`
  - x: `Family_Size_Bin`, y: `Has_Ailment`, hue: `Family_Size_Bin`, palette: `coolwarm`, estimator: `np.mean`, `errorbar=None`.
  - Notes: Prevalence by household-size categories.

- Graph 6: `graph6_source_finance.png`
  - Plot type: `sns.countplot`
  - Data: `finance_data` — `sick_households` excluding `Finance_Label == 'None'`.
  - x: `Economic_Status`, hue: `Finance_Label`, palette: `muted`.
  - Notes: Shows counts (not percentages) of financing sources used by sick households within each economic status. Legend is placed outside the plot with `bbox_to_anchor`.

Common plotting operations used across graphs:
- `plt.figure(figsize=(..., ...))` sets output size.
- `sns.*` high-level plotting functions (barplot, boxplot, countplot) handle aggregation/estimation internally; sometimes `estimator=np.mean` is explicitly passed to make intent clear.
- `plt.tight_layout()` to prevent layout clipping.
- `plt.savefig(filename, dpi=150)` to write high-resolution PNG files.
- `plt.close()` to free the figure and avoid overlapping figures in subsequent plots.

## Practical notes & suggestions
- Reproducibility: The script uses no random seeds (not needed for deterministic bar/box plots), but consider setting figure DPI or style globally if you need consistent appearance across runs.
- Consistency: Graph 2 uses precomputed table values (ensures the same aggregation as table output). Other barplots use `odisha_df` directly; ensure the same estimator (mean) is assumed when comparing table vs plot.
- Errorbars: Many barplots set `errorbar=None` — if you want confidence intervals, remove `errorbar=None` or pass `ci`/`errorbar` parameters.
- Large values: Expenditure plot uses a log scale; communicate this clearly on the axis labels when presenting (e.g., add text or annotate that y-scale is log-transformed).

## How to run
From the directory containing the files, run:

```bash
python rmhs_1.py
```

This will read `dataset_assignment1.csv` in the working directory and create `odisha_analysis_tables.txt` and the graph PNG files.

---
If you want, I can:
- add inline comments in `rmhs_1.py` linking to sections of this documentation
- convert numeric labels to `CategoricalDtype` for explicit ordering
- add CLI args to change output folder or figure DPI

Created on: February 3, 2026
