
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- 1. Load Data ---
try:
    df = pd.read_csv('dataset_assignment1.csv')
    print("✅ Data loaded successfully.")
except FileNotFoundError:
    print("❌ Error: 'dataset_assignment1.csv' not found.")
    exit()

# --- 2. Filter for Odisha ---
# Odisha NSS Regions: 211, 212, 213
odisha_df = df[df['NSS_Region'].isin([211, 212, 213])].copy()
print(f"✅ Filtered for Odisha. Sample Size: {len(odisha_df)}")

# --- 3. Data Cleaning & Feature Engineering ---

# A. Handling Missing Values
cols_to_fill = ['prop_spells_treated', 'Major_source_of_finance']
odisha_df[cols_to_fill] = odisha_df[cols_to_fill].fillna(0)

# B. [CRITICAL FIX] Filter Invalid Expenditure & Create Economic Status
# 1. Remove rows with unrealistic expenditure (< 100) to fix "Lower Middle" issue
valid_exp_df = odisha_df[odisha_df['Household_usual_consumer_expendi'] > 100].copy()

# 2. Re-calculate Cap on valid data
exp_cap = valid_exp_df['Household_usual_consumer_expendi'].quantile(0.99)
valid_exp_df['Household_usual_consumer_expendi_clean'] = np.where(
    valid_exp_df['Household_usual_consumer_expendi'] > exp_cap,
    exp_cap,
    valid_exp_df['Household_usual_consumer_expendi']
)

# 3. Create Quartiles (Economic Status)
valid_exp_df['Economic_Status'] = pd.qcut(
    valid_exp_df['Household_usual_consumer_expendi_clean'], 
    q=4, 
    labels=['Poorest', 'Lower Middle', 'Upper Middle', 'Richest']
)

# Update the main dataframe
odisha_df = valid_exp_df

# C. Sector (Rural vs Urban)
odisha_df['Sector_Label'] = odisha_df['Sector'].map({1: 'Rural', 2: 'Urban'})

# D. Family Size Bins
odisha_df['Family_Size_Bin'] = pd.cut(
    odisha_df['Household_size'], 
    bins=[0, 3, 6, 20], 
    labels=['Small (1-3)', 'Medium (4-6)', 'Large (7+)']
)

# E. [CLEANING] Social Group Label
# Standard Codes: 1=ST, 2=SC, 3=OBC, 9=Others
# We FILTER OUT any rows with undefined codes (like 4, 5, 10) to strictly clean the data.
valid_social_groups = [1, 2, 3, 9]
odisha_df = odisha_df[odisha_df['Social_group'].isin(valid_social_groups)].copy()

social_map = {1: 'ST', 2: 'SC', 3: 'OBC', 9: 'Others'}
odisha_df['Social_Group_Label'] = odisha_df['Social_group'].map(social_map)
print(f"✅ Cleaned Social Groups. New Sample Size: {len(odisha_df)}")

# F. Source of Finance Label
finance_map = {0: 'None', 1: 'Income/Savings', 2: 'Borrowings', 3: 'Sale of Assets', 4: 'Friends/Family', 9: 'Other'}
odisha_df['Finance_Label'] = odisha_df['Major_source_of_finance'].map(finance_map).fillna('Other')

# G. Define Prevalence
odisha_df['Has_Ailment'] = odisha_df['spells_count'].apply(lambda x: 1 if x > 0 else 0)
sick_households = odisha_df[odisha_df['Has_Ailment'] == 1].copy()

# --- 4. Generate Tables ---
print("\nGenerating summary tables...")

def create_summary_table(group_col):
    prev = odisha_df.groupby(group_col, observed=True)['Has_Ailment'].mean() * 100
    seek = sick_households.groupby(group_col, observed=True)['prop_spells_treated'].mean() * 100
    return pd.DataFrame({'Prevalence (%)': prev, 'Treatment Rate (%)': seek})

# Create all tables
table1 = create_summary_table('Economic_Status')
table2 = create_summary_table('Sector_Label')
table3 = create_summary_table('Social_Group_Label')
table4 = create_summary_table('Family_Size_Bin')
table5 = pd.crosstab(sick_households['Economic_Status'], sick_households['Finance_Label'], normalize='index') * 100

