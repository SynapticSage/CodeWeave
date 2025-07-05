import os
import sys
import requests
import zipfile
import io
import logging
import argparse
import subprocess
from tqdm.auto import tqdm
from pdfminer.high_level import extract_text
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.logging import RichHandler
from rich import print as rprint
from rich.prompt import Prompt, Confirm

from codeweave.utils.path import (
    should_exclude_file,
    inclusion_violate,
    extract_git_folder,
    is_test_file,
    is_file_type,
    is_likely_useful_file,
    lookup_file_extension,
    file_extension_dict,
)
from codeweave.utils.file import has_sufficient_content, remove_comments_and_docstrings
from codeweave.utils.jupyter import convert_ipynb_to_py

# Common binary file extensions
BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.svg',  # Images
    '.mp3', '.mp4', '.avi', '.mov', '.wav',  # Audio/Video
    '.zip', '.tar', '.gz', '.rar', '.7z',  # Archives
    '.exe', '.dll', '.so', '.dylib',  # Executables
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',  # Documents (except PDF which has special handling)
    '.pyc', '.pyo', '.class',  # Compiled files
    '.db', '.sqlite', '.pickle',  # Data files
}

def is_binary_file(file_path):
    """Check if a file is likely binary based on its extension."""
    _, ext = os.path.splitext(file_path.lower())
    return ext in BINARY_EXTENSIONS

# Optional AI imports - only load if available
try:
    from codeweave.utils.ai import (
        is_natural_language_input,
        generate_codeweave_command,
        confirm_and_execute_command,
    )
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

def setup_logging(debug_flag):
    """Setup logging configuration with rich handler."""
    log_level = logging.DEBUG if debug_flag else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

def download_repo(args, output_file_path, scan_only=False):
    """Download and process files from a GitHub repository.
    
    Args:
        args: Command line arguments
        output_file_path: Path to write output
        scan_only: If True, only scan for extensions without processing files
    """
    import tempfile
    
    download_url = f"{args.repo}/archive/refs/heads/{args.branch_or_tag}.zip"

    logging.info(f"Download URL: {download_url}")
    response = requests.get(download_url)

    if response.status_code == 200:
        # Save to temporary file in /tmp
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.zip', dir='/tmp', delete=False) as temp_zip:
            temp_zip.write(response.content)
            temp_path = temp_zip.name
            logging.debug(f"Downloaded ZIP saved to temporary file: {temp_path}")
        
        # Process the ZIP file
        with zipfile.ZipFile(temp_path, 'r') as zip_obj:
            collected_extensions = set()
            process_zip_object(zip_obj, args, output_file_path, collected_extensions, scan_only)
            args.collected_extensions = collected_extensions
        
        # Note: We don't delete the temp file - let the OS clean it up from /tmp
        logging.debug("Temporary ZIP file left in /tmp for OS cleanup")
    else:
        logging.error(f"Failed to download the repository. Status code: {response.status_code}")
        sys.exit(1)

def process_zip(args: argparse.Namespace, output_file_path=None):
    """Process files from a local .zip file."""
    with zipfile.ZipFile(args.zip, 'r') as zip_obj:
        collected_extensions = set()
        process_zip_object(zip_obj, args, output_file_path, collected_extensions)
        args.collected_extensions = collected_extensions

