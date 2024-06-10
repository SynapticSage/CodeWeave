# Description: Utility functions for path manipulation and file type checking.

import os
import fnmatch
import argparse
import logging

file_extension_dict = {
        'python': ['.py'],
        'py': ['.py'],
        'ipython': ['.ipynb'],
        'ipynb': ['.ipynb'],
        'go': ['.go'],
        'js': ['.js'],
        'html': ['.html'],
        'mojo': ['.mojo'],
        'java': ['.java'],
        'c': ['.c','.h'],
        'cpp': ['.cpp','.h','.hpp'],
        'c++': ['.cpp','.h','.hpp'],
        'csharp': ['.cs'],
        'ruby': ['.rb'],
        'mojo': ['.mojo'],
        'javascript': ['.js'],
        'markdown': ['.md', '.markdown', '.mdx'],
        'matlab': ['.m'],
        'md': ['.md'],
        'shell': ['.sh'],
        'bash': ['.sh'],
        'zsh': ['.sh'],
        'toml': ['.toml']
}

def lookup_file_extension(file_path:str)->list[str]:
    """Lookup the file extension of a file_path and return list of valid keys of
    file_extension_dict"""
    return [key for key, value in file_extension_dict.items() if any(file_path.endswith(ext) for ext in value)]

def should_exclude_file(file_path, args):
    """Check if the file path matches any of the exclude patterns."""
    exclude_patterns = args.exclude
    answer = any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns)
    if answer:
        logging.debug(f"Excluding file: {file_path}")
    return answer

def inclusion_violate(file_path, args):
    """
    Check if the file path violates the include patterns
    """
    if args.include:
        confirm_include = any(include in file_path for include in args.include)
        if not confirm_include:
            logging.debug(f"Skipping file: {file_path}")
    else:
        # Default to include
        confirm_include = True
    return not confirm_include

def extract_git_folder(folder:str)->str|None:
    """ Extract the git folder name from the folder path 
    We must search from the lower child folder up to the parent folder
    looking for .git
    """
    if folder:
        if '.git' in os.listdir(folder):
            return os.path.basename(folder)
        folder = os.path.dirname(folder)
    return None
def is_test_file(file_content, lang):
    """Determine if the file content suggests it is a test file."""
    test_indicators = []
    if lang == "python" or lang == "mojo":
        test_indicators = ["import unittest", "import pytest", "from unittest", "from pytest"]
    elif lang == "go":
        test_indicators = ["import testing", "func Test"]
    elif lang == "js":
        test_indicators = ["describe(", "it(", "test(", "expect(", "jest", "mocha"]
    return any(indicator in file_content for indicator in test_indicators)

def is_file_type(file_path, file_languages:list):
    """Check if the file has any of the specified file extensions."""
    is_ft = any(file_path.endswith(ext) for file_language in file_languages for
        ext in file_extension_dict[file_language.replace('.','')])
    if not is_ft:
        logging.debug(f"Skipping file: {file_path}")
    return is_ft

def is_likely_useful_file(file_path:str, lang:str, args:argparse.Namespace)->bool:
    """Determine if the file is likely to be useful by excluding certain
    directories and specific file types."""
    excluded_dirs = args.excluded_dirs
    utility_or_config_files = []
    github_workflow_or_docs = [".github", ".gitignore", "LICENSE", "README"]
    # if file_path.endswith(".py"):
    #     import pdb; pdb.set_trace()

    if lang == "python" or lang == "mojo":
        excluded_dirs.append("__pycache__")
        utility_or_config_files.extend(["hubconf.py", "setup.py"])
        github_workflow_or_docs.extend(["stale.py", "gen-card-", "write_model_card"])
    elif lang == "go":
        excluded_dirs.append("vendor")
        utility_or_config_files.extend(["go.mod", "go.sum", "Makefile"])
    elif lang == "js":
        excluded_dirs.extend(["node_modules", "dist", "build"])
        utility_or_config_files.extend(["package.json", "package-lock.json", "webpack.config.js"])
    elif lang == "html":
        excluded_dirs.extend(["css", "js", "images", "fonts"])

    if any((part.startswith('.') and not part.startswith('..') and part != '.' and part != '..')
        for part in file_path.split('/')):
        logging.debug(f"Skipping hidden file: {file_path}")
        return False
    if 'test' in file_path.lower():
        logging.debug(f"Skipping test file: {file_path}")
        return False
    for excluded_dir in excluded_dirs:
        if f"/{excluded_dir}/" in file_path or file_path.startswith(excluded_dir + "/"):
            logging.debug(f"Skipping excluded directory: {file_path}")
            return False
    for file_name in utility_or_config_files:
        if file_name in file_path:
            logging.debug(f"Skipping utility or config file: {file_path}")
            return False
    for doc_file in github_workflow_or_docs:
        doc_file_check = (doc_file in file_path if not doc_file.startswith(".") else
                 doc_file in os.path.basename(file_path))
        if doc_file_check:
            logging.debug(f"Skipping GitHub workflow or documentation file: {file_path}")
            return False
    return True

