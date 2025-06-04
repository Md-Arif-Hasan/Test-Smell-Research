# import pandas as pd

# # Read the CSV files
# smells_cp_df = pd.read_csv('/home/iit/Downloads/Thesis/Data/SM_CP_FP/SmellsPlusCP_FRevised/_aerospike-client-python.csv')
# fault_proneness_df = pd.read_csv('/home/iit/Downloads/Thesis/Data/SM_CP_FP/Fault_proneness/aerospike-client-python_fault_proneness.csv')

# # Print column names for verification
# print("Columns in first CSV:", smells_cp_df.columns.tolist())
# print("Columns in second CSV:", fault_proneness_df.columns.tolist())

# # Merge the dataframes matching TestFile with File
# merged_df = pd.merge(
#     smells_cp_df,
#     fault_proneness_df,
#     left_on='TestFile',
#     right_on='File',
#     how='inner'
# )

# # Save the merged dataframe to a new CSV file
# output_path = '/home/iit/Downloads/Thesis/Data/SM_CP_FP/Final/_aerospike_final.csv'
# merged_df.to_csv(output_path, index=False)

# # Print summary statistics
# print(f"\nOriginal number of rows in first file: {len(smells_cp_df)}")
# print(f"Original number of rows in second file: {len(fault_proneness_df)}")
# print(f"Number of rows in merged file: {len(merged_df)}")



import pandas as pd
import os
from pathlib import Path

def get_project_names(smells_dir, fp_dir):
    """
    Get project names by comparing files in both directories.
    
    Parameters:
    smells_dir (str): Path to smells CSV directory
    fp_dir (str): Path to fault proneness CSV directory
    
    Returns:
    list: List of project names that exist in both directories
    """
    # Get all CSV files from smells directory and strip prefix '_' and '.csv'
    smell_files = {f[1:-4] for f in os.listdir(smells_dir) if f.endswith('.csv')}
    
    # Get all CSV files from fault proneness directory and strip '_fault_proneness.csv'
    fp_files = {f.replace('_fault_proneness.csv', '') for f in os.listdir(fp_dir) if f.endswith('_fault_proneness.csv')}
    
    # Find common project names
    common_projects = smell_files.intersection(fp_files)
    return sorted(list(common_projects))

def merge_project_data(base_path, project_name):
    """
    Merge smell and fault proneness data for a specific project.
    
    Parameters:
    base_path (str): Base path to the data directory
    project_name (str): Name of the project to process
    
    Returns:
    pd.DataFrame: Merged dataframe
    """
    # Construct file paths
    smells_path = os.path.join(base_path, 'SM_CP_FP/SmellsPlusCP_FRevised', f'_{project_name}.csv')
    fp_path = os.path.join(base_path, 'SM_CP_FP/Fault_proneness', f'{project_name}_fault_proneness.csv')
    
    # Read the CSV files
    try:
        smells_cp_df = pd.read_csv(smells_path)
        fault_proneness_df = pd.read_csv(fp_path)
        
        print(f"\nProcessing {project_name}:")
        print(f"Columns in smells CSV: {smells_cp_df.columns.tolist()}")
        print(f"Columns in fault proneness CSV: {fault_proneness_df.columns.tolist()}")
        
        # Merge the dataframes
        merged_df = pd.merge(
            smells_cp_df,
            fault_proneness_df,
            left_on='TestFile',
            right_on='File',
            how='inner'
        )
        
        # Print summary statistics
        print(f"Original rows in smells file: {len(smells_cp_df)}")
        print(f"Original rows in fault proneness file: {len(fault_proneness_df)}")
        print(f"Rows in merged file: {len(merged_df)}")
        
        return merged_df
        
    except Exception as e:
        print(f"Error processing {project_name}: {str(e)}")
        return None

def process_all_projects(base_path):
    """
    Process all projects found in both directories and save merged data.
    
    Parameters:
    base_path (str): Base path to the data directory
    """
    # Define directories
    smells_dir = os.path.join(base_path, 'SM_CP_FP/SmellsPlusCP_FRevised')
    fp_dir = os.path.join(base_path, 'SM_CP_FP/Fault_proneness')
    output_dir = os.path.join(base_path, 'SM_CP_FP/Final')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get list of projects that exist in both directories
    projects = get_project_names(smells_dir, fp_dir)
    print(f"Found {len(projects)} projects to process")
    
    # Process each project
    successful = 0
    failed = 0
    
    for project in projects:
        merged_df = merge_project_data(base_path, project)
        
        if merged_df is not None:
            # Save the merged dataframe
            output_path = os.path.join(output_dir, f'_{project}_final.csv')
            merged_df.to_csv(output_path, index=False)
            print(f"Saved merged data to: {output_path}\n")
            successful += 1
        else:
            failed += 1
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Total projects found: {len(projects)}")
    print(f"Successfully processed: {successful}")
    print(f"Failed to process: {failed}")

# Base path to your data directory
base_path = '/home/iit/Downloads/Thesis/Data'

# Process all projects
process_all_projects(base_path)