def process_zip_object(zip_obj, args: argparse.Namespace, output_file_path=None, collected_extensions=None, scan_only=False):
    """Process files from a local .zip file.
    
    Args:
        zip_obj: ZipFile object to process
        args: Command line arguments
        output_file_path: Path to write output
        collected_extensions: Set to collect file extensions
        scan_only: If True, only scan for extensions without processing files
    """
    console = Console()
    
    if collected_extensions is None:
        collected_extensions = set()
    
    # Use args.output_file_path if output_file_path is not provided
    if output_file_path is None and hasattr(args, "output_file_path"):
        output_file_path = args.output_file_path
    
    # Parse the program argument if provided
    program_filetype = None
    program_command = None
    if args.program:
        program_filetype, program_command = parse_program_arg(args.program)
        if program_filetype and program_command:
            console.print(f"[blue]Will run[/blue] [bold cyan]'{program_command}'[/bold cyan] [blue]on files of type[/blue] [bold cyan]'{program_filetype}'[/bold cyan]")
        else:
            console.print("[red]Invalid program format, ignoring --program option[/red]")
            
    with open(output_file_path, "w", encoding="utf-8") as outfile:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Processing zip files", total=len(zip_obj.namelist()))
            
            for file_path in zip_obj.namelist():
                progress.update(task, description=f"Processing: {os.path.basename(file_path)[:30]}...")
                
                # During scan mode, we want to collect all extensions (skip directories only)
                if not scan_only:
                    if (file_path.endswith("/")
                        or not is_file_type(file_path, args.lang)
                        or not is_likely_useful_file(file_path, args.lang, args)
                        or should_exclude_file(file_path, args)):
                        progress.advance(task)
                        continue

                    if args.include:
                        confirm_include = any(include in file_path for include in args.include)
                        if not confirm_include:
                            logging.debug(f"Skipping file: {file_path}")
                            progress.advance(task)
                            continue
                    else:
                        # Default to include
                        confirm_include = True
                    if not confirm_include:
                        progress.advance(task)
                        continue
                else:
                    # In scan mode, skip directories only
                    if file_path.endswith("/"):
                        progress.advance(task)
                        continue

                logging.debug(f"Processing file: {file_path}")
                
                # Collect file extension
                _, ext = os.path.splitext(file_path)
                if ext:
                    collected_extensions.add(ext.lower())
                
                # If we're only scanning for extensions, skip the rest
                if scan_only:
                    progress.advance(task)
                    continue
                
                # --- Run program on specific filetype if requested ---
                program_output = None
                if program_filetype and program_command:
                    # For zip files, we need to extract the file to a temporary location to run the program
                    if program_filetype in lookup_file_extension(file_path) or program_filetype == '*':
                        # Create a temporary file
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_file.write(zip_obj.read(file_path))
                            temp_path = temp_file.name
                        
                        # Run the program on the temporary file
                        program_output = run_program_on_file(temp_path, program_command)
                        logging.debug(f"Program output for {file_path}: {program_output}")
                        
                        # Clean up the temporary file
                        os.unlink(temp_path)
                        
                        # Need to re-read the file since we've consumed it
                        zip_obj.open(file_path)
                
                # Skip binary files (except PDF which has special handling)
                if is_binary_file(file_path) and not (file_path.endswith('.pdf') and 'pdf' in args.lang):
                    logging.debug(f"Skipping binary file: {file_path}")
                    progress.advance(task)
                    continue
                
                if file_path.endswith('.pdf') and 'pdf' in args.lang:
                    if args.pdf_text_mode:
                        file_content = extract_text(io.BytesIO(zip_obj.read(file_path)))
                        logging.debug(f"Extracted text from PDF: {file_path}")
                    else:
                        # Just indicate this is a PDF file but don't extract text
                        file_content = "[PDF file - use --pdf_text_mode to extract text]"
                elif file_path.endswith('.ipynb') and args.ipynb_nbconvert:
                    file_content = zip_obj.read(file_path).decode("utf-8")
                    file_content = convert_ipynb_to_py(file_content)
                else:
                    try:
                        file_content = zip_obj.read(file_path).decode("utf-8")
                    except UnicodeDecodeError:
                        logging.debug(f"Skipping file due to encoding issues: {file_path}")
                        progress.advance(task)
                        continue

                if any(is_test_file(file_content, lang) for lang in args.lang) or not has_sufficient_content(file_content):
                    progress.advance(task)
                    continue
                if "python" in args.lang and not args.keep_comments:
                    try:
                        file_content = remove_comments_and_docstrings(file_content)
                    except SyntaxError:
                        progress.advance(task)
                        continue

                comment_prefix = "// " if any(lang in ["go", "js"] for lang in args.lang) else "# "
                outfile.write(f"{comment_prefix}File: {file_path}\n")
                
                # If the program ran on this file, handle the output according to --nosubstitute flag
                if program_output:
                    outfile.write(f"{comment_prefix}Program output:\n")
                    outfile.write(program_output)
                    outfile.write("\n\n")
                    
                    # If --nosubstitute is provided, include file content as well
                    # Otherwise (default), only show program output and skip file content
                    if not args.nosubstitute:
                        # Skip writing file content since we're substituting with program output
                        outfile.write("\n\n")
                        progress.advance(task)
                        continue

                # If topN is specified, show top N lines with a header comment
                if args.topN:
                    lines = file_content.splitlines()
                    top_lines = lines[:args.topN]
                    outfile.write(f"{comment_prefix}(top {args.topN} lines)\n")
                    outfile.write('\n'.join(top_lines))
                    outfile.write("\n\n")
                    outfile.write(file_content)
                else:
                    outfile.write(file_content)
                    
                outfile.write("\n\n")
                progress.advance(task)

