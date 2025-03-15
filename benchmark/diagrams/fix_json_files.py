import os
import json
import re
from typing import Dict, Any

def fix_json_file(filepath: str) -> bool:
    """
    Fix potential issues with JSON files.
    
    Parameters:
    -----------
    filepath : str
        Path to the JSON file
        
    Returns:
    --------
    bool
        True if the file was fixed, False otherwise
    """
    try:
        # Try to load the file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # If we can load it, no need to fix
        return False
    except json.JSONDecodeError:
        # If we can't load it, try to fix it
        print(f"Fixing {filepath}...")
        
        # Read the file as text
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Fix common issues
        # 1. Missing commas between objects
        content = re.sub(r'}\s*{', '},{', content)
        
        # 2. Trailing commas
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        # 3. Unquoted keys
        content = re.sub(r'(\w+):', r'"\1":', content)
        
        # Try to load the fixed content
        try:
            data = json.loads(content)
            
            # If successful, write back to the file
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except json.JSONDecodeError as e:
            print(f"Could not fix {filepath}: {e}")
            return False

def ensure_required_fields(filepath: str) -> bool:
    """
    Ensure that the JSON file has all required fields.
    
    Parameters:
    -----------
    filepath : str
        Path to the JSON file
        
    Returns:
    --------
    bool
        True if the file was fixed, False otherwise
    """
    try:
        # Load the file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        modified = False
        
        # Check for required fields
        if 'name' not in data:
            # Extract name from filename
            filename = os.path.basename(filepath)
            data['name'] = os.path.splitext(filename)[0]
            modified = True
        
        # Ensure non_transpiled section exists
        if 'non_transpiled' not in data:
            data['non_transpiled'] = {}
            modified = True
        
        # Ensure transpiled section exists
        if 'transpiled' not in data:
            data['transpiled'] = {}
            modified = True
        
        # Ensure zx_optimized section exists
        if 'zx_optimized' not in data:
            data['zx_optimized'] = {}
            modified = True
        
        # Ensure improvements section exists
        if 'improvements' not in data:
            data['improvements'] = {
                'transpiled': {},
                'zx': {}
            }
            modified = True
        elif 'transpiled' not in data['improvements']:
            data['improvements']['transpiled'] = {}
            modified = True
        elif 'zx' not in data['improvements']:
            data['improvements']['zx'] = {}
            modified = True
        
        # Ensure num_qubits field exists in all sections
        for section in ['non_transpiled', 'transpiled', 'zx_optimized']:
            if section in data and 'num_qubits' not in data[section] and 'num_qubits' in data.get('non_transpiled', {}):
                data[section]['num_qubits'] = data['non_transpiled']['num_qubits']
                modified = True
        
        # Write back if modified
        if modified:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def process_directory(directory: str) -> None:
    """
    Process all JSON files in a directory.
    
    Parameters:
    -----------
    directory : str
        Directory containing JSON files
    """
    fixed_count = 0
    ensured_count = 0
    
    for filename in os.listdir(directory):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(directory, filename)
        
        # Fix JSON file if needed
        if fix_json_file(filepath):
            fixed_count += 1
        
        # Ensure required fields
        if ensure_required_fields(filepath):
            ensured_count += 1
    
    print(f"Fixed {fixed_count} JSON files")
    print(f"Ensured required fields in {ensured_count} JSON files")

if __name__ == "__main__":
    # Process the results directory
    process_directory("../../results_01") 