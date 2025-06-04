# import pandas as pd
# import os

# def extract_filename(path):
#     """Safely extract filename, handling potential NaN values."""
#     if pd.isna(path):
#         return None
#     return os.path.basename(str(path))

# def merge_csv_files(cp_file, smell_file, output_path):
#     # Read CSV files
#     cp_df = pd.read_csv(cp_file)
#     smell_df = pd.read_csv(smell_file)

#     # Extract filenames for test files, converting to strings
#     cp_df['test_filename'] = cp_df['TestFile'].apply(extract_filename)
#     smell_df['test_filename'] = smell_df['File Path'].apply(extract_filename)

#     # Merge on test filenames, dropping rows with NaN
#     merged_df = cp_df.merge(smell_df, on='test_filename', how='inner')
#     merged_df = merged_df.dropna(subset=['test_filename'])

#     # Save merged dataframe
#     merged_df.to_csv(output_path, index=False)
#     print(f"Merged rows: {len(merged_df)}")

# # Paths
# cp_file = "/home/siam/Desktop/volume1/MS_Papers_Arif/Data/CP_Summary/aerospike-client-python_transformed.csv"
# smell_file = "/home/siam/Desktop/volume1/MS_Papers_Arif/Data/AggregatedSmellsCSV/aerospike-client-python_csv/Summary/smell_summary.csv"
# output_dir = "/home/siam/Desktop/volume1/MS_Papers_Arif/Data/SmellsPlusCP"
# output_file = "aerospike-client-python.csv"
# output_path = os.path.join(output_dir, output_file)

# # Ensure output directory exists
# os.makedirs(output_dir, exist_ok=True)

# # Merge files
# merge_csv_files(cp_file, smell_file, output_path)





import os
import pandas as pd

def extract_filename(path):
    """Safely extract filename."""
    if pd.isna(path):
        return None
    return os.path.basename(str(path))

def merge_project_csvs(cp_dir, smell_dir, output_dir):
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)

    # Logging for tracking
    merge_log = []

    # Iterate through CP transformed CSV files
    for cp_filename in os.listdir(cp_dir):
        if cp_filename.endswith('_transformed.csv'):
            # Extract project name
            project_name = cp_filename.replace('_transformed.csv', '')
            
            # Construct full paths
            cp_file = os.path.join(cp_dir, cp_filename)
            smell_dir_path = os.path.join(smell_dir, f"{project_name}_csv/Summary")
            
            # Check if smell directory exists
            if not os.path.exists(smell_dir_path):
                print(f"Skipping {project_name}: Smell directory not found")
                continue

            # Iterate through smell summary files in the project directory
            for smell_filename in os.listdir(smell_dir_path):
                if smell_filename == 'smell_summary.csv':
                    smell_file = os.path.join(smell_dir_path, smell_filename)
                    output_file = os.path.join(output_dir, f"{project_name}.csv")

                    # Read CSV files
                    cp_df = pd.read_csv(cp_file)
                    smell_df = pd.read_csv(smell_file)

                    # Extract filenames for test files
                    cp_df['test_filename'] = cp_df['TestFile'].apply(extract_filename)
                    smell_df['test_filename'] = smell_df['File Path'].apply(extract_filename)

                    # Merge on test filenames
                    merged_df = cp_df.merge(smell_df, on='test_filename', how='inner')
                    merged_df = merged_df.dropna(subset=['test_filename'])

                    # Save merged dataframe
                    merged_df.to_csv(output_file, index=False)
                    
                    # Log merge details
                    merge_log.append({
                        'Project': project_name,
                        'Total Merged Rows': len(merged_df)
                    })
                    print(f"{project_name}: Merged {len(merged_df)} rows")

    # Optional: Create a log file
    log_df = pd.DataFrame(merge_log)
    log_df.to_csv(os.path.join(output_dir, 'merge_log.csv'), index=False)

# Directories
cp_dir = "/home/siam/Desktop/volume1/MS_Papers_Arif/Data/CP/CP_Summary"
smell_dir = "/home/siam/Desktop/volume1/MS_Papers_Arif/Data/TestSmells/SmellsCleanAggregatedData"
output_dir = "/home/siam/Desktop/volume1/MS_Papers_Arif/Data/SmellsPlusCPP"

# Merge files in bulk
merge_project_csvs(cp_dir, smell_dir, output_dir)