def process_folder(args: argparse.Namespace, output_file_path, scan_only=False):
    """
    Processes a local folder: 
    1) Optionally prepends a file tree (via the 'tree' command).
    2) Gathers and writes out source files that match the user's language and 
       filtering criteria.
    3) Optionally runs a program on each file of a specific filetype.
    
    Args:
        args: Command line arguments
        output_file_path: Path to write output
        scan_only: If True, only scan for extensions without processing files
    """
    
    # Initialize collected extensions
    collected_extensions = set()
    
    # Parse the program argument if provided
    program_filetype = None
    program_command = None
    if args.program:
        program_filetype, program_command = parse_program_arg(args.program)
        if program_filetype and program_command:
            logging.info(f"Will run '{program_command}' on files of type '{program_filetype}'")
        else:
            logging.error("Invalid program format, ignoring --program option")

    # --- 1) Generate a file tree using the 'tree' command, applying exclusions ---
    if args.tree and not scan_only:
        tree_cmd = ['tree']

        # If the user passed extra flags via --tree_flags, add them here
        if args.tree_flags:
            tree_cmd.extend(args.tree_flags.split())

        # Build a list of exclusion patterns from excluded dirs and exclude file patterns
        exclude_patterns = []
        if args.excluded_dirs:
            exclude_patterns.extend(args.excluded_dirs)
        if args.exclude:
            exclude_patterns.extend(args.exclude)

        # If we have any patterns to exclude, pass them to `tree -I "...|...|..."`
        # and also use --prune to avoid printing empty directories
        if exclude_patterns:
            # Create a single string with '|' separating each pattern
            # e.g. docs|examples|test|scripts
            tree_exclude_regex = '|'.join(exclude_patterns)
            # Add the exclude and prune flags to the tree command
            tree_cmd.extend(['-I', tree_exclude_regex, '--prune'])

        # Finally, append the folder we want to run 'tree' on
        tree_cmd.append(args.folder)

        try:
            result = subprocess.run(tree_cmd, capture_output=True, text=True, check=True)
            tree_output = result.stdout
        except subprocess.CalledProcessError as e:
            logging.error("Failed to generate file tree via 'tree' command")
            tree_output = f'Error generating file tree: {e}'

        # Write the tree output to our final file (wipe it first)
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(tree_output)
            outfile.write('\n\n')
        logging.info('File tree prepended to output file.')

    # --- 2) Process/append actual files that meet your criteria ---
    from functools import reduce
    from operator import ior
    mode = 'a' if args.tree else 'w'
    
    console = Console()
    
    # Count total files for progress tracking
    total_files = sum(len(files) for _, _, files in os.walk(args.folder))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        folder_task = progress.add_task("Scanning folders", total=None)
        file_task = progress.add_task("Processing files", total=total_files)
        
        processed_files = 0
        
        for root, dirs, files in os.walk(args.folder):
            progress.update(folder_task, description=f"Scanning: {os.path.basename(root) or 'root'}")
            logging.debug(f'In folder: {root}')
            
            # Skip excluded directories during os.walk() - modify dirs in-place
            dirs[:] = [d for d in dirs if d not in args.excluded_dirs]
            
            # Early check: skip if current root contains any excluded directory
            if any(excluded_dir in root for excluded_dir in args.excluded_dirs):
                logging.debug(f'Excluded directory, skipping entire folder: {root}')
                continue
                
            logging.debug(f'File list:\n{files}')

            for file in files:
                file_path = os.path.join(root, file)
                progress.update(file_task, description=f"Processing: {os.path.basename(file_path)[:30]}...")

                # During scan mode, we want to collect all extensions
                if not scan_only:
                    # Build your dictionary of "skip" conditions
                    we_should_examine = {
                        'bad filetype': not is_file_type(file, args.lang),
                        'not useful': not any(is_likely_useful_file(file, lang, args) for lang in args.lang),
                        'should exclude': should_exclude_file(file, args),
                        'inclusion violate': inclusion_violate(file, args),
                    }

                    if reduce(ior, we_should_examine.values()):
                        logging.debug(f'Skipping file: {file_path}')
                        logging.debug(f'Reasons: {we_should_examine}')
                        progress.advance(file_task)
                        continue

                # Note: Directory exclusion now handled at folder level above
                
                # Collect file extension
                _, ext = os.path.splitext(file_path)
                if ext:
                    collected_extensions.add(ext.lower())
                
                # If we're only scanning for extensions, skip the rest
                if scan_only:
                    progress.advance(file_task)
                    continue
                    
                # Skip binary files (except PDF which has special handling)
                if is_binary_file(file_path) and not (file_path.endswith('.pdf') and 'pdf' in args.lang):
                    logging.debug(f"Skipping binary file: {file_path}")
                    progress.advance(file_task)
                    continue
                    
                # --- 3) Run program on specific filetype if requested ---
                program_output = None
                if program_filetype and program_command:
                    # Check if this file matches the specified filetype
                    extension_keys = lookup_file_extension(file_path)
                    if program_filetype in extension_keys or program_filetype == '*':
                        program_output = run_program_on_file(file_path, program_command)
                        logging.debug(f"Program output for {file_path}: {program_output}")

                # Now handle PDF extraction, or reading text directly
                if file_path.endswith('.pdf') and 'pdf' in args.lang:
                    if args.pdf_text_mode:
                        file_content = extract_text(file_path)
                        logging.debug(f"Extracted text from PDF: {file_path}")
                    else:
                        # Just indicate this is a PDF file but don't extract text
                        file_content = "[PDF file - use --pdf_text_mode to extract text]"
                else:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                    except UnicodeDecodeError:
                        logging.debug(f"Skipping file due to encoding issues: {file_path}")
                        progress.advance(file_task)
                        continue

                # Skip test files or short/empty files
                if any(is_test_file(file_content, lang) for lang in args.lang) or not has_sufficient_content(file_content):
                    logging.debug(f'Skipping file: {file_path}')
                    logging.debug('Reason: Test file or insufficient content')
                    progress.advance(file_task)
                    continue

                # Optionally remove comments/docstrings for Python
                if 'python' in args.lang and (not args.keep_comments):
                    extension_keys = lookup_file_extension(file_path)
                    if 'python' in extension_keys:
                        try:
                            file_content = remove_comments_and_docstrings(file_content)
                        except SyntaxError:
                            logging.debug(f'Tried to remove comments/docstrings from {file_path} but failed (SyntaxError).')
                            progress.advance(file_task)
                            continue
                
                # Write the file content to the output file
                with open(output_file_path, mode, encoding='utf-8') as outfile:
                    comment_prefix = '// ' if any(lang in ['go', 'js'] for lang in args.lang) else '# '
                    outfile.write(f'{comment_prefix}File: {file_path}\n')
                    
                    # If the program ran on this file, handle the output according to --nosubstitute flag
                    if program_output:
                        outfile.write(f'{comment_prefix}Program output:\n')
                        outfile.write(program_output)
                        outfile.write('\n\n')
                        
                        # If --nosubstitute is provided, include file content as well
                        # Otherwise (default), only show program output and skip file content
                        if not args.nosubstitute:
                            # Skip writing file content since we're substituting with program output
                            outfile.write('\n\n')
                            mode = 'a'
                            progress.advance(file_task)
                            continue
                
                    # If topN is specified, show top N lines with a header comment
                    if args.topN:
                        lines = file_content.splitlines()
                        top_lines = lines[:args.topN]
                        outfile.write(f'{comment_prefix}(top {args.topN} lines)\n')
                        outfile.write('\n'.join(top_lines))
                        outfile.write('\n\n')
                        outfile.write(file_content)
                    else:
                        outfile.write(file_content)
                    
                    outfile.write('\n\n')

                mode = 'a'
                progress.advance(file_task)
    
    # Store collected extensions in args
    args.collected_extensions = collected_extensions

