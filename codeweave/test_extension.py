#!/usr/bin/env python3
"""Test script to verify extension collection feature works correctly"""

import subprocess
import sys
import tempfile
import zipfile
import os

def test_extension_collection():
    """Test that file extensions are collected and displayed"""
    
    # Create a temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files with various extensions (with sufficient content)
        test_files = {
            'test.py': '''# Python file
def hello():
    print("hello world")
    return True

if __name__ == "__main__":
    hello()
    # Adding more lines to meet minimum content requirement
    for i in range(10):
        print(f"Line {i}")
''',
            'test.js': '''// JavaScript file
function hello() {
    console.log("hello world");
    return true;
}

hello();
// Adding more lines to meet minimum content requirement
for (let i = 0; i < 10; i++) {
    console.log(`Line ${i}`);
}
''',
            'test.ts': '''// TypeScript file
const greeting: string = "hello world";

function hello(): boolean {
    console.log(greeting);
    return true;
}

hello();
// Adding more lines to meet minimum content requirement
for (let i = 0; i < 10; i++) {
    console.log(`Line ${i}`);
}
''',
            'README.md': '''# Test Project

This is a test project with multiple file types.

## Features
- Python support
- JavaScript support
- TypeScript support
- Markdown documentation

## Installation
1. Clone the repository
2. Install dependencies
3. Run the application

## Usage
See the documentation for more details.
''',
            'config.json': '{"test": true}',
            'style.css': 'body { color: red; }',
            'index.html': '<html><body>Test</body></html>',
            'data.xml': '<?xml version="1.0"?><root><data>test</data></root>',
            'script.sh': '#!/bin/bash\necho "test"',
            'Makefile': 'test:\n\techo "test"'
        }
        
        for filename, content in test_files.items():
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
        
        # Run codeweave on the test directory
        result = subprocess.run(
            [sys.executable, '-m', 'codeweave', temp_dir, '--lang', 'python,js,typescript,md'],
            capture_output=True,
            text=True
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        
        # Check that extensions were collected
        assert 'Unique Extensions:' in result.stdout, "Extension count not found in output"
        assert '.py' in result.stdout, ".py extension not found"
        assert '.js' in result.stdout, ".js extension not found"
        assert '.ts' in result.stdout, ".ts extension not found"
        assert '.md' in result.stdout, ".md extension not found"
        
        print("\n✅ Extension collection test passed!")

def test_zip_processing():
    """Test that ZIP files are processed without import errors"""
    
    # Create a temporary ZIP file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        temp_zip_path = temp_zip.name
    
    try:
        # Create a ZIP with test files
        with zipfile.ZipFile(temp_zip_path, 'w') as zf:
            zf.writestr('test/hello.py', 'print("Hello from ZIP")')
            zf.writestr('test/config.json', '{"test": true}')
            zf.writestr('test/readme.md', '# Test ZIP')
        
        # Process the ZIP file
        result = subprocess.run(
            [sys.executable, '-m', 'codeweave', temp_zip_path, '--lang', 'python,md,json'],
            capture_output=True,
            text=True
        )
        
        print("\nZIP Processing Test:")
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        
        # Check for the previous error
        assert 'UnboundLocalError' not in result.stderr, "UnboundLocalError still occurs!"
        assert result.returncode == 0, f"Process failed with return code {result.returncode}"
        
        # Check extensions were collected
        assert 'Unique Extensions:' in result.stdout, "Extension count not found for ZIP"
        assert '.py' in result.stdout, ".py extension not found in ZIP"
        assert '.md' in result.stdout, ".md extension not found in ZIP"
        assert '.json' in result.stdout, ".json extension not found in ZIP"
        
        print("\n✅ ZIP processing test passed!")
        
    finally:
        # Clean up
        if os.path.exists(temp_zip_path):
            os.unlink(temp_zip_path)

if __name__ == '__main__':
    print("Testing CodeWeave extension collection feature...\n")
    test_extension_collection()
    test_zip_processing()
    print("\n🎉 All tests passed!")