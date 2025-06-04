import os
import pandas as pd
import numpy as np
import ast
import re
import tempfile
from git import Repo
import logging
import sys
import time
import radon.complexity as complexity
import radon.metrics as metrics
import radon.raw as raw_metrics
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class SingleProjectTestMetricsCollector:
    """Metrics collector for test smells analysis on a single project"""
    
    def __init__(self, project_url, work_dir=None):
        """
        Initialize the metrics collector for a single project
        
        Args:
            project_url (str): GitHub project URL
            work_dir (str, optional): Working directory for cloned repository
        """
        self.project_url = project_url
        self.work_dir = work_dir or os.path.join(tempfile.gettempdir(), "test_metrics_analysis")
        os.makedirs(self.work_dir, exist_ok=True)
        self.project_name = project_url.split('/')[-1].replace('.git', '')
        self.project_dir = os.path.join(self.work_dir, self.project_name)
        self.results = []
        
    def clone_repository(self):
        """Clone the GitHub repository"""
        try:
            if os.path.exists(self.project_dir):
                logger.info(f"Repository already exists: {self.project_name}")
                return True
            
            logger.info(f"Cloning {self.project_url}")
            Repo.clone_from(self.project_url, self.project_dir)
            logger.info(f"Successfully cloned {self.project_name}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to clone {self.project_url}: {str(e)}")
            return False
    
    def find_python_files(self):
        """
        Find all Python files in the repository
        
        Returns:
            tuple: (list of production files, list of test files)
        """
        production_files = []
        test_files = []
        
        for root, _, files in os.walk(self.project_dir):
            # Skip common non-code directories
            if any(part in root for part in ['.git', '__pycache__', 'venv', '.venv', 'env', '.tox']):
                continue
                
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.project_dir)
                
                # Classify as test or production
                if 'test' in file.lower() or 'test' in rel_path.lower():
                    test_files.append(rel_path)
                else:
                    production_files.append(rel_path)
        
        return production_files, test_files
    
    def match_test_files(self, prod_files, test_files):
        """
        Match test files to production files
        
        Args:
            prod_files (list): List of production files
            test_files (list): List of test files
            
        Returns:
            list: List of (prod_file, test_file) pairs
        """
        pairs = []
        
        for test_file in test_files:
            test_name = os.path.basename(test_file).lower()
            test_name_no_ext = os.path.splitext(test_name)[0]
            
            # Remove common test prefixes/suffixes
            clean_name = test_name_no_ext
            for pattern in ['test_', '_test', 'tests_', '_tests']:
                clean_name = clean_name.replace(pattern, '')
                
            best_match = None
            highest_similarity = 0
            
            for prod_file in prod_files:
                prod_name = os.path.basename(prod_file).lower()
                prod_name_no_ext = os.path.splitext(prod_name)[0]
                
                # Simple string similarity check
                if clean_name in prod_name_no_ext or prod_name_no_ext in clean_name:
                    similarity = len(set(clean_name) & set(prod_name_no_ext)) / len(set(clean_name) | set(prod_name_no_ext))
                    
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_match = prod_file
            
            if best_match and highest_similarity > 0.3:  # Threshold for similarity
                pairs.append((best_match, test_file))
            else:
                # If no match found, pair with None
                pairs.append((None, test_file))
        
        return pairs
    
    def get_file_metrics(self, prod_file_path, test_file_path):
        """
        Calculate enhanced metrics for a production-test file pair
        
        Args:
            prod_file_path (str): Path to the production file (or None)
            test_file_path (str): Path to the test file
            
        Returns:
            dict: Dictionary with enhanced metrics
        """
        metrics_dict = {}
        
        # Full paths
        full_test_path = os.path.join(self.project_dir, test_file_path)
        full_prod_path = os.path.join(self.project_dir, prod_file_path) if prod_file_path else None
        
        # Check if test file exists
        if not os.path.exists(full_test_path):
            logger.warning(f"Test file does not exist: {full_test_path}")
            return self._get_default_metrics()
        
        try:
            # Get code complexity metrics
            metrics_dict.update(self._calculate_complexity_metrics(full_prod_path, full_test_path))
            
            # Get assertion-related metrics
            metrics_dict.update(self._calculate_assert_metrics(full_test_path))
            
            # Get cohesion metrics
            metrics_dict.update(self._calculate_cohesion_metrics(full_test_path))
            
            # Get coupling metrics
            metrics_dict.update(self._calculate_coupling_metrics(full_test_path))
            
            # Get test structure metrics
            metrics_dict.update(self._analyze_test_methods(full_test_path))
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return self._get_default_metrics()
        
        return metrics_dict
    
    def _get_default_metrics(self):
        """Return default metrics dictionary with zeros"""
        return {
            # Complexity metrics
            'prod_cc_avg': 0,
            'prod_cc_max': 0,
            'test_cc_avg': 0,
            'test_cc_max': 0,
            'cc_ratio': 0,
            'halstead_volume': 0,
            'halstead_difficulty': 0,
            'halstead_effort': 0,
            'maintainability_index': 0,
            
            # Assertion metrics
            'assert_count': 0,
            'unittest_assert_count': 0,
            'pytest_assert_count': 0,
            'total_assert_count': 0,
            'assert_density': 0,
            'mock_count': 0,
            
            # Cohesion metrics
            'lcom': 0,
            'tcc': 0,
            'similar_assert_ratio': 0,
            
            # Coupling metrics
            'internal_imports': 0,
            'external_imports': 0,
            'total_imports': 0,
            'import_complexity': 0,
            
            # Test structure metrics
            'test_count': 0,
            'avg_test_size': 0,
            'max_test_size': 0,
            'test_to_helper_ratio': 0,
            'setup_ratio': 0,
            'test_duplication_score': 0
        }
    
    def _calculate_complexity_metrics(self, prod_file_path, test_file_path):
        """
        Calculate complexity metrics for production and test files
        
        Args:
            prod_file_path (str): Path to production file (or None)
            test_file_path (str): Path to test file
            
        Returns:
            dict: Dictionary with complexity metrics
        """
        metrics_dict = {}
        
        # Production file complexity
        if prod_file_path and os.path.exists(prod_file_path):
            try:
                with open(prod_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    prod_code = f.read()
                    
                prod_functions = complexity.cc_visit(prod_code)
                if prod_functions:
                    complexities = [func.complexity for func in prod_functions]
                    metrics_dict['prod_cc_avg'] = np.mean(complexities)
                    metrics_dict['prod_cc_max'] = max(complexities)
                else:
                    metrics_dict['prod_cc_avg'] = 0
                    metrics_dict['prod_cc_max'] = 0
                    
                # Maintainability index for production code
                try:
                    mi = metrics.mi_visit(prod_code, multi=True)
                    metrics_dict['maintainability_index'] = mi
                except:
                    metrics_dict['maintainability_index'] = 0
            except Exception as e:
                logger.error(f"Error calculating production complexity: {str(e)}")
                metrics_dict['prod_cc_avg'] = 0
                metrics_dict['prod_cc_max'] = 0
                metrics_dict['maintainability_index'] = 0
        else:
            metrics_dict['prod_cc_avg'] = 0
            metrics_dict['prod_cc_max'] = 0
            metrics_dict['maintainability_index'] = 0
        
        # Test file complexity
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                test_code = f.read()
                
            test_functions = complexity.cc_visit(test_code)
            if test_functions:
                complexities = [func.complexity for func in test_functions]
                metrics_dict['test_cc_avg'] = np.mean(complexities)
                metrics_dict['test_cc_max'] = max(complexities)
            else:
                metrics_dict['test_cc_avg'] = 0
                metrics_dict['test_cc_max'] = 0
                
            # Halstead metrics for test code
            try:
                h_metrics = metrics.h_visit(test_code)
                if h_metrics:
                    metrics_dict['halstead_volume'] = h_metrics.total.volume
                    metrics_dict['halstead_difficulty'] = h_metrics.total.difficulty
                    metrics_dict['halstead_effort'] = h_metrics.total.effort
                else:
                    metrics_dict['halstead_volume'] = 0
                    metrics_dict['halstead_difficulty'] = 0
                    metrics_dict['halstead_effort'] = 0
            except:
                metrics_dict['halstead_volume'] = 0
                metrics_dict['halstead_difficulty'] = 0
                metrics_dict['halstead_effort'] = 0
        
        except Exception as e:
            logger.error(f"Error calculating test complexity: {str(e)}")
            metrics_dict['test_cc_avg'] = 0
            metrics_dict['test_cc_max'] = 0
            metrics_dict['halstead_volume'] = 0
            metrics_dict['halstead_difficulty'] = 0
            metrics_dict['halstead_effort'] = 0
        
        # Calculate complexity ratio
        if metrics_dict['prod_cc_avg'] > 0:
            metrics_dict['cc_ratio'] = metrics_dict['test_cc_avg'] / metrics_dict['prod_cc_avg']
        else:
            metrics_dict['cc_ratio'] = 0
            
        return metrics_dict
    
    def _calculate_assert_metrics(self, test_file_path):
        """
        Calculate assertion-related metrics for test file
        
        Args:
            test_file_path (str): Path to test file
            
        Returns:
            dict: Dictionary with assertion metrics
        """
        metrics_dict = {}
        
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # Count different types of assertions
            assert_pattern = r'assert\s+[^,;]+'
            assert_count = len(re.findall(assert_pattern, code))
            
            # Count unittest assertions (e.g., assertEqual, assertTrue)
            unittest_assert_pattern = r'self\.assert[A-Z][a-zA-Z]*\('
            unittest_assert_count = len(re.findall(unittest_assert_pattern, code))
            
            # Count pytest assertions (e.g., assert_equal, assert_true)
            pytest_assert_pattern = r'assert_[a-z_]+\('
            pytest_assert_count = len(re.findall(pytest_assert_pattern, code))
            
            # Count mock assertions and verifications
            mock_pattern = r'mock\.[a-z_]+\.\w+|mock\.\w+\(|assert_called|assert_not_called'
            mock_count = len(re.findall(mock_pattern, code, re.IGNORECASE))
            
            metrics_dict['assert_count'] = assert_count
            metrics_dict['unittest_assert_count'] = unittest_assert_count
            metrics_dict['pytest_assert_count'] = pytest_assert_count
            metrics_dict['mock_count'] = mock_count
            metrics_dict['total_assert_count'] = assert_count + unittest_assert_count + pytest_assert_count
            
            # Calculate assertion density (assertions per LOC)
            raw = raw_metrics.analyze(code)
            if raw.sloc > 0:
                metrics_dict['assert_density'] = metrics_dict['total_assert_count'] / raw.sloc
            else:
                metrics_dict['assert_density'] = 0
                
        except Exception as e:
            logger.error(f"Error calculating assert metrics: {str(e)}")
            metrics_dict['assert_count'] = 0
            metrics_dict['unittest_assert_count'] = 0
            metrics_dict['pytest_assert_count'] = 0
            metrics_dict['mock_count'] = 0
            metrics_dict['total_assert_count'] = 0
            metrics_dict['assert_density'] = 0
            
        return metrics_dict
    
    def _calculate_cohesion_metrics(self, test_file_path):
        """
        Calculate cohesion metrics for test file
        
        Args:
            test_file_path (str): Path to test file
            
        Returns:
            dict: Dictionary with cohesion metrics
        """
        metrics_dict = {}
        
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Extract all test methods
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_') or 'test' in node.name.lower():
                        functions.append(node)
            
            if not functions:
                metrics_dict['lcom'] = 0
                metrics_dict['tcc'] = 0
                metrics_dict['similar_assert_ratio'] = 0
                return metrics_dict
            
            # Calculate LCOM (Lack of Cohesion of Methods)
            shared_variables = defaultdict(set)
            
            for i, func in enumerate(functions):
                vars_used = set()
                
                # Extract variables used in the function
                for node in ast.walk(func):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                        vars_used.add(node.id)
                    elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                        if isinstance(node.value, ast.Name) and node.value.id == 'self':
                            vars_used.add(f"self.{node.attr}")
                
                shared_variables[i] = vars_used
            
            # Count pairs with no shared variables
            no_shared_count = 0
            total_pairs = 0
            
            for i in range(len(functions)):
                for j in range(i+1, len(functions)):
                    total_pairs += 1
                    if not shared_variables[i].intersection(shared_variables[j]):
                        no_shared_count += 1
            
            metrics_dict['lcom'] = no_shared_count / total_pairs if total_pairs > 0 else 0
            
            # Calculate TCC (Tight Class Cohesion)
            connected_pairs = total_pairs - no_shared_count
            metrics_dict['tcc'] = connected_pairs / total_pairs if total_pairs > 0 else 0
            
            # Measure assert similarity across test methods
            assert_patterns = []
            for func in functions:
                func_asserts = []
                for node in ast.walk(func):
                    if isinstance(node, ast.Assert) or (
                        isinstance(node, ast.Call) and 
                        isinstance(node.func, ast.Attribute) and 
                        'assert' in getattr(node.func, 'attr', '')
                    ):
                        func_asserts.append(ast.dump(node))
                assert_patterns.append(set(func_asserts))
            
            similar_asserts = 0
            total_comparisons = 0
            
            for i in range(len(assert_patterns)):
                for j in range(i+1, len(assert_patterns)):
                    total_comparisons += 1
                    if assert_patterns[i] and assert_patterns[j]:
                        union_size = len(assert_patterns[i].union(assert_patterns[j]))
                        if union_size > 0:
                            similarity = len(assert_patterns[i].intersection(assert_patterns[j])) / union_size
                            if similarity > 0.5:  # Threshold for similarity
                                similar_asserts += 1
            
            metrics_dict['similar_assert_ratio'] = similar_asserts / total_comparisons if total_comparisons > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating cohesion metrics: {str(e)}")
            metrics_dict['lcom'] = 0
            metrics_dict['tcc'] = 0
            metrics_dict['similar_assert_ratio'] = 0
            
        return metrics_dict
    
    def _calculate_coupling_metrics(self, test_file_path):
        """
        Calculate coupling metrics for test file
        
        Args:
            test_file_path (str): Path to test file
            
        Returns:
            dict: Dictionary with coupling metrics
        """
        metrics_dict = {}
        
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # Parse imports
            tree = ast.parse(code)
            imports = []
            direct_imports = 0
            from_imports = 0
            wildcard_imports = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    direct_imports += len(node.names)
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    from_imports += len(node.names)
                    for name in node.names:
                        if name.name == '*':
                            wildcard_imports += 1
                        if node.module:
                            imports.append(f"{node.module}.{name.name}")
            
            # Count external vs internal imports
            project_modules = set()
            
            # Find all Python modules in the project (simplified)
            for root, _, files in os.walk(self.project_dir):
                if any(part in root for part in ['.git', '__pycache__', 'venv', '.venv', 'env', '.tox']):
                    continue
                
                for file in files:
                    if file.endswith('.py'):
                        mod_name = os.path.splitext(file)[0]
                        project_modules.add(mod_name)
            
            internal_imports = 0
            external_imports = 0
            
            for imp in imports:
                base_module = imp.split('.')[0]
                if base_module in project_modules:
                    internal_imports += 1
                else:
                    external_imports += 1
            
            metrics_dict['internal_imports'] = internal_imports
            metrics_dict['external_imports'] = external_imports
            metrics_dict['total_imports'] = len(imports)
            
            # Calculate import complexity score
            metrics_dict['import_complexity'] = direct_imports + (2 * from_imports) + (5 * wildcard_imports)
            
        except Exception as e:
            logger.error(f"Error calculating coupling metrics: {str(e)}")
            metrics_dict['internal_imports'] = 0
            metrics_dict['external_imports'] = 0
            metrics_dict['total_imports'] = 0
            metrics_dict['import_complexity'] = 0
            
        return metrics_dict
    
    def _analyze_test_methods(self, test_file_path):
        """
        Analyze test methods for structure metrics
        
        Args:
            test_file_path (str): Path to test file
            
        Returns:
            dict: Dictionary with test structure metrics
        """
        metrics_dict = {}
        
        try:
            with open(test_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            tree = ast.parse(code)
            test_methods = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_') or 'test' in node.name.lower():
                        test_methods.append(node)
            
            if not test_methods:
                metrics_dict['test_count'] = 0
                metrics_dict['avg_test_size'] = 0
                metrics_dict['max_test_size'] = 0
                metrics_dict['test_to_helper_ratio'] = 0
                metrics_dict['setup_ratio'] = 0
                metrics_dict['test_duplication_score'] = 0
                return metrics_dict
            
            # Count test methods
            metrics_dict['test_count'] = len(test_methods)
            
            # Calculate test method sizes
            test_sizes = []
            for method in test_methods:
                end_lineno = getattr(method, 'end_lineno', 0)
                if not end_lineno and hasattr(method, 'body'):
                    # Estimate end line if not available
                    end_lineno = method.lineno + len(method.body)
                size = end_lineno - method.lineno
                test_sizes.append(size)
            
            metrics_dict['avg_test_size'] = np.mean(test_sizes) if test_sizes else 0
            metrics_dict['max_test_size'] = max(test_sizes) if test_sizes else 0
            
            # Count helper methods (non-test methods)
            helper_methods = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not (node.name.startswith('test_') or 'test' in node.name.lower()):
                        if node.name not in ['setUp', 'tearDown', 'setUpClass', 'tearDownClass']:
                            helper_methods.append(node)
            
            helper_count = len(helper_methods) or 1  # Avoid division by zero
            metrics_dict['test_to_helper_ratio'] = len(test_methods) / helper_count
            
            # Setup methods presence and size
            setup_methods = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name in ['setUp', 'tearDown', 'setUpClass', 'tearDownClass', 'setup_method', 'teardown_method']:
                        setup_methods.append(node)
            
            setup_code_size = 0
            for method in setup_methods:
                end_lineno = getattr(method, 'end_lineno', 0)
                if not end_lineno and hasattr(method, 'body'):
                    end_lineno = method.lineno + len(method.body)
                size = end_lineno - method.lineno
                setup_code_size += size
            
            total_code_size = sum(test_sizes) + setup_code_size
            metrics_dict['setup_ratio'] = setup_code_size / total_code_size if total_code_size > 0 else 0
            
            # Test duplication detection
            test_content = []
            for method in test_methods:
                content = ast.dump(method)
                test_content.append(content)
            
            duplication_score = 0
            for i in range(len(test_content)):
                for j in range(i+1, len(test_content)):
                    # Simple string similarity using difflib
                    import difflib
                    similarity = difflib.SequenceMatcher(None, test_content[i], test_content[j]).ratio()
                    if similarity > 0.7:  # Threshold for duplication
                        duplication_score += 1
            
            metrics_dict['test_duplication_score'] = duplication_score
            
        except Exception as e:
            logger.error(f"Error analyzing test methods: {str(e)}")
            metrics_dict['test_count'] = 0
            metrics_dict['avg_test_size'] = 0
            metrics_dict['max_test_size'] = 0
            metrics_dict['test_to_helper_ratio'] = 0
            metrics_dict['setup_ratio'] = 0
            metrics_dict['test_duplication_score'] = 0
            
        return metrics_dict
    
    def analyze_project(self):
        """
        Analyze the project and collect metrics for all test files
        
        Returns:
            pd.DataFrame: DataFrame with metrics for all test files
        """
        if not os.path.exists(self.project_dir):
            success = self.clone_repository()
            if not success:
                logger.error(f"Failed to clone repository {self.project_url}")
                return pd.DataFrame()
        
        # Find Python files
        logger.info(f"Finding Python files in {self.project_name}")
        prod_files, test_files = self.find_python_files()
        
        if not test_files:
            logger.warning(f"No test files found in {self.project_name}")
            return pd.DataFrame()
        
        logger.info(f"Found {len(prod_files)} production files and {len(test_files)} test files")
        
        # Match test files to production files
        logger.info("Matching test files to production files")
        file_pairs = self.match_test_files(prod_files, test_files)
        
        # Collect metrics for each pair
        results = []
        
        for i, (prod_file, test_file) in enumerate(file_pairs):
            logger.info(f"Processing {i+1}/{len(file_pairs)}: {test_file}")
            
            metrics = self.get_file_metrics(prod_file, test_file)
            
            # Add file info to metrics
            metrics['project'] = self.project_name
            metrics['test_file'] = test_file
            metrics['production_file'] = prod_file if prod_file else 'N/A'
            
            results.append(metrics)
        
        # Convert results to DataFrame
        df = pd.DataFrame(results)
        
        # Reorder columns to match desired output format
        column_order = ['project', 'test_file', 'production_file'] + [
            col for col in df.columns if col not in ['project', 'test_file', 'production_file']
        ]
        df = df[column_order]
        
        return df
def main():
    # The single project to analyze
    project_url = "https://github.com/aerospike/aerospike-client-python.git"
    
    # Initialize the metrics collector
    collector = SingleProjectTestMetricsCollector(project_url=project_url)
    
    # Analyze the project
    logger.info(f"Starting analysis of {project_url}")
    results_df = collector.analyze_project()
    
    if results_df.empty:
        logger.error("No data collected. Exiting.")
        return
    
    # Save results
    output_csv = f"{collector.project_name}_test_metrics.csv"
    results_df.to_csv(output_csv, index=False)
    logger.info(f"Metrics saved to {output_csv}")
    
    # Display results
    print(f"\nProject: {collector.project_name}")
    print(f"Number of test files analyzed: {len(results_df)}")
    print("\nSample results (first 5 rows):")
    print(results_df[['project', 'test_file', 'test_count', 'total_assert_count', 'test_cc_avg', 'lcom']].head())
    
    # If running in Jupyter, enable file download link
    try:
        from IPython.display import FileLink, display
        print("\nDownload the CSV file here:")
        display(FileLink(output_csv))
    except ImportError:
        print(f"To download the CSV, find the file here: {output_csv}")

if __name__ == "__main__":
    main()