def create_argument_parser():
    parser = argparse.ArgumentParser(description='CodeWeave - Intelligent source code aggregation and AI workflow optimization')
    
    # Input source group
    input_group = parser.add_argument_group('Input Sources')
    input_group.add_argument('input', type=str, help='A GitHub repository URL, a local .zip file, or a local folder',
                       default="", nargs='?')
    input_group.add_argument('--repo', type=str, help='The name of the GitHub repository')
    input_group.add_argument('--zip', type=str, help='Path to the local .zip file')
    input_group.add_argument('--folder', type=str, help='Path to the local folder')
    input_group.add_argument('--branch_or_tag', type=str, help='The branch or tag of the repository to download', default="master")
    
    # File selection and filtering group
    filter_group = parser.add_argument_group('File Selection & Filtering')
    filter_group.add_argument('--lang', type=str, default=None, 
                       help='Programming language(s), format(s), or file extension(s) (comma-separated, e.g., python,javascript,.tsx,.vue). If not specified, interactive selection will be triggered.')
    filter_group.add_argument('--include', type=str, help='Comma-separated list of subfolders/patterns to focus on')
    filter_group.add_argument('--exclude', type=str, help='Comma-separated list of file patterns to exclude')
    filter_group.add_argument('--excluded_dirs', '--exclude_dir', type=str, 
                       help='Comma-separated list of directories to exclude',
                       default="docs,examples,tests,test,scripts,utils,benchmarks")
    filter_group.add_argument('--interactive-extensions', action='store_true',
                       help='Force interactive extension selection even when --lang is specified')
    
    # Content processing group
    content_group = parser.add_argument_group('Content Processing')
    content_group.add_argument('--keep-comments', action='store_true', 
                        help='Keep comments and docstrings in the source code (only applicable for Python)')
    content_group.add_argument('--ipynb_nbconvert', action='store_true', default=True, 
                        help='Convert IPython Notebook files to Python script files using nbconvert')
    content_group.add_argument('--pdf_text_mode', action='store_true', default=False,
                        help='Convert PDF files to text for analysis (requires pdf filetype in --lang)')
    content_group.add_argument('--topN', type=int, 
                        help="Show the top N lines of each file in the output as a preview")
    content_group.add_argument('--tree', action='store_true', 
                        help="Prepend a file tree (generated via the 'tree' command) to the output file (only works for local folders)")
    content_group.add_argument('--tree_flags', type=str,
                        help="Flags to pass to the 'tree' command (e.g., '-a -L 2'). If not provided, defaults will be used")
    
    # External program integration group
    program_group = parser.add_argument_group('External Program Integration')
    program_group.add_argument('--program', type=str, 
                        help="Run the specified program on each file matching the given filetype. Format: 'filetype=command'")
    program_group.add_argument('--nosubstitute', action='store_true', default=False,
                        help="Show both program output AND file content when using --program. Default behavior is to only show program output.")
    program_group.add_argument('--summarize', action='store_true', default=False,
                        help='Generate a summary of the code using Fabric')
    program_group.add_argument('--fabric_args', type=str, default='literal',
                        help='Arguments to pass to Fabric when using --summarize')
    
    # AI integration group (always add, but show availability in help)
    ai_status = "✅ Available" if AI_AVAILABLE else "❌ Install with: pip install codeweave[ai]"
    ai_group = parser.add_argument_group(f'AI Integration ({ai_status})')
    ai_group.add_argument('--prompt', type=str, 
                        help='Generate CodeWeave command from natural language description')
    ai_group.add_argument('--ai-provider', type=str, default='openrouter',
                        choices=['openrouter', 'openai', 'anthropic'],
                        help='AI provider to use for command generation (default: openrouter)')
    ai_group.add_argument('--ai-model', type=str, 
                        help='Specific AI model to use (e.g., gpt-4, claude-3-sonnet)')
    ai_group.add_argument('--no-confirm', action='store_true', default=False,
                        help='Skip confirmation prompt and run generated command directly')
    
    # Output options group
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--name_append', type=str, help='Append this string to the output file name')
    output_group.add_argument('--pbcopy', action='store_true', default=False, 
                        help='Copy the output to clipboard (macOS only)')
    
    # Debug options group
    debug_group = parser.add_argument_group('Debugging Options')
    debug_group.add_argument('--debug', action='store_true', help='Enable debug logging')
    debug_group.add_argument('--pdb', action='store_true', help="Drop into pdb on error")
    debug_group.add_argument('--pdb_fromstart', action='store_true', help="Drop into pdb from start")
    
    return parser

