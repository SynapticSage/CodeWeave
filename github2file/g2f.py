import os
import sys
import requests
import zipfile
import io
import logging
import argparse
from tqdm.auto import tqdm
from pdfminer.high_level import extract_text

from github2file.utils.path import should_exclude_file, inclusion_violate, extract_git_folder, is_test_file, is_file_type, is_likely_useful_file, lookup_file_extension
from github2file.utils.file import has_sufficient_content, remove_comments_and_docstrings
from github2file.utils.jupyter import convert_ipynb_to_py

def setup_logging(debug_flag):
    """Setup logging configuration."""
    log_level = logging.DEBUG if debug_flag else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def download_repo(args):
    """Download and process files from a GitHub repository."""
    download_url = f"{args.repo_url}/archive/refs/heads/{args.branch_or_tag}.zip"

    logging.info(f"Download URL: {download_url}")
    response = requests.get(download_url)

    if response.status_code == 200:
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        process_zip_file_object(zip_file, args)
    else:
        logging.error(f"Failed to download the repository. Status code: {response.status_code}")
        sys.exit(1)

def process_zip_file(args:argparse.Namespace):
    """Process files from a local .zip file."""
    with zipfile.ZipFile(args.zip_file, 'r') as zip_file:
        process_zip_file_object(zip_file, args)