# Save Tables to File
output_file = 'odisha_analysis_tables.txt'
with open(output_file, 'w') as f:
    f.write("==================================================\n")
    f.write("      ODISHA HEALTHCARE ANALYSIS TABLES\n")
    f.write("==================================================\n\n")
    f.write("--- TABLE 1: ANALYSIS BY ECONOMIC STATUS ---\n" + table1.round(2).to_string() + "\n\n")
    f.write("--- TABLE 2: ANALYSIS BY SECTOR (RURAL/URBAN) ---\n" + table2.round(2).to_string() + "\n\n")
    f.write("--- TABLE 3: ANALYSIS BY SOCIAL GROUP ---\n" + table3.round(2).to_string() + "\n\n")
    f.write("--- TABLE 4: ANALYSIS BY FAMILY SIZE ---\n" + table4.round(2).to_string() + "\n\n")
    f.write("--- TABLE 5: SOURCE OF FINANCE (% of Sick HH) ---\n" + table5.round(2).to_string() + "\n\n")

print(f"✅ Tables saved to '{output_file}'")

# --- 5. Generate and Save Individual Graphs ---
sns.set_theme(style="whitegrid")
print("Generating separate graph files...")

# Graph 1: Prevalence by Economic Status & Sector
plt.figure(figsize=(10, 6))
sns.barplot(data=odisha_df, x='Economic_Status', y='Has_Ailment', hue='Sector_Label', palette="Blues_d", errorbar=None)
plt.title('Prevalence of Ailment: Economic Status & Sector')
plt.ylabel('Prevalence (Proportion)')
plt.tight_layout()
plt.savefig("graph1_prevalence_econ_sector.png", dpi=150)
plt.close()
print("Saved: graph1_prevalence_econ_sector.png")

# Graph 2: Treatment Seeking Behavior
plt.figure(figsize=(10, 6))
sns.barplot(x=table1.index, y=table1['Treatment Rate (%)'], palette="Greens_d", hue=table1.index, legend=False)
plt.title('Treatment Seeking Rate by Income')
plt.ylabel('Avg % of Spells Treated')
plt.xlabel('Economic Status')
plt.tight_layout()
plt.savefig("graph2_seeking_rate.png", dpi=150)
plt.close()
print("Saved: graph2_seeking_rate.png")

# Graph 3: Medical Expenditure Distribution (CHANGED TO HISTOGRAM + KDE)
plt.figure(figsize=(10, 6))
spenders = sick_households[sick_households['outpatient_expenditure_total_Rs'] > 0]
#  - This visualizes the skewness
sns.histplot(data=spenders, x='outpatient_expenditure_total_Rs', kde=True, log_scale=True, color="teal", element="step")
plt.title('Distribution of Medical Expenditure (Histogram + KDE)\nHigh Right Skewness Visible', fontsize=12)
plt.ylabel('Frequency (Count of Households)')
plt.xlabel('Expenditure (INR) - Log Scale')
plt.tight_layout()
plt.savefig("graph3_expenditure_histogram_kde.png", dpi=150)
plt.close()
print("Saved: graph3_expenditure_histogram_kde.png (Replaced Boxplot with Histogram+KDE)")

# Graph 4: Prevalence by Social Group (Cleaned)
plt.figure(figsize=(10, 6))
sns.barplot(data=odisha_df, x='Social_Group_Label', y='Has_Ailment', palette="viridis", estimator=np.mean, errorbar=None, hue='Social_Group_Label', legend=False)
plt.title('Prevalence by Social Group')
plt.ylabel('Prevalence (Proportion)')
plt.xlabel('Social Group')
plt.tight_layout()
plt.savefig("graph4_prevalence_social_group.png", dpi=150)
plt.close()
print("Saved: graph4_prevalence_social_group.png")

# Graph 5: Prevalence by Family Size
plt.figure(figsize=(10, 6))
sns.barplot(data=odisha_df, x='Family_Size_Bin', y='Has_Ailment', palette="coolwarm", estimator=np.mean, errorbar=None, hue='Family_Size_Bin', legend=False)
plt.title('Prevalence by Family Size')
plt.ylabel('Prevalence (Proportion)')
plt.tight_layout()
plt.savefig("graph5_prevalence_family_size.png", dpi=150)
plt.close()
print("Saved: graph5_prevalence_family_size.png")

# Graph 6: Source of Finance
plt.figure(figsize=(12, 7))
finance_data = sick_households[sick_households['Finance_Label'] != 'None']
sns.countplot(data=finance_data, x='Economic_Status', hue='Finance_Label', palette="muted")
plt.title('Source of Finance by Economic Status')
plt.ylabel('Count of Households')
plt.legend(title='Source', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("graph6_source_finance.png", dpi=150)
plt.close()
print("Saved: graph6_source_finance.png")

print("\n✅ All graphs generated and saved successfully.")