def determine_if_url_zip_or_folder(args):
    """Determine if the input is a URL, a .zip file, or a folder."""
    if args.input.startswith("http") and "://" in args.input:
        args.repo = args.input
    elif args.input.endswith(".zip"):
        args.zip = args.input
    else:
        args.folder = args.input

def check_for_include_override(include_list, exclude_list):
    """Check if any of the exclude_list are overridden by the include_list"""
    exclude_list = exclude_list or []
    checks = {include: (include in exclude_list) for include in include_list}
    if any(checks.values()):
        # Pop the element from the exclude list if it is included in the include list.
        for include, value in checks.items():
            if value:
                logging.debug(f"Removing {include} from the exclude list")
                exclude_list.remove(include)

def add_new_extension(languages):
    """Add new language extensions to the file_extension_dict"""
    for lang in languages:
        if lang.startswith('.'):
            # Direct extension provided
            extension_key = lang[1:]  # Remove the dot for the key
            if extension_key not in file_extension_dict:
                logging.info(f"Adding extension {lang} to the dictionary")
                file_extension_dict[extension_key] = [lang]
        elif lang not in file_extension_dict:
            # Assume it's a new language with .lang extension
            logging.info(f"Adding new extension .{lang} to the dictionary")
            file_extension_dict[lang] = [f'.{lang}']

def interactive_extension_selection(collected_extensions):
    """
    Interactively select file extensions to process.
    
    Args:
        collected_extensions: Set of file extensions found during scanning
        
    Returns:
        List of selected extensions or None if cancelled
    """
    console = Console()
    
    if not collected_extensions:
        console.print("[yellow]No file extensions found during scan.[/yellow]")
        return None
    
    # Sort and filter out binary extensions
    all_extensions = sorted(collected_extensions)
    extensions = [ext for ext in all_extensions if ext not in BINARY_EXTENSIONS]
    
    # Check if we have any non-binary extensions
    if not extensions:
        console.print("[yellow]No processable file extensions found. All discovered files are binary.[/yellow]")
        console.print(f"[dim]Binary extensions found: {', '.join(all_extensions)}[/dim]")
        return None
    
    # Display found extensions
    binary_count = len(all_extensions) - len(extensions)
    if binary_count > 0:
        console.print(Panel(
            f"[bold cyan]Found {len(all_extensions)} file extension(s), {len(extensions)} processable[/bold cyan]\n\n"
            f"[dim]Processable: {', '.join(extensions)}[/dim]\n"
            f"[dim]Binary (excluded): {binary_count} extension(s)[/dim]",
            title="[bold]File Extensions Discovered[/bold]",
            border_style="cyan"
        ))
    else:
        console.print(Panel(
            f"[bold cyan]Found {len(extensions)} processable file extension(s)[/bold cyan]\n\n"
            f"[dim]{', '.join(extensions)}[/dim]",
            title="[bold]File Extensions Discovered[/bold]",
            border_style="cyan"
        ))
    
    # Create a checklist-style interface
    console.print("\n[bold]Select extensions to process:[/bold]")
    console.print("[dim]Enter extension numbers separated by commas, ranges (e.g., 1-5), or 'all'[/dim]\n")
    
    # Display extensions with numbers
    for i, ext in enumerate(extensions, 1):
        # Try to find a language name for the extension
        lang_names = []
        for lang, exts in file_extension_dict.items():
            if ext in exts:
                lang_names.append(lang)
        
        lang_info = f" ({', '.join(lang_names)})" if lang_names else ""
        console.print(f"  {i:3d}. {ext}{lang_info}")
    
    console.print()
    
    # Get user selection
    while True:
        selection = Prompt.ask("[cyan]Your selection[/cyan]", default="all").strip().lower()
        
        if selection == "all":
            return extensions
        
        if selection == "none" or selection == "":
            return []
        
        try:
            selected_indices = set()
            
            # Parse comma-separated values and ranges
            for part in selection.split(','):
                part = part.strip()
                if '-' in part:
                    # Handle range
                    start, end = part.split('-', 1)
                    start_idx = int(start.strip())
                    end_idx = int(end.strip())
                    for idx in range(start_idx, end_idx + 1):
                        if 1 <= idx <= len(extensions):
                            selected_indices.add(idx)
                else:
                    # Handle single number
                    idx = int(part)
                    if 1 <= idx <= len(extensions):
                        selected_indices.add(idx)
            
            if selected_indices:
                selected_extensions = [extensions[i-1] for i in sorted(selected_indices)]
                
                # Confirm selection
                console.print(f"\n[green]Selected extensions:[/green] {', '.join(selected_extensions)}")
                if Confirm.ask("Proceed with these extensions?", default=True):
                    return selected_extensions
            else:
                console.print("[red]No valid selections made. Please try again.[/red]")
        
        except (ValueError, IndexError):
            console.print("[red]Invalid selection. Please enter numbers, ranges (1-5), or 'all'.[/red]")

