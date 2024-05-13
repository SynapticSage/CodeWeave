# GitHub Repository to File Converter

This Python script allows you to download and process files from a GitHub repository, making it easier to share code with chatbots that have large context capabilities but don't automatically download code from GitHub.

## Features

- Download and process files from a GitHub repository.
- Support for both public and private repositories.
- Filter files based on programming language (Python or Go).
- Exclude certain directories, file types, and test files.
- Remove comments and docstrings from Python source code (optional).
- Specify a branch or tag to download from (default: "master").

## Installation
Clone the repository and install the package using:
```bash
pip install .
```

## Usage
`github2file` can be executed from the command line with several options:

### Command Syntax
```bash
python g2f.py [options] <repository_url>
```

### Options
- `<repository_url>`: URL of the GitHub repository (required positional argument).
- `--zip_file <path>`: Path to a local zip file to process.
- `--folder <path>`: Path to a local folder to process.
- `--lang <languages>`: Specify the programming languages as a comma-separated list. Defaults to `python`.
- `--keep-comments`: Keep comments and docstrings in Python files.
- `--branch_or_tag <name>`: Download from a specific branch or tag. Defaults to `master`.
- `--debug`: Enable debug logging for more verbose output.
- `--include <patterns>`: Include files or directories matching these comma-separated patterns.
- `--exclude <patterns>`: Exclude files or directories matching these comma-separated patterns.
- `--excluded_dirs <dirs>`: Directories to exclude by default (e.g., `docs,examples,tests`).
- `--name_append <string>`: Append a custom string to the output file name.
- `--ipynb_nbconvert`: Convert Jupyter notebooks to Python scripts. Enabled by default.

## Examples

### Downloading and Processing from a GitHub Repository
```bash
python g2f.py --lang py,ipynb,md --exclude_dirs test,docs https://github.com/huggingface/transformers
```
dumps all python, ipnb, and markdown files, excluding the test and docs folder

### Processing a Local Zip File
```bash
python g2f.py --zip_file path/to/file.zip --lang py --keep-comments
```

For further information and help with command-line arguments:
```bash
python g2f.py -h
```

