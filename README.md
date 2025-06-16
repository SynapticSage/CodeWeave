# CodeWeave

<div align="center">
  <img src="assets/logo.png" alt="CodeWeave Logo" width="200" height="200">
  
  [![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
</div>

CodeWeave is a powerful command-line tool that intelligently aggregates source code from GitHub repositories, local zip files, or directories, weaving them into organized, AI-ready output files. Perfect for code analysis, documentation, and AI-assisted development workflows.

## Quick Start

```bash
# Process current directory for Python files with rich progress bars
codeweave . --lang python

# AI-powered: Generate commands from natural language
codeweave --prompt "extract python files excluding tests and virtual environments"

# Download and process a GitHub repository with beautiful terminal output
codeweave https://github.com/user/repo --lang python,markdown

# Process with file tree and exclude common directories - works from anywhere!
codeweave /path/to/project --lang python --tree --excluded_dirs .venv,node_modules
```

## 🚀 Key Features

### 📁 Input & Processing
- **Multiple Sources**: GitHub repos, ZIP files, local directories
- **Smart Language Detection**: 15+ programming languages and file types
- **Performance Optimized**: Fast traversal that skips excluded directories
- **Advanced Filtering**: Include/exclude patterns for directories and files

### 🎨 User Experience  
- **Rich Terminal Interface**: Beautiful progress bars and colored output
- **Global Script**: Works from any directory with environment detection
- **File Tree Generation**: Visual directory structure with exclusions
- **Real-time Progress**: Live updates with time estimates and statistics

### 🛠️ Advanced Features
- **Content Processing**: Remove comments, convert notebooks, extract PDF text
- **External Programs**: Run custom commands on specific file types
- **Code Summarization**: Generate summaries using Fabric integration
- **Output Control**: Clipboard copy, naming, preview options
- **Developer Tools**: Debug logging, grouped CLI options, extensibility

### 🤖 AI-Powered Command Generation
- **Natural Language Processing**: Convert plain English to CodeWeave commands
- **Multi-Provider Support**: OpenAI, Anthropic, OpenRouter via LiteLLM
- **Smart Auto-Detection**: Automatically recognizes natural language vs paths
- **Interactive Confirmation**: Preview and approve generated commands

## ✨ Rich Terminal Experience

CodeWeave features a beautiful, modern terminal interface that makes code processing a pleasure:

### 🎨 Visual Features
- **📊 Rich Progress Bars**: Real-time progress with file counts, processing speed, and time remaining
- **🎯 Smart Status Display**: Color-coded messages with clear visual hierarchy
- **📋 Configuration Summary**: Elegant table showing all your processing settings
- **✅ Completion Reports**: Detailed summary with file size, statistics, and success indicators
- **🌈 Syntax Highlighting**: Enhanced error messages and debugging output

### 🚀 User Experience
- **📱 Live Updates**: See exactly which file is being processed in real-time  
- **⏱️ Time Estimates**: Know how long large operations will take
- **🎛️ Front Matter Display**: Clear overview of what's being processed before it starts
- **📈 Processing Statistics**: Track files processed, skipped, and total progress
- **🎨 Modern Design**: Professional appearance that's easy on the eyes

### Example Output
```
╭─────────────────────────────────────────────────╮
│ CodeWeave - Intelligent source code aggregation │
╰─────────────────────────────────────────────────╯
                    Processing Configuration                    
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting            ┃ Value                                  ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Input Type         │ Local Folder                           │
│ Source             │ /path/to/your/project                  │
│ Languages          │ python, markdown                       │
│ Output File        │ project_python,markdown.txt            │
└────────────────────┴────────────────────────────────────────┘

Processing folder...
⠋ Scanning: src                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━             
⠋ Processing: main.py...           ━━━━━━━━━━━━━━━━━━━           68% 0:00:02

╭────────────────────────────────── Summary ───────────────────────────────────╮
│ ✓ Processing Complete!                                                       │
│                                                                              │
│ Output File: outputs/project_python,markdown.txt                             │
│ File Size: 2.45 MB (2,567,890 bytes)                                         │
│ Languages: python, markdown                                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Installation

### Easy Installation (Recommended)

```bash
git clone https://github.com/user/codeweave.git
cd codeweave
make setup
```

This installs CodeWeave, creates a global `codeweave` command, and adds a `g2f` alias for backward compatibility.

### AI-Powered Features (Optional)

For natural language command generation, install AI dependencies:

```bash
# Recommended: Full AI provider support via LiteLLM
pip install codeweave[ai]

# Alternative: Basic AI support via OpenAI SDK
pip install codeweave[ai-basic]

# Manual installation
pip install litellm  # Preferred - supports all providers
pip install openai   # Fallback - OpenAI/OpenRouter only
```

**Alternative installations:**
```bash
make setup-basic    # Install without g2f alias
make install-global # Install global command only
```

### Manual Installation Options

**Standard Installation:**
```bash
git clone https://github.com/user/codeweave.git
cd codeweave
make install
```

**Development Installation:**
```bash
git clone https://github.com/user/codeweave.git
cd codeweave
make install-dev
```

**Direct from GitHub:**
```bash
pip install git+https://github.com/user/codeweave.git
```

### Usage After Installation

- **🌍 Global command:** `codeweave <path>` - Works from any directory with smart environment detection
- **⚡ Legacy alias:** `g2f <path>` (after `make shell-alias` or `make setup`)
- **📦 Short alias:** `cw <path>` (available after pip install)
- **🐍 Python module:** `python -m codeweave <path>`

**Note:** The global `codeweave` command uses intelligent environment detection to automatically find your CodeWeave installation, even when you're in different directories or using different Python environments!

## Supported Languages and File Types

CodeWeave supports the following languages and file types:

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

## 🤖 AI Integration

### Natural Language Command Generation

CodeWeave can generate commands from plain English descriptions, making it easier to use complex options.

#### Configuration

Set up your AI provider via environment variables:

```bash
# Primary configuration
export CODEWEAVE_API_KEY="your_api_key_here"
export CODEWEAVE_AI_PROVIDER="openrouter"  # openrouter|openai|anthropic
export CODEWEAVE_AI_MODEL="openai/gpt-4"   # specific model (optional)

# Provider-specific keys (fallback)
export OPENROUTER_API_KEY="your_openrouter_key"
export OPENAI_API_KEY="your_openai_key" 
export ANTHROPIC_API_KEY="your_anthropic_key"
```

#### Usage Examples

**Explicit Prompt Mode:**
```bash
# Generate command from description
codeweave --prompt "extract all python files but skip tests and virtual environments"
# Generated: codeweave . --lang python --excluded_dirs tests,test,.venv,venv

# Specify AI provider and model
codeweave --prompt "get markdown and python files with file tree" --ai-provider anthropic --ai-model claude-3-sonnet

# Skip confirmation (auto-execute)
codeweave --prompt "process github repo for javascript" --no-confirm
```

**Auto-Detection Mode:**
```bash
# CodeWeave automatically detects natural language vs paths
codeweave "analyze this project for Python code excluding tests"
codeweave "download repo and get all JavaScript files with tree structure"
codeweave "extract markdown files from current directory"
```

**AI Provider Options:**
- `--ai-provider openrouter` (default) - Access 100+ models via OpenRouter
- `--ai-provider openai` - Direct OpenAI API access  
- `--ai-provider anthropic` - Direct Anthropic API access
- `--ai-model model-name` - Specify exact model (e.g., gpt-4, claude-3-sonnet)
- `--no-confirm` - Skip confirmation and run generated command directly

## Usage

You can use GitHub2File either by downloading a repository directly from GitHub, processing a local zip file, or processing a local directory. Here are the different ways to call the script:

### Basic Usage

The tool accepts a single input argument that can be a GitHub URL, local zip file, or directory path:

```bash
# GitHub repository
codeweave https://github.com/user/repo

# Local directory
codeweave /path/to/folder

# Local zip file
codeweave /path/to/archive.zip
```

You can also use explicit parameters:

```bash
# Explicit parameters
codeweave --repo https://github.com/user/repo
codeweave --folder /path/to/folder
codeweave --zip /path/to/archive.zip
```

### Options

#### Input Sources

- `<input>`: A GitHub repository URL, a local .zip file, or a local folder.
- `--repo`: The name of the GitHub repository to download.
- `--zip`: Path to the local zip file.
- `--folder`: Path to the local folder.
- `--branch_or_tag`: The branch or tag of the repository to download. Default is `master`.

#### File Selection & Filtering

- `--lang`: The programming language(s) and format(s) of the repository (comma-separated, e.g., python,pdf). Default is `python`.
- `--include`: Comma-separated list of subfolders/patterns to focus on.
- `--exclude`: Comma-separated list of file patterns to exclude.
- `--excluded_dirs`: Comma-separated list of directories to exclude. Default is `docs,examples,tests,test,scripts,utils,benchmarks`. Note: Patterns listed here are automatically added to `--exclude` patterns, so you don't need to specify them in both places.

#### Content Processing

- `--keep-comments`: Keep comments and docstrings in the source code (only applicable for Python).
- `--ipynb_nbconvert`: Convert IPython Notebook files to Python script files using nbconvert. Default is `True`.
- `--pdf_text_mode`: Convert PDF files to text for analysis (requires pdf filetype in --lang). Default is `False`.
- `--topN`: Show the top N lines of each file in the output as a preview.
- `--tree`: Prepend a file tree (generated via the 'tree' command) to the output file. Only works for local folders. The tree follows the same exclusion patterns specified by `--exclude` and `--excluded_dirs`.
- `--tree_flags`: Flags to pass to the 'tree' command (e.g., '-a -L 2'). If not provided, defaults will be used.

#### External Program Integration

- `--program`: Run a specified program on each file matching a given filetype. Format: `filetype=command`. The command will be run with the file path as an argument, and the output will be included in the output file. Use `*` as the filetype to run the command on all files.
- `--nosubstitute`: Show both program output AND file content when using `--program`. Without this flag (default behavior), only the program output will be shown instead of the file content.
- `--summarize`: Generate a summary of the code using Fabric. Default is `False`.
- `--fabric_args`: Arguments to pass to Fabric when using --summarize. Default is `literal`.

#### AI Integration

- `--prompt`: Generate CodeWeave command from natural language description.
- `--ai-provider`: AI provider to use for command generation (openrouter, openai, anthropic). Default is `openrouter`.
- `--ai-model`: Specific AI model to use (e.g., gpt-4, claude-3-sonnet).
- `--no-confirm`: Skip confirmation prompt and run generated command directly.

#### Output Options

- `--name_append`: Append this string to the output file name.
- `--pbcopy`: Copy the output to clipboard (macOS only). Default is `False`.

#### Debugging Options

- `--debug`: Enable debug logging.
- `--pdb`: Drop into pdb on error.
- `--pdb_fromstart`: Drop into pdb from start.

### Example Usage

#### Download and Process a GitHub Repository

```bash
codeweave https://github.com/user/repo --lang python,markdown,pdf --pbcopy --excluded_dirs env
```

or using the explicit parameter:

```bash
codeweave --repo https://github.com/user/repo --lang python,markdown --excluded_dirs env
```

#### Process a Local Zip File

```bash
codeweave /path/to/repo.zip --lang python,pdf --include src,lib --exclude test --keep-comments
```

or using the explicit parameter:

```bash
codeweave --zip /path/to/repo.zip --lang python,pdf --include src,lib
```

#### Process a Local Directory

```bash
codeweave /path/to/folder --lang python,pdf --excluded_dirs env,docs
```

or using the explicit parameter:

```bash
codeweave --folder /path/to/folder --lang python,pdf --excluded_dirs env,docs
```

### Advanced Usage

You can combine multiple options to fine-tune the processing:

```bash
codeweave --folder /path/to/repo --lang python,pdf --keep-comments --include src,lib --name_append processed --debug --pbcopy
```

#### Using File Tree and Top N Preview

To include a file tree structure and preview the top 10 lines of each file:

```bash
codeweave --folder /path/to/repo --lang python,pdf --tree --topN 10 --exclude test
```

The tree command respects exclusion patterns, so files and directories specified in `--exclude` and `--excluded_dirs` won't appear in the tree structure.

You can also customize the tree command with additional flags:

```bash
codeweave --folder /path/to/repo --tree --tree_flags "-a -L 3" --lang python
```

#### Running Programs on Specific Filetypes

To run a specific program on each file of a certain type:

```bash
codeweave --folder /path/to/repo --lang python --program "python=wc -l"
```

This will run `wc -l` on each Python file and include the output before the file content.

You can also use `*` as a wildcard to run the program on all files:

```bash
codeweave --folder /path/to/repo --lang python,js --program "*=stat"
```

This will run the `stat` command on all files regardless of filetype, showing only the output of the `stat` command in the output file.

If you want to see both the program output AND the original file content, use the `--nosubstitute` flag:

```bash
codeweave --folder /path/to/repo --lang python --program "python=wc -l" --nosubstitute
```

This will run `wc -l` on each Python file, showing both the line count output AND the original file content in the output file.

#### Processing PDF Files

To include PDF files in your output and extract their text content:

```bash
codeweave --folder /path/to/repo --lang python,pdf --pdf_text_mode
```

Without `--pdf_text_mode`, PDFs will be included in the output but only as placeholders. With this flag enabled, the tool will extract the text content from the PDFs and include it in the output file.

#### Simplified Directory Exclusion

You now only need to specify directories to exclude once. The tool automatically applies patterns from `--excluded_dirs` to file exclusions:

```bash
# Before:
# codeweave --excluded_dirs env,.venv,.mind --exclude env,.venv,.mind --lang python,md,org,txt .

# Now (simplified):
codeweave --excluded_dirs env,.venv,.mind --lang python,md,org,txt .
```

This will exclude the specified directories from both directory traversal and the file tree output.

#### Code Summarization with Fabric

To generate a summary of your code using Fabric:

```bash
codeweave --folder /path/to/repo --lang python --summarize
```

This requires Fabric to be installed and accessible in your PATH. The summary will be saved to a separate file with "_summary" appended to the filename.

You can customize the Fabric command with additional arguments:

```bash
codeweave --folder /path/to/repo --lang python --summarize --fabric_args "literal analyze"
```

This will run `fabric --literal analyze` on the generated output file.

## Performance Tips

For optimal performance with large codebases:

1. **Use directory exclusions**: Always exclude large directories like `.venv`, `node_modules`, `.git`
   ```bash
   codeweave . --excluded_dirs .venv,node_modules,.git,dist,build
   ```

2. **Leverage pattern exclusions**: Use `--exclude` for file patterns
   ```bash
   codeweave . --exclude "*.pyc,*.log,*.tmp"
   ```

3. **Limit language scope**: Only process languages you need
   ```bash
   codeweave . --lang python,markdown  # Instead of processing all file types
   ```

4. **The tool automatically optimizes**: Excluded directories are skipped entirely during traversal, not just filtered afterward

## CLI Help

The tool provides comprehensive help with grouped options:

```bash
codeweave --help
```

Options are organized into logical groups:
- **Input Sources**: Repository, zip, folder, branch selection
- **File Selection & Filtering**: Language, include/exclude patterns
- **Content Processing**: Comments, notebooks, PDFs, tree generation
- **External Program Integration**: Custom commands, summarization
- **Output Options**: File naming, clipboard integration
- **Debugging Options**: Logging, debugging tools

## Troubleshooting

### Common Issues

**"No source code found to save"**
- Check your `--lang` parameter matches your file types
- Verify `--excluded_dirs` isn't excluding your target files
- Use `--debug` to see what files are being processed

**Slow performance on large repositories**
- Add common large directories to `--excluded_dirs`: `.venv`, `node_modules`, `.git`
- Use `--include` to focus on specific directories
- Consider using `--topN` for preview instead of full files

**Tree command not found**
- Install `tree` command: `brew install tree` (macOS) or `apt-get install tree` (Ubuntu)
- Or skip tree generation by omitting `--tree` flag

**PDF text extraction fails**
- Ensure `pdfminer` is installed: `pip install pdfminer.six`
- Some PDFs may not support text extraction

**Global `codeweave` command not found or not working**
- The smart global script automatically detects your CodeWeave installation
- It searches common locations: `~/Code/repos/github2file`, `~/github2file`, etc.
- Uses virtual environments when found: `~/Code/repos/github2file/env/bin/python`
- To debug: Run `which codeweave` to see if installed, then check error messages
- Manual install: `sudo make global-script` from the project directory

**"CodeWeave is not installed or not accessible" error**
- The global script tried multiple locations but couldn't find a working installation
- Try: `python3 -c "import codeweave; print(codeweave.__file__)"` to check if available
- Install globally: `pip install .` from the project directory  
- Or run directly: `cd /path/to/github2file && python -m codeweave <args>`

## Contributing

If you want to contribute to this project, please fork the repository and create a pull request.

### Development Setup

```bash
git clone https://github.com/user/codeweave.git
cd codeweave
make install-dev
make test  # Run tests
```