def parse_program_arg(program_arg):
    """Parse the program argument in the format 'filetype=command'"""
    if not program_arg or '=' not in program_arg:
        logging.error("Invalid program format. Expected 'filetype=command'")
        return None, None
    
    parts = program_arg.split('=', 1)
    if len(parts) != 2:
        logging.error("Invalid program format. Expected 'filetype=command'")
        return None, None
    
    filetype, command = parts
    filetype = filetype.strip()
    command = command.strip()
    
    if not filetype or not command:
        logging.error("Both filetype and command must be specified")
        return None, None
    
    return filetype, command

def run_program_on_file(file_path, command):
    """Run the specified command on the file"""
    try:
        logging.info(f"Running command on file: {file_path}")
        full_command = f'{command} "{file_path}"'
        logging.debug(f"Executing: {full_command}")
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Command failed with exit code {result.returncode}")
            logging.error(f"Error: {result.stderr}")
            return None
        return result.stdout
    except Exception as e:
        logging.error(f"Error running command on file: {e}")
        return None

def display_configuration_header(args):
    """Display a rich configuration header with processing details"""
    console = Console()
    
    # Determine input source
    input_source = "Unknown"
    input_type = "Unknown"
    if args.repo:
        input_source = args.repo
        input_type = "GitHub Repository"
    elif args.zip:
        input_source = args.zip
        input_type = "ZIP Archive"
    elif args.folder:
        input_source = args.folder
        input_type = "Local Folder"
    
    # Create configuration table
    config_table = Table(title="Processing Configuration", show_header=True, header_style="bold magenta")
    config_table.add_column("Setting", style="cyan", width=20)
    config_table.add_column("Value", style="white")
    
    config_table.add_row("Input Type", input_type)
    config_table.add_row("Source", input_source)
    config_table.add_row("Languages", ', '.join(args.lang) if args.lang else "Interactive selection")
    config_table.add_row("Output File", getattr(args, 'output_file', 'Not set'))
    
    if args.excluded_dirs:
        config_table.add_row("Excluded Dirs", ', '.join(args.excluded_dirs))
    if args.exclude:
        config_table.add_row("Excluded Patterns", ', '.join(args.exclude))
    if args.include:
        config_table.add_row("Include Patterns", ', '.join(args.include))
    if args.program:
        config_table.add_row("Program", args.program)
    if args.tree:
        config_table.add_row("File Tree", "✓ Enabled")
    if args.topN:
        config_table.add_row("Top N Lines", str(args.topN))
    
    # Display header panel and configuration
    console.print(Panel.fit(
        "[bold blue]CodeWeave[/bold blue] - [italic]Intelligent source code aggregation[/italic]",
        border_style="blue"
    ))
    console.print(config_table)
    console.print()

