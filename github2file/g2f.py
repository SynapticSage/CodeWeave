import os
import sys
import requests
import zipfile
import io
import ast
import logging
import argparse

def is_file_type(file_path, file_extensions):
    """Check if the file has any of the specified file extensions."""
    return any(file_path.endswith(ext) for ext in file_extensions)

def is_likely_useful_file(file_path, lang):
    """Determine if the file is likely to be useful by excluding certain directories and specific file types."""
    excluded_dirs = ["docs", "examples", "tests", "test", "scripts", "utils", "benchmarks"]
    utility_or_config_files = []
    github_workflow_or_docs = [".github", ".gitignore", "LICENSE", "README"]

    if lang == "python":
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

    if any(part.startswith('.') for part in file_path.split('/')):
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

def is_test_file(file_content, lang):
    """Determine if the file content suggests it is a test file."""
    test_indicators = []
    if lang == "python":
        test_indicators = ["import unittest", "import pytest", "from unittest", "from pytest"]
    elif lang == "go":
        test_indicators = ["import testing", "func Test"]
    elif lang == "js":
        test_indicators = ["describe(", "it(", "test(", "expect(", "jest", "mocha"]
    return any(indicator in file_content for indicator in test_indicators)

def has_sufficient_content(file_content, min_line_count=10):
    """Check if the file has a minimum number of substantive lines."""
    lines = [line for line in file_content.split('\n') if line.strip() and not line.strip().startswith(('#', '//'))]
    return len(lines) >= min_line_count

def remove_comments_and_docstrings(source):
    """Remove comments and docstrings from the Python source code."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and ast.get_docstring(node):
            node.body = node.body[1:]  # Remove docstring
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
            node.value.s = ""  # Remove comments
    return ast.unparse(tree)

def download_repo(repo_url, output_file, lang, keep_comments=False, branch_or_tag="master"):
    """Download and process files from a GitHub repository."""
    download_url = f"{repo_url}/archive/refs/heads/{branch_or_tag}.zip"

    print(download_url)
    response = requests.get(download_url)

    if response.status_code == 200:
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        process_zip_file_object(zip_file, output_file, lang, keep_comments)
    else:
        print(f"Failed to download the repository. Status code: {response.status_code}")
        sys.exit(1)


def process_zip_file(zip_file:str, output_file, lang, keep_comments=False):
    """ Process files from a local .zip file. """
    with zipfile.ZipFile(zip_file, 'r') as zip_file:
        process_zip_file_object(zip_file, output_file, lang, keep_comments)


def process_zip_file_object(zip_file:zipfile.ZipFile, output_file, langs, keep_comments=False):
    """Process files from a local .zip file."""
    file_extensions = [f".{lang}" for lang in langs]
    with open(output_file, "w", encoding="utf-8") as outfile:
        for file_path in zip_file.namelist():
            if (file_path.endswith("/") 
                or not is_file_type(file_path, file_extensions) 
                or not any(is_likely_useful_file(file_path, lang) for lang in langs)):
                continue
            file_content = zip_file.read(file_path).decode("utf-8")

            if any(is_test_file(file_content, lang) for lang in langs) or not has_sufficient_content(file_content):
                continue
            if "python" in langs and not keep_comments:
                try:
                    file_content = remove_comments_and_docstrings(file_content)
                except SyntaxError:
                    continue

            comment_prefix = "// " if any(lang in ["go", "js"] for lang in langs) else "# "
            outfile.write(f"{comment_prefix}File: {file_path}\n")
            outfile.write(file_content)
            outfile.write("\n\n")

def create_argument_parser():
    parser = argparse.ArgumentParser(description='Download and process files from a GitHub repository.')
    parser.add_argument('--zip_file', type=str, help='Path to the local .zip file')
    parser.add_argument('--lang', type=str, default='python', help='The programming language(s) of the repository (comma-separated)')
    parser.add_argument('--keep-comments', action='store_true', help='Keep comments and docstrings in the source code (only applicable for Python)')
    parser.add_argument('--branch_or_tag', type=str, help='The branch or tag of the repository to download', default="master")
    parser.add_argument('repo_url', type=str, help='The URL of the GitHub repository',
                        default="", nargs='?')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser

def main(args=None):
    parser = create_argument_parser()
    try:
        args = parser.parse_args(args)
        if args.debug:
            # Enable debug logging
            logging.basicConfig(level=logging.DEBUG)
            logging.debug("Debug logging enabled")
            logging.debug(f"Arguments: {args}")
        langs = [lang.strip() for lang in args.lang.split(',')]
        if args.repo_url:
            output_file = f"{args.repo_url.split('/')[-1]}_{args.lang}.txt"
            download_repo(args.repo_url, output_file, langs, args.keep_comments, args.branch_or_tag)
        else:
            output_file = f"{os.path.splitext(os.path.basename(args.zip_file))[0]}_{args.lang}.txt"
            with zipfile.ZipFile(args.zip_file, 'r') as zf:
                process_zip_file_object(zf, output_file, langs, args.keep_comments)

        print(f"Combined {args.lang.capitalize()} source code saved to {output_file}")
    except argparse.ArgumentError as e:
        print(str(e))
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
