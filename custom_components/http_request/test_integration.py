"""Test script to verify the integration structure."""
import json
import os

def check_integration():
    """Check if all required files exist and are valid."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        "__init__.py",
        "manifest.json", 
        "config_flow.py",
        "sensor.py",
        "strings.json",
        "translations/en.json",
        "translations/ko.json"
    ]
    
    print("Checking HTTP Request integration files...")
    print(f"Base path: {base_path}")
    print("-" * 50)
    
    all_good = True
    
    for file in required_files:
        file_path = os.path.join(base_path, file)
        if os.path.exists(file_path):
            print(f"✓ {file} exists")
            
            # Check JSON files
            if file.endswith(".json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    print(f"  → JSON is valid")
                except json.JSONDecodeError as e:
                    print(f"  → JSON ERROR: {e}")
                    all_good = False
        else:
            print(f"✗ {file} MISSING")
            all_good = False
    
    print("-" * 50)
    
    # Check manifest.json specifically
    manifest_path = os.path.join(base_path, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        required_manifest_keys = ["domain", "name", "version", "config_flow", "codeowners", "requirements"]
        print("Checking manifest.json keys:")
        for key in required_manifest_keys:
            if key in manifest:
                print(f"✓ {key}: {manifest[key]}")
            else:
                print(f"✗ {key} MISSING")
                all_good = False
    
    print("-" * 50)
    if all_good:
        print("✓ All checks passed!")
    else:
        print("✗ Some checks failed!")
    
    return all_good

if __name__ == "__main__":
    check_integration()