def display_completion_summary(output_file_path, args):
    """Display a rich completion summary with file statistics"""
    console = Console()
    
    if os.path.exists(output_file_path):
        file_size = os.path.getsize(output_file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Create completion summary
        summary_text = (
            f"[bold green]✓ Processing Complete![/bold green]\n\n"
            f"[cyan]Output File:[/cyan] {output_file_path}\n"
            f"[cyan]File Size:[/cyan] {file_size_mb:.2f} MB ({file_size:,} bytes)\n"
            f"[cyan]Languages:[/cyan] {', '.join(args.lang) if args.lang else 'All detected'}"
        )
        
        # Add extension information if available
        if hasattr(args, 'collected_extensions') and args.collected_extensions:
            extensions = sorted(args.collected_extensions)
            extension_count = len(extensions)
            summary_text += f"\n[cyan]Unique Extensions:[/cyan] {extension_count}"
            
            # Show extensions in a formatted way
            if extension_count <= 20:
                # Show all extensions if 20 or fewer
                summary_text += f"\n[dim]{', '.join(extensions)}[/dim]"
            else:
                # Show first 20 and indicate there are more
                shown_exts = extensions[:20]
                summary_text += f"\n[dim]{', '.join(shown_exts)}, and {extension_count - 20} more...[/dim]"
        
        summary_panel = Panel(
            summary_text,
            title="[bold]Summary[/bold]",
            border_style="green"
        )
        console.print(summary_panel)
        
        # If there are many extensions, show them in a separate table
        if hasattr(args, 'collected_extensions') and len(args.collected_extensions) > 20:
            ext_table = Table(title="All File Extensions Found", show_header=True, header_style="bold cyan")
            ext_table.add_column("Extensions", style="dim")
            
            # Group extensions into rows of 10 for better display
            extensions = sorted(args.collected_extensions)
            for i in range(0, len(extensions), 10):
                ext_table.add_row(', '.join(extensions[i:i+10]))
            
            console.print(ext_table)
        
        if args.pbcopy:
            console.print("[yellow]📋 Output copied to clipboard[/yellow]")
    else:
        console.print(Panel(
            "[bold red]⚠ No source code found[/bold red]\n\n"
            "Please check your input arguments and try again.",
            title="[bold]Warning[/bold]",
            border_style="red"
        ))

def main(args=None) -> str:
    # Parse arguments.
    parser = create_argument_parser()
    args = parser.parse_args(args)
    if args.pdb_fromstart:
        import pdb; pdb.set_trace()
    # Process language argument
    if args.lang:
        args.lang = [lang.strip() for lang in args.lang.split(',')]
        add_new_extension(args.lang)
    else:
        # If no --lang specified, we'll use interactive mode
        args.lang = []  # Empty list for now, will be populated by interactive selection

    # Setup logging early.
    setup_logging(args.debug)

    logging.info("Starting the script")
    logging.debug(f"Arguments: {args}")

    # Handle AI prompt mode (only if AI functionality is available)
    if AI_AVAILABLE and (args.prompt or (args.input and is_natural_language_input(args.input))):
        console = Console()
        
        # Determine the prompt text
        prompt_text = args.prompt if args.prompt else args.input
        
        console.print(Panel(
            f"[bold yellow]AI Command Generation[/bold yellow]\n\n"
            f"[cyan]Prompt:[/cyan] {prompt_text}",
            title="CodeWeave AI",
            border_style="yellow"
        ))
        
        # Generate command using AI
        provider = getattr(args, 'ai_provider', 'openrouter')
        model = getattr(args, 'ai_model', None) 
        no_confirm = getattr(args, 'no_confirm', False)
        
        generated_command = generate_codeweave_command(prompt_text, provider, model)
        
        if not generated_command:
            console.print("[red]Failed to generate command. Please try again or use manual command.[/red]")
            return None
        
        # Ask for confirmation and execute
        if confirm_and_execute_command(generated_command, no_confirm):
            console.print("[green]Executing generated command...[/green]")
            # Parse the generated command and execute it
            import shlex
            try:
                # Remove 'codeweave' prefix and parse arguments
                cmd_args = shlex.split(generated_command)
                if cmd_args[0] == 'codeweave':
                    cmd_args = cmd_args[1:]
                
                # Recursively call main with generated arguments
                return main(cmd_args)
            except Exception as e:
                console.print(f"[red]Error executing generated command: {e}[/red]")
                return None
        else:
            console.print("[yellow]Command execution cancelled.[/yellow]")
            return None
    elif args.prompt and not AI_AVAILABLE:
        console = Console()
        console.print(Panel(
            "[red]AI functionality not available![/red]\n\n"
            "Install AI dependencies:\n"
            "• [cyan]pip install codeweave[ai][/cyan] (recommended)\n"
            "• [cyan]pip install codeweave[ai-basic][/cyan] (basic)",
            title="Missing AI Dependencies",
            border_style="red"
        ))
        return None

    try:
        # Process excluded directories
        if args.excluded_dirs:
            args.excluded_dirs = [subfolder.strip() for subfolder in args.excluded_dirs.split(',')]
        else:
            args.excluded_dirs = []
            
        # Process include patterns
        if args.include:
            args.include = [subfolder.strip() for subfolder in args.include.split(',')]
            check_for_include_override(args.include, args.exclude)
            check_for_include_override(args.include, args.excluded_dirs)
        else:
            args.include = []
            
        # Process exclude patterns and automatically add excluded_dirs to ensure consistent exclusion
        if args.exclude:
            args.exclude = [pattern.strip() for pattern in args.exclude.split(',')]
        else:
            args.exclude = []
            
        # Automatically add excluded_dirs patterns to exclude list to avoid duplication
        # but avoid adding duplicates
        for excluded_dir in args.excluded_dirs:
            if excluded_dir not in args.exclude:
                args.exclude.append(excluded_dir)

        if args.input:
            # Determine if the input is a URL, a .zip file, or a folder, and set the corresponding attribute.
            determine_if_url_zip_or_folder(args)
        if args.repo:
            lang_suffix = ','.join(args.lang) if args.lang else 'selected'
            args.output_file = f"{args.repo.split('/')[-1]}_{lang_suffix}.txt"
        elif args.zip:
            lang_suffix = ','.join(args.lang) if args.lang else 'selected'
            args.output_file = f"{os.path.splitext(os.path.basename(args.zip))[0]}_{lang_suffix}.txt"
        elif args.folder:
            args.folder = os.path.abspath(os.path.expanduser(args.folder))
            gitfolder = extract_git_folder(args.folder)
            folder = args.folder if gitfolder is None else gitfolder
            check_for_include_override(args.folder.split('/'), args.exclude)
            check_for_include_override(args.folder.split('/'), args.excluded_dirs)
            if not gitfolder:
                logging.warning("No git folder found in the path")
            lang_suffix = ','.join(args.lang) if args.lang else 'selected'
            args.output_file = f"{folder}_{lang_suffix}.txt"
        else:
            raise ValueError("Input not recognized as a URL, a .zip file, or a folder")

        if args.name_append:
            args.output_file = f"{os.path.splitext(args.output_file)[0]}_{args.name_append}{os.path.splitext(args.output_file)[1]}"

        # Default: place the output file inside an 'outputs' folder.
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, args.output_file)
        
        # Attach the output_file_path to the args namespace for easy access
        args.output_file_path = output_file_path

        # Display rich configuration header
        display_configuration_header(args)

        if os.path.exists(output_file_path):
            logging.info(f"Output file {output_file_path} already exists. Removing it.")
            os.remove(output_file_path)

        # Initialize collected_extensions to ensure it's always available
        args.collected_extensions = set()

        # Handle interactive extension selection if requested or if no language specified
        if args.interactive_extensions or not args.lang:
            console = Console()
            console.print("[bold yellow]Interactive extension selection mode[/bold yellow]")
            console.print("[dim]Scanning for file extensions...[/dim]\n")
            
            # First pass: scan for extensions only
            if args.repo:
                console.print("[bold green]Downloading repository for scanning...[/bold green]")
                # For repos, we need to download first, then scan
                download_repo(args, output_file_path, scan_only=True)
                # Extensions are collected in args.collected_extensions during download
            elif args.zip:
                console.print("[bold green]Scanning zip file...[/bold green]")
                # Create a temporary process to scan extensions
                with zipfile.ZipFile(args.zip, 'r') as zip_file:
                    temp_extensions = set()
                    process_zip_object(zip_file, args, output_file_path, temp_extensions, scan_only=True)
                    args.collected_extensions = temp_extensions
            elif args.folder:
                console.print("[bold green]Scanning folder...[/bold green]")
                process_folder(args, output_file_path, scan_only=True)
            
            # Select extensions interactively
            selected_extensions = interactive_extension_selection(args.collected_extensions)
            
            if not selected_extensions:
                console.print("[yellow]No extensions selected. Exiting.[/yellow]")
                return None
            
            # Update args.lang with selected extensions
            args.lang = selected_extensions
            add_new_extension(args.lang)
            
            # Clear the output file for the second pass
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
            
            # Reset collected extensions for the actual processing
            args.collected_extensions = set()
            
            console.print(f"\n[green]Processing files with extensions:[/green] {', '.join(selected_extensions)}\n")
        
        # Process files (either normally or second pass for interactive mode)
        if args.repo:
            console = Console()
            if not args.interactive_extensions:
                console.print("[bold green]Downloading repository...[/bold green]")
            download_repo(args, output_file_path)
        elif args.zip:
            console = Console()
            console.print("[bold green]Processing zip file...[/bold green]")
            process_zip(args)
        elif args.folder:
            console = Console()
            console.print("[bold green]Processing folder...[/bold green]")
            process_folder(args, output_file_path)
        else:
            parser.print_help()
            sys.exit(1)

        # If summarize is specified, pipe the output to Fabric
        if args.summarize and os.path.exists(output_file_path):
            console = Console()
            console.print("[bold yellow]Generating code summary using Fabric...[/bold yellow]")
            summary_file_path = f"{os.path.splitext(output_file_path)[0]}_summary.txt"
            fabric_command = f'cat "{output_file_path}" | fabric --{args.fabric_args} > "{summary_file_path}"'
            
            try:
                logging.debug(f"Running command: {fabric_command}")
                os.system(fabric_command)
                console.print(f"[green]Code summary saved to {summary_file_path}[/green]")
            except Exception as e:
                console.print(f"[red]Error generating summary with Fabric: {e}[/red]")
                console.print("[red]Make sure Fabric is installed and accessible in your PATH[/red]")

        if args.pbcopy and os.path.exists(output_file_path):
            os.system(f'cat "{output_file_path}" | pbcopy')
        
        # Display completion summary
        display_completion_summary(output_file_path, args)

        return output_file_path

    except argparse.ArgumentError as e:
        logging.error(str(e))
        parser.print_help()
        if args.pdb:
            import pdb
            pdb.post_mortem()
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
