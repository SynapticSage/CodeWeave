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

from github2file.utils.path import (
    should_exclude_file,
    inclusion_violate,
    extract_git_folder,
    is_test_file,
    is_file_type,
    is_likely_useful_file,
    lookup_file_extension,
    file_extension_dict,
)
from github2file.utils.file import has_sufficient_content, remove_comments_and_docstrings
from github2file.utils.jupyter import convert_ipynb_to_py

def setup_logging(debug_flag):
    """Setup logging configuration."""
    log_level = logging.DEBUG if debug_flag else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def download_repo(args, output_file_path):
    """Download and process files from a GitHub repository."""
    download_url = f"{args.repo}/archive/refs/heads/{args.branch_or_tag}.zip"

    logging.info(f"Download URL: {download_url}")
    response = requests.get(download_url)

    if response.status_code == 200:
        zip_obj = zipfile.ZipFile(io.BytesIO(response.content))
        process_zip_object(zip_obj, args, output_file_path)
    else:
        logging.error(f"Failed to download the repository. Status code: {response.status_code}")
        sys.exit(1)

def process_zip(args: argparse.Namespace):
    """Process files from a local .zip file."""
    with zipfile.ZipFile(args.zip, 'r') as zip_obj:
        process_zip_object(zip_obj, args)

def process_zip_object(zip_obj, args: argparse.Namespace, output_file_path):
    """Process files from a local .zip file."""
    with open(output_file_path, "w", encoding="utf-8") as outfile:
        for file_path in tqdm(zip_obj.namelist(),
                              desc="Processing files",
                              unit="file",
                              total=len(zip_obj.namelist())):
            if (file_path.endswith("/")
                or not is_file_type(file_path, args.lang)
                or not is_likely_useful_file(file_path, args.lang, args)
                or should_exclude_file(file_path, args)):
                continue

            if args.include:
                confirm_include = any(include in file_path for include in args.include)
                if not confirm_include:
                    logging.debug(f"Skipping file: {file_path}")
                    continue
            else:
                # Default to include
                confirm_include = True
            if not confirm_include:
                continue

            logging.debug(f"Processing file: {file_path}")
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
                file_content = zip_obj.read(file_path).decode("utf-8")

            if any(is_test_file(file_content, lang) for lang in args.lang) or not has_sufficient_content(file_content):
                continue
            if "python" in args.lang and not args.keep_comments:
                try:
                    file_content = remove_comments_and_docstrings(file_content)
                except SyntaxError:
                    continue

            comment_prefix = "// " if any(lang in ["go", "js"] for lang in args.lang) else "# "
            outfile.write(f"{comment_prefix}File: {file_path}\n")
            
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

def process_folder(args: argparse.Namespace, output_file_path):
    """
    Processes a local folder: 
    1) Optionally prepends a file tree (via the 'tree' command).
    2) Gathers and writes out source files that match the user's language and 
       filtering criteria.
    """

    # --- 1) Generate a file tree using the 'tree' command, applying exclusions ---
    if args.tree:
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

    for root, _, files in tqdm(os.walk(args.folder), desc='Processing folders', unit='folder', leave=False):
        logging.debug(f'In folder: {root}')
        logging.debug(f'File list:\n{files}')

        for file in files:
            file_path = os.path.join(root, file)

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
                continue

            # Also skip any directories in --excluded_dirs
            if any(excluded_dir in root for excluded_dir in args.excluded_dirs):
                logging.debug(f'Excluded directory, skipping {file_path}')
                continue

            # Now handle PDF extraction, or reading text directly
            if file_path.endswith('.pdf') and 'pdf' in args.lang:
                if args.pdf_text_mode:
                    file_content = extract_text(file_path)
                    logging.debug(f"Extracted text from PDF: {file_path}")
                else:
                    # Just indicate this is a PDF file but don't extract text
                    file_content = "[PDF file - use --pdf_text_mode to extract text]"
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

            # Skip test files or short/empty files
            if any(is_test_file(file_content, lang) for lang in args.lang) or not has_sufficient_content(file_content):
                logging.debug(f'Skipping file: {file_path}')
                logging.debug('Reason: Test file or insufficient content')
                continue

            # Optionally remove comments/docstrings for Python
            if 'python' in args.lang and (not args.keep_comments):
                extension_keys = lookup_file_extension(file_path)
                if 'python' in extension_keys:
                    try:
                        file_content = remove_comments_and_docstrings(file_content)
                    except SyntaxError:
                        logging.debug(f'Tried to remove comments/docstrings from {file_path} but failed (SyntaxError).')
            
            # Write the file content to the output file
            with open(output_file_path, mode, encoding='utf-8') as outfile:
                comment_prefix = '// ' if any(lang in ['go', 'js'] for lang in args.lang) else '# '
                outfile.write(f'{comment_prefix}File: {file_path}\n')
                
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

