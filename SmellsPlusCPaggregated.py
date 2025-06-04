# import os
# import pandas as pd
# import numpy as np

# # Comprehensive smell column mapping
# SMELL_COLUMNS = {
#     'Assertion Roulette': 'Assertion Roulette',
#     'Conditional Test Logic': 'Conditional Test Logic',
#     'Constructor Initialization': 'Constructor Initialization',
#     'Default Test': 'Default Test',
#     'Duplicate Assertion': 'Duplicate Assertion',
#     'Empty Test': 'Empty Test',
#     'Exception Handling': 'Exception Handling',
#     'General Fixture': 'General Fixture',
#     'Ignored Test': 'Ignored Test',
#     'Lack of Cohesion of Test Cases': 'Lack of Cohesion of Test Cases',
#     'Magic Number Test': 'Magic Number Test',
#     'Obscure In-Line Setup': 'Obscure In-Line Setup',
#     'Redundant Assertion': 'Redundant Assertion',
#     'Redundant Print': 'Redundant Print',
#     'Sleepy Test': 'Sleepy Test',
#     'Suboptimal Assert': 'Suboptimal Assert',
#     'Test Maverick': 'Test Maverick',
#     'Unknown Test': 'Unknown Test',
#     'Total TS': 'Total TS'
# }

# def parse_and_aggregate_csvs(input_dir, output_path):
#     all_dfs = []

#     for filename in os.listdir(input_dir):
#         if filename.endswith('.csv') and filename != 'aggregate_summary.csv':
#             filepath = os.path.join(input_dir, filename)
            
#             # Read CSV 
#             df = pd.read_csv(filepath, dtype=str, na_filter=False)
            
#             # Rename and zero-fill columns
#             for old_col, new_col in SMELL_COLUMNS.items():
#                 if old_col in df.columns:
#                     df[new_col] = df[old_col].replace('', '0')
#                     df[new_col] = pd.to_numeric(df[new_col], errors='coerce').fillna(0)
#                 else:
#                     df[new_col] = 0
            
#             # Add project name column
#             df['Project'] = filename.replace('.csv', '')
            
#             all_dfs.append(df)

#     if all_dfs:
#         # Concatenate dataframes
#         aggregate_df = pd.concat(all_dfs, ignore_index=True)
        
#         # Select only the smell columns and project
#         smell_columns = list(SMELL_COLUMNS.values())
#         project_summary = aggregate_df.groupby('Project')[smell_columns].sum().reset_index()
        
#         # Save aggregate and summary CSVs
#         aggregate_df.to_csv(output_path, index=False)
#         project_summary.to_csv(os.path.join(os.path.dirname(output_path), 'project_smell_summary.csv'), index=False)
        
#         print("Aggregation complete:")
#         print(project_summary)
#     else:
#         print("No CSVs found to merge")

# # Paths
# input_dir = "/home/iit/Downloads/Thesis/Data/SmellsPlusCP"
# output_path = os.path.join(input_dir, 'aggregate_summary.csv')

# # Aggregate CSVs
# parse_and_aggregate_csvs(input_dir, output_path)





import pandas as pd
import numpy as np

# Read CSV
df = pd.read_csv('/home/iit/Downloads/Thesis/Data/aggregate_summary.csv')

# Replace blank cells with 0
df = df.replace(r'^\s*$', 0, regex=True)

# Convert columns to numeric, coercing any remaining non-numeric values to 0
numeric_columns = df.select_dtypes(include=[object]).columns
df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce').fillna(0)

# Save updated CSV
df.to_csv('/home/iit/Downloads/Thesis/Data/aggregate_summary_zero_filled.csv', index=False)

print("CSV processed. Zero-filled values saved.")