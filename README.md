# GitHub2File

GitHub2File is a tool to download and process files from a GitHub repository, extracting and combining source code or other relevant files into a single output file.

## Features

- Download and process files from a GitHub repository.
- Process local zip files and directories.
- Filter files by programming language.
- Include or exclude specific directories and files.
- Convert IPython notebooks to Python scripts.
- Remove comments and docstrings from Python files.
- Optionally copy the output to the clipboard (MacOS only).
- Generate a file tree structure at the beginning of the output file.
- Preview the top N lines of each file.

## Installation

To install the package, run:

```bash
pip install .
```

## Supported Languages and File Types

GitHub2File supports the following languages and file types:

- **Python** (`.py`)
- **PDF** (`.pdf`)
- **IPython Notebooks** (`.ipynb`)
- **Markdown** (`.md`, `.markdown`, `.mdx`)
- **JavaScript** (`.js`)
- **Go** (`.go`)
- **HTML** (`.html`)
- **Mojo** (`.mojo`)
- **Java** (`.java`)
- **Lua** (`.lua`)
- **C** (`.c`, `.h`)
- **C++** (`.cpp`, `.h`, `.hpp`)
- **C#** (`.cs`)
- **Ruby** (`.rb`)
- **MATLAB** (`.m`)
- **Shell** (`.sh`)
- **TOML** (`.toml`)

## Usage

You can use GitHub2File either by downloading a repository directly from GitHub, processing a local zip file, or processing a local directory. Here are the different ways to call the script:

### Download and Process a GitHub Repository

```bash
python -m github2file --repo_url <repository_url> [options]
```

### Process a Local Zip File

```bash
python -m github2file --zip_file <path_to_zip_file> [options]
```

### Process a Local Directory

```bash
python -m github2file --folder <path_to_folder> [options]
```

### Options

- `--repo_url`: The URL of the GitHub repository to download.
- `--zip_file`: Path to the local zip file.
- `--folder`: Path to the local folder.
- `--lang`: The programming language(s) and format(s) of the repository (comma-separated). Default is `python`. Supported formats include `python`, `pdf`, and `ipynb`.
- `--keep-comments`: Keep comments and docstrings in the source code (only applicable for Python).
- `--branch_or_tag`: The branch or tag of the repository to download. Default is `master`.
- `--ipynb_nbconvert`: Convert IPython Notebook files to Python script files using nbconvert. Default is `True`.
- `--pdf_text_mode`: Convert PDF files to text for analysis (requires pdf filetype in --lang). Default is `False`.
- `--summarize`: Generate a summary of the code using Fabric. Default is `False`.
- `--fabric_args`: Arguments to pass to Fabric when using --summarize. Default is `literal`.
- `--pbcopy`: Copy the output to the clipboard. Default is `False`.
- `--debug`: Enable debug logging.
- `--include`: Comma-separated list of subfolders/patterns to focus on.
- `--exclude`: Comma-separated list of file patterns to exclude.
- `--excluded_dirs`: Comma-separated list of directories to exclude. Default is `docs,examples,tests,test,scripts,utils,benchmarks`. Note: Patterns listed here are automatically added to `--exclude` patterns, so you don't need to specify them in both places.
- `--name_append`: Append this string to the output file name.
- `--tree`: Prepend a file tree (generated via the 'tree' command) to the output file. Only works for local folders. The tree follows the same exclusion patterns specified by `--exclude` and `--excluded_dirs`.
- `--tree_flags`: Flags to pass to the 'tree' command (e.g., '-a -L 2'). If not provided, defaults will be used.
- `--topN`: Show the top N lines of each file in the output as a preview.

### Example Usage

#### Download and Process a GitHub Repository

```bash
python -m github2file --repo_url https://github.com/user/repo --lang python,markdown,pdf --pbcopy --excluded_dirs env
```

or 

```bash
python -m github2file --lang python,markdown --pbcopy --excluded_dirs env https://github.com/user/repo 
```
#### Process a Local Zip File

```bash
python -m github2file --zip_file /path/to/repo.zip --lang python,pdf --include src,lib --exclude test --keep-comments
```

#### Process a Local Directory

```bash
python -m github2file --folder /path/to/repo --lang python,pdf --excluded_dirs env,docs
```

### Advanced Usage

You can combine multiple options to fine-tune the processing:

```bash
python -m github2file --folder /path/to/repo --lang python,pdf --keep-comments --include src,lib --name_append processed --debug --pbcopy
```

#### Using File Tree and Top N Preview

To include a file tree structure and preview the top 10 lines of each file:

```bash
python -m github2file --folder /path/to/repo --lang python,pdf --tree --topN 10 --exclude test
```

The tree command respects exclusion patterns, so files and directories specified in `--exclude` and `--excluded_dirs` won't appear in the tree structure.

You can also customize the tree command with additional flags:

```bash
python -m github2file --folder /path/to/repo --tree --tree_flags "-a -L 3" --lang python
```

#### Processing PDF Files

To include PDF files in your output and extract their text content:

```bash
python -m github2file --folder /path/to/repo --lang python,pdf --pdf_text_mode
```

Without `--pdf_text_mode`, PDFs will be included in the output but only as placeholders. With this flag enabled, the tool will extract the text content from the PDFs and include it in the output file.

#### Simplified Directory Exclusion

You now only need to specify directories to exclude once. The tool automatically applies patterns from `--excluded_dirs` to file exclusions:

```bash
# Before:
# python -m github2file --excluded_dirs env,.venv,.mind --exclude env,.venv,.mind --lang python,md,org,txt .

# Now (simplified):
python -m github2file --excluded_dirs env,.venv,.mind --lang python,md,org,txt .
```

This will exclude the specified directories from both directory traversal and the file tree output.

#### Code Summarization with Fabric

To generate a summary of your code using Fabric:

```bash
python -m github2file --folder /path/to/repo --lang python --summarize
```

This requires Fabric to be installed and accessible in your PATH. The summary will be saved to a separate file with "_summary" appended to the filename.

You can customize the Fabric command with additional arguments:

```bash
python -m github2file --folder /path/to/repo --lang python --summarize --fabric_args "literal analyze"
```

This will run `fabric --literal analyze` on the generated output file.

## Contributing

If you want to contribute to this project, please fork the repository and create a pull request.

