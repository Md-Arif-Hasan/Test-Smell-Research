import pandas as pd
import os
import re

def is_test_file(filename):
    """Determine if a file is a test file based on common test file patterns"""
    test_patterns = [
        r'_test\.py$',      # matches _test.py at end
        r'test_.*\.py$',    # matches test_ at start
        r'_tests\.py$',     # matches _tests.py at end
        r'tests_.*\.py$',   # matches tests_ at start
        r'/tests?/',        # matches /test/ or /tests/ directory
        r'/testing/'        # matches /testing/ directory
    ]
    return any(re.search(pattern, filename) for pattern in test_patterns)

def get_base_name(filename):
    """Extract base name for matching test and production files"""
    # Remove test indicators
    base = filename
    base = re.sub(r'_test\.py$', '.py', base)
    base = re.sub(r'test_(.*)\.py$', r'\1.py', base)
    base = re.sub(r'_tests\.py$', '.py', base)
    base = re.sub(r'tests_(.*)\.py$', r'\1.py', base)
    return base

def find_matching_files(files):
    """Find matching test and production file pairs"""
    # Separate test and production files
    test_files = [f for f in files if is_test_file(f)]
    prod_files = [f for f in files if not is_test_file(f)]
    
    # Create mapping of base names to test/prod files
    file_pairs = {}
    
    # Process all files
    for test_file in test_files:
        test_base = get_base_name(test_file)
        # Find matching production file
        matching_prod = None
        for prod_file in prod_files:
            if get_base_name(prod_file) == test_base:
                matching_prod = prod_file
                break
        if matching_prod:
            file_pairs[matching_prod] = test_file
    
    return file_pairs

def transform_csv(input_path, output_dir):
    """Transform CSV data to group test and production files together with their metrics."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract project name from input path
    project_name = os.path.basename(input_path).replace('_analysis.csv', '')
    
    # Read input CSV
    data = pd.read_csv(input_path)
    
    # Get all unique filenames
    all_files = data['Filename'].unique()
    
    # Find matching file pairs
    file_pairs = find_matching_files(all_files)
    
    # Create empty lists to store paired data
    paired_data = []
    processed_files = set()
    
    # Process production files and their matching test files
    for prod_file in data['Filename'].unique():
        if prod_file in processed_files or is_test_file(prod_file):
            continue
            
        # Get production file metrics
        prod_row = data[data['Filename'] == prod_file].iloc[0]
        prod_metrics = prod_row[['Changes', 'TotalCommits', 'Insertions', 'Deletions']].values
        
        # Find matching test file
        test_file = file_pairs.get(prod_file, 'N/A')
        
        # Get test file metrics if it exists
        test_metrics = [0, 0, 0, 0]  # Default values if test file doesn't exist
        if test_file != 'N/A':
            test_row = data[data['Filename'] == test_file]
            if not test_row.empty:
                test_metrics = test_row.iloc[0][['Changes', 'TotalCommits', 'Insertions', 'Deletions']].values
                processed_files.add(test_file)
        
        # Add the paired data
        paired_data.append({
            'ProductionFile': prod_file,
            'TestFile': test_file,
            'Prod_Changes': prod_metrics[0],
            'Prod_TotalCommits': prod_metrics[1],
            'Prod_Insertions': prod_metrics[2],
            'Prod_Deletions': prod_metrics[3],
            'Test_Changes': test_metrics[0],
            'Test_TotalCommits': test_metrics[1],
            'Test_Insertions': test_metrics[2],
            'Test_Deletions': test_metrics[3]
        })
        
        processed_files.add(prod_file)
    
    # Convert to DataFrame
    result_df = pd.DataFrame(paired_data)
    
    # Create output filename
    output_filename = f"{project_name}_transformed.csv"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save transformed CSV
    result_df.to_csv(output_path, index=False)
    print(f"Transformed CSV saved to: {output_path}")

# Run the transformation with your specific paths
input_path = "/home/iit/Downloads/Thesis/project_analysis_results/typer_analysis.csv"
output_dir = "/home/iit/Downloads/Thesis/convertedCSV"

transform_csv(input_path, output_dir)