def create_argument_parser():
    parser = argparse.ArgumentParser(description='Download and process files from a GitHub repository.')
    parser.add_argument('--zip', type=str, help='Path to the local .zip file')
    parser.add_argument('--folder', type=str, help='Path to the local folder')
    parser.add_argument('--lang', type=str, default='python', 
                        help='The programming language(s) and format(s) of the repository (comma-separated, e.g., python,pdf). If not provided, the script will attempt to determine the language based on the file extension.')
    parser.add_argument('--keep-comments', action='store_true', help='Keep comments and docstrings in the source code (only applicable for Python)')
    parser.add_argument('--branch_or_tag', type=str, help='The branch or tag of the repository to download', default="master")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--include', type=str, help='Comma-separated list of subfolders/patterns to focus on')
    parser.add_argument('--exclude', type=str, help='Comma-separated list of file patterns to exclude')
    parser.add_argument('--excluded_dirs', '--exclude_dir', type=str, 
                        help='Comma-separated list of directories to exclude',
                        default="docs,examples,tests,test,scripts,utils,benchmarks")
    parser.add_argument('--name_append', type=str, help='Append this string to the output file name')
    parser.add_argument('--ipynb_nbconvert', action='store_true', default=True, 
                        help='Convert IPython Notebook files to Python script files using nbconvert')
    parser.add_argument('--pdf_text_mode', action='store_true', default=False,
                        help='Convert PDF files to text for analysis (requires pdf filetype in --lang)')
    parser.add_argument('--summarize', action='store_true', default=False,
                        help='Generate a summary of the code using Fabric')
    parser.add_argument('--fabric_args', type=str, default='literal',
                        help='Arguments to pass to Fabric when using --summarize')
    parser.add_argument('--pbcopy', action='store_true', default=False, 
                        help='pbcopy the output to clipboard')
    parser.add_argument('--repo', type=str, help='The name of the GitHub repository')
    parser.add_argument('--pdb', action='store_true', help="Drop into pdb on error")
    parser.add_argument('--pdb_fromstart', action='store_true', help="Drop into pdb from start")
    # New arguments for file tree prepending.
    parser.add_argument('--tree', action='store_true', 
                        help="Prepend a file tree (generated via the 'tree' command) to the output file (only works for local folders)")
    parser.add_argument('--tree_flags', type=str,
                        help="Flags to pass to the 'tree' command (e.g., '-a -L 2'). If not provided, defaults will be used")
    parser.add_argument('--topN', type=int, 
                        help="Show the top N lines of each file in the output as a preview")
    parser.add_argument('input', type=str, help='A GitHub repository URL, a local .zip file, or a local folder',
                        default="", nargs='?')
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
        if lang not in file_extension_dict:
            logging.info("Adding new extension to the dictionary")
            file_extension_dict[lang] = [f'.{lang}']

def main(args=None) -> str:
    # Parse arguments.
    parser = create_argument_parser()
    args = parser.parse_args(args)
    if args.pdb_fromstart:
        import pdb; pdb.set_trace()
    if args.lang:
        args.lang = [lang.strip() for lang in args.lang.split(',')]
    else:
        args.lang = set()  # Indicates special behavior where each encountered file extension is added to the set.

    add_new_extension(args.lang)

    # Setup logging early.
    setup_logging(args.debug)

    logging.info("Starting the script")
    logging.debug(f"Arguments: {args}")

    try:
        if args.excluded_dirs:
            args.excluded_dirs = [subfolder.strip() for subfolder in args.excluded_dirs.split(',')]
        if args.include:
            args.include = [subfolder.strip() for subfolder in args.include.split(',')]
            check_for_include_override(args.include, args.exclude)
            check_for_include_override(args.include, args.excluded_dirs)
        else:
            args.include = []
        if args.exclude:
            args.exclude = [pattern.strip() for pattern in args.exclude.split(',')]
        else:
            args.exclude = []

        if args.input:
            # Determine if the input is a URL, a .zip file, or a folder, and set the corresponding attribute.
            determine_if_url_zip_or_folder(args)
        if args.repo:
            args.output_file = f"{args.repo.split('/')[-1]}_{','.join(args.lang)}.txt"
        elif args.zip:
            args.output_file = f"{os.path.splitext(os.path.basename(args.zip))[0]}_{','.join(args.lang)}.txt"
        elif args.folder:
            args.folder = os.path.abspath(os.path.expanduser(args.folder))
            gitfolder = extract_git_folder(args.folder)
            folder = args.folder if gitfolder is None else gitfolder
            check_for_include_override(args.folder.split('/'), args.exclude)
            check_for_include_override(args.folder.split('/'), args.excluded_dirs)
            if not gitfolder:
                logging.warning("No git folder found in the path")
            args.output_file = f"{folder}_{','.join(args.lang)}.txt"
        else:
            raise ValueError("Input not recognized as a URL, a .zip file, or a folder")

        if args.name_append:
            args.output_file = f"{os.path.splitext(args.output_file)[0]}_{args.name_append}{os.path.splitext(args.output_file)[1]}"

        # Default: place the output file inside an 'outputs' folder.
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, args.output_file)

        if os.path.exists(output_file_path):
            logging.info(f"Output file {output_file_path} already exists. Removing it.")
            os.remove(output_file_path)

        if args.repo:
            logging.info("Downloading repository")
            download_repo(args, output_file_path)
        elif args.zip:
            logging.info("Processing zip file")
            process_zip(args)
        elif args.folder:
            logging.info("Processing folder")
            process_folder(args, output_file_path)
        else:
            parser.print_help()
            sys.exit(1)

        if os.path.exists(output_file_path):
            logging.info(f"Combined {', '.join(args.lang).capitalize()} source code saved to {output_file_path}")
            
            # If summarize is specified, pipe the output to Fabric
            if args.summarize:
                logging.info("Generating code summary using Fabric...")
                summary_file_path = f"{os.path.splitext(output_file_path)[0]}_summary.txt"
                fabric_command = f'cat "{output_file_path}" | fabric --{args.fabric_args} > "{summary_file_path}"'
                
                try:
                    logging.debug(f"Running command: {fabric_command}")
                    os.system(fabric_command)
                    logging.info(f"Code summary saved to {summary_file_path}")
                except Exception as e:
                    logging.error(f"Error generating summary with Fabric: {e}")
                    logging.error("Make sure Fabric is installed and accessible in your PATH")
        else:
            logging.info("No source code found to save -- check the input arguments")

        if args.pbcopy:
            logging.info(f"Copying the output to the clipboard {output_file_path} at {os.getcwd()}")
            os.system(f'cat "{output_file_path}" | pbcopy')

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
