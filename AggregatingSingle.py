# import pandas as pd
# import os
# from pathlib import Path
# import time

# def aggregate_project_csvs(project_folder, output_folder):
#     """
#     Aggregate all CSV files from a project folder into a single CSV file.
    
#     Args:
#         project_folder (str): Path to project folder containing CSV files
#         output_folder (str): Path to output folder for aggregated CSV
        
#     Returns:
#         tuple: (success, stats dictionary)
#     """
#     try:
#         # Get the project name for the output file
#         project_name = os.path.basename(project_folder)
#         output_file = os.path.join(output_folder, f"{project_name}_aggregated.csv")
        
#         # List to store all dataframes
#         dfs = []
        
#         # Statistics
#         stats = {
#             'processed_files': 0,
#             'total_rows': 0,
#             'error_files': 0
#         }
        
#         print(f"\nProcessing project: {project_name}")
        
#         # Walk through all subdirectories
#         for root, _, files in os.walk(project_folder):
#             csv_files = [f for f in files if f.endswith('.csv')]
            
#             for csv_file in csv_files:
#                 file_path = os.path.join(root, csv_file)
#                 try:
#                     # Read the CSV file
#                     df = pd.read_csv(file_path)
                    
#                     # Add source file information and project name
#                     df['source_file'] = csv_file
#                     df['test_smell_type'] = csv_file.replace('.csv', '')
#                     df['project'] = project_name
                    
#                     dfs.append(df)
#                     stats['processed_files'] += 1
#                     print(f"  Processed: {csv_file}")
                    
#                 except Exception as e:
#                     stats['error_files'] += 1
#                     print(f"  Error processing {csv_file}: {str(e)}")
        
#         if dfs:
#             # Combine all dataframes
#             combined_df = pd.concat(dfs, ignore_index=True)
#             stats['total_rows'] = len(combined_df)
            
#             # Reorder columns to put source information first
#             cols = ['project', 'source_file', 'test_smell_type'] + [
#                 col for col in combined_df.columns 
#                 if col not in ['project', 'source_file', 'test_smell_type']
#             ]
#             combined_df = combined_df[cols]
            
#             # Save the combined dataframe
#             combined_df.to_csv(output_file, index=False)
#             return True, stats
#         else:
#             return False, stats
            
#     except Exception as e:
#         print(f"Error processing project {project_name}: {str(e)}")
#         return False, stats

# def process_all_projects(base_input_dir, output_dir):
#     """
#     Process all project folders and create aggregated CSV files for each.
    
#     Args:
#         base_input_dir (str): Base directory containing project folders
#         output_dir (str): Directory for output CSV files
#     """
#     # Create output directory if it doesn't exist
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Get all immediate subdirectories (project folders)
#     project_folders = [f.path for f in os.scandir(base_input_dir) if f.is_dir()]
    
#     # Overall statistics
#     total_stats = {
#         'total_projects': len(project_folders),
#         'successful_projects': 0,
#         'failed_projects': 0,
#         'total_files_processed': 0,
#         'total_rows_processed': 0,
#         'total_error_files': 0
#     }
    
#     start_time = time.time()
    
#     print(f"Found {len(project_folders)} projects to process")
    
#     # Process each project folder
#     for project_folder in project_folders:
#         success, stats = aggregate_project_csvs(project_folder, output_dir)
        
#         # Update overall statistics
#         if success:
#             total_stats['successful_projects'] += 1
#         else:
#             total_stats['failed_projects'] += 1
        
#         total_stats['total_files_processed'] += stats['processed_files']
#         total_stats['total_rows_processed'] += stats['total_rows']
#         total_stats['total_error_files'] += stats['error_files']
    
#     # Calculate processing time
#     processing_time = time.time() - start_time
    
#     # Print summary
#     print("\n" + "="*50)
#     print("Processing Summary:")
#     print("="*50)
#     print(f"Total projects processed: {total_stats['total_projects']}")
#     print(f"Successful projects: {total_stats['successful_projects']}")
#     print(f"Failed projects: {total_stats['failed_projects']}")
#     print(f"Total files processed: {total_stats['total_files_processed']}")
#     print(f"Total rows processed: {total_stats['total_rows_processed']}")
#     print(f"Total error files: {total_stats['total_error_files']}")
#     print(f"Total processing time: {processing_time:.2f} seconds")
#     print("="*50)

# if __name__ == "__main__":
#     input_dir = "/home/iit/Downloads/Thesis/TEST_SMELL_EXTRACT_CSV"
#     output_dir = "/home/iit/Downloads/Thesis/extracted_singlesmell_csv"
    
#     process_all_projects(input_dir, output_dir)


import pandas as pd

def process_raw_data(file_path):
    """
    Process the space-separated file into a structured DataFrame.
    """
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Split the content into pairs of file path and faulty status
    items = content.strip().split()
    
    # Create lists for paths and status
    paths = []
    status = []
    
    # Process items in pairs
    for i in range(0, len(items), 2):
        if i + 1 < len(items):
            paths.append(items[i])
            status.append(int(items[i + 1]))
    
    # Create DataFrame
    return pd.DataFrame({'file_path': paths, 'is_faulty': status})

def map_production_test_files(df):
    """
    Maps production files with their associated test files.
    """
    # Separate test and production files
    test_files = df[df['file_path'].str.contains('/test', case=False)]
    prod_files = df[~df['file_path'].str.contains('/test', case=False)]
    
    # Create lists for mapped data
    production_files = []
    production_faulty = []
    test_files_mapped = []
    test_faulty = []
    
    # For each production file, find matching test file
    for _, prod_row in prod_files.iterrows():
        prod_file = prod_row['file_path']
        base_name = prod_file.split('/')[-1].replace('.py', '')
        
        # Look for matching test file
        matching_tests = test_files[test_files['file_path'].str.contains(base_name, case=False)]
        
        if not matching_tests.empty:
            # Add all matching test files
            for _, test_row in matching_tests.iterrows():
                production_files.append(prod_file)
                production_faulty.append(prod_row['is_faulty'])
                test_files_mapped.append(test_row['file_path'])
                test_faulty.append(test_row['is_faulty'])
        else:
            # Add production file with no matching test
            production_files.append(prod_file)
            production_faulty.append(prod_row['is_faulty'])
            test_files_mapped.append(None)
            test_faulty.append(None)
    
    # Create result DataFrame
    result_df = pd.DataFrame({
        'ProductionFile': production_files,
        'IsFaultyProduction': production_faulty,
        'AssociatedTestFile': test_files_mapped,
        'IsFaultyTest': test_faulty
    })
    
    return result_df

# File paths
input_file = r'/home/iit/Downloads/Thesis/Data/SM_CP_FP/Fault_proneness_combined.csv'
output_file = r'/home/iit/Downloads/Thesis/Data/SM_CP_FP/Fault_proneness_Prod_test.csv'

try:
    # Process the raw data
    print(f"Reading input file: {input_file}")
    df = process_raw_data(input_file)
    
    # Create the mapping
    print("Processing file mappings...")
    mapped_df = map_production_test_files(df)
    
    # Save the result
    print(f"Saving output to: {output_file}")
    mapped_df.to_csv(output_file, index=False)
    
    # Display summary statistics
    print("\nSummary:")
    print(f"Total production files mapped: {len(mapped_df)}")
    print(f"Production files with associated tests: {mapped_df['AssociatedTestFile'].notna().sum()}")
    print(f"Production files without tests: {mapped_df['AssociatedTestFile'].isna().sum()}")
    
    # Display first few mappings
    print("\nFirst few mappings:")
    print(mapped_df.head())
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
    raise