def process_zip_file_object(zip_file, args:argparse.Namespace):
    """Process files from a local .zip file."""
    with open(args.output_file, "w", encoding="utf-8") as outfile:
        for file_path in tqdm(zip_file.namelist(), 
                              desc="Processing files", 
                              unit="file", 
                              total=len(zip_file.namelist())):
            if (file_path.endswith("/")
                or not is_file_type(file_path, args.lang)
                or not any(is_likely_useful_file(file_path, lang, args) for lang in args.lang)
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

            file_content = zip_file.read(file_path).decode("utf-8")
            if file_path.endswith('.pdf') and 'pdf' in args.format:
                file_content = extract_text(io.BytesIO(zip_file.read(file_path)))
            elif file_path.endswith('.ipynb') and args.ipynb_nbconvert:
                file_content = convert_ipynb_to_py(file_content)

            if any(is_test_file(file_content, lang) for lang in args.lang) or not has_sufficient_content(file_content):
                continue
            if "python" in args.lang and not args.keep_comments:
                try:
                    file_content = remove_comments_and_docstrings(file_content)
                except SyntaxError:
                    continue

            comment_prefix = "// " if any(lang in ["go", "js"] for lang in args.lang) else "# "
            outfile.write(f"{comment_prefix}File: {file_path}\n")
            outfile.write(file_content)
            outfile.write("\n\n")

def process_folder(args:argparse.Namespace):
    """Process files from a local folder."""
    from functools import reduce
    from operator import ior
    for root, _, files in tqdm(os.walk(args.folder),
                               desc="Processing folders",
                               unit="folder",
                               leave=False):
        logging.debug(f"In folder: {root}")
        logging.debug(f"File list:\n{files}")
        if files == ['sampleWrapperScript.m', 'exportTrodesRecsAsOne.m']:
            import pdb; pdb.set_trace()
        for file in files:
            file_path = os.path.join(root, file)
            # Annotated logic for skipping files
            we_should_examine = {
                "bad filetype": not is_file_type(file, args.lang),
                "not useful":   not any(is_likely_useful_file(file, lang, args) for lang in args.lang),
                "should exclude": should_exclude_file(file, args),
                "inclusion violate": inclusion_violate(file, args)
            }
            if reduce(ior, we_should_examine.values()):
                logging.debug(f"Skipping file: {file_path}")
                logging.debug(f"Reasons: {we_should_examine}")
                continue
            if any(excluded_dir in root for excluded_dir in args.excluded_dirs):
                logging.debug(f"Excluded directory, skipping {file_path}")
                continue

            if file_path.endswith('.pdf') and 'pdf' in args.format:
                file_content = extract_text(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            if any(is_test_file(file_content, lang) for lang in args.lang) or not has_sufficient_content(file_content):
                logging.debug(f"Skipping file: {file_path}")
                logging.debug(f"Reason: Test file or insufficient content")
                continue
            if "python" in args.lang and not args.keep_comments:
                extension_keys = lookup_file_extension(file_path)
                if "python" in extension_keys:
                    try:
                        file_content = remove_comments_and_docstrings(file_content)
                    except SyntaxError:
                        logging.debug(f"Tried to remove comments and docstrings from {file_path} but failed")
                        logging.debug(f"Reason: Syntax error")

            with open(args.output_file, 'a', encoding='utf-8') as outfile:
                comment_prefix = "// " if any(lang in ["go", "js"] for lang in args.lang) else "# "
                outfile.write(f"{comment_prefix}File: {file_path}\n")
                outfile.write(file_content)
                outfile.write("\n\n")

def create_argument_parser():
    parser = argparse.ArgumentParser(description='Download and process files from a GitHub repository.')
    parser.add_argument('--zip_file', type=str, help='Path to the local .zip file')
    parser.add_argument('--folder', type=str, help='Path to the local folder')
    parser.add_argument('--lang', type=str, default='python', help='The programming language(s) of the repository (comma-separated)')
    parser.add_argument('--keep-comments', action='store_true', help='Keep comments and docstrings in the source code (only applicable for Python)')
    parser.add_argument('--format', type=str, default='python', help='The format of the files to process (comma-separated, e.g., python,pdf)')
    parser.add_argument('--branch_or_tag', type=str, help='The branch or tag of the repository to download', default="master")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--include', type=str, help='Comma-separated list of subfolders/patterns to focus on')
    parser.add_argument('--exclude', type=str, help='Comma-separated list of file patterns to exclude')
    parser.add_argument('--excluded_dirs', type=str, help='Comma-separated list of directories to exclude',
                        default="docs,examples,tests,test,scripts,utils,benchmarks")
    parser.add_argument('repo_url', type=str, help='The URL of the GitHub repository',
                        default="", nargs='?')
    parser.add_argument('--name_append', type=str, help='Append this string to the output file name')
    parser.add_argument('--ipynb_nbconvert', action='store_true', default=True, help='Convert IPython Notebook files to Python script files using nbconvert')
    parser.add_argument('--pbcopy', action='store_true', default=False, help='pbcopy the output to clipboard')
    return parser

def check_for_include_override(include_list, exclude_list):
    """Check if any of the exclude_list are overridden by the include_list"""
    checks = {include:(include in exclude_list) for include in include_list}
    if any(checks.values()):
        # pop the excluded_dirs if it is included in the include list
        for include, value in checks.items():
            if value:
                logging.debug(f"Removing {include} from the exclude list")
                exclude_list.remove(include)

def main(args=None):
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args(args)
    args.lang = [lang.strip() for lang in args.lang.split(',')]
    args.format = [fmt.strip() for fmt in args.format.split(',')]

    # Setup logging early
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

        if args.repo_url:
            args.output_file = f"{args.repo_url.split('/')[-1]}_{','.join(args.lang)}.txt"
        elif args.zip_file:
            args.output_file = f"{os.path.splitext(os.path.basename(args.zip_file))[0]}_{','.join(args.lang)}.txt"
        elif args.folder:
            args.folder = os.path.abspath(os.path.expanduser(args.folder))
            gitfolder = extract_git_folder(args.folder)
            check_for_include_override(args.folder.split('/'), args.exclude)
            check_for_include_override(args.folder.split('/'), args.excluded_dirs)
            if not gitfolder:
                logging.warning("No git folder found in the path")
            if args.name_append:
                args.output_file = f"{gitfolder}_{args.name_append}_{','.join(args.lang)}.txt"
            else:
                args.output_file = f"{gitfolder}_{','.join(args.lang)}.txt"

        if os.path.exists(args.output_file):
            logging.info(f"Output file {args.output_file} already exists. Removing it.")
            os.remove(args.output_file)

        if args.repo_url:
            logging.info("Downloading repository")
            download_repo(args)
        elif args.zip_file:
            logging.info("Processing zip file")
            process_zip_file(args)
        elif args.folder:
            logging.info("Processing folder")
            process_folder(args)
        else:
            parser.print_help()
            sys.exit(1)

        if os.path.exists(args.output_file):
            logging.info(f"Combined {', '.join(args.lang).capitalize()} source code saved to {args.output_file}")
        else:
            logging.info("No source code found to save -- check the input arguments")

        if args.pbcopy:
            os.system(f'cat {args.output_file} | pbcopy')

    except argparse.ArgumentError as e:
        logging.error(str(e))
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
