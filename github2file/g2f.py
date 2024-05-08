import os
import sys
import requests
import zipfile
import io
import logging
import argparse

from github2file.utils.path import should_exclude_file, inclusion_violate, extract_git_folder, is_test_file, is_file_type, is_likely_useful_file
from github2file.utils.file import has_sufficient_content, remove_comments_and_docstrings


def download_repo(args):
    """Download and process files from a GitHub repository."""
    download_url = f"{args.repo_url}/archive/refs/heads/{args.branch_or_tag}.zip"

    print(download_url)
    response = requests.get(download_url)

    if response.status_code == 200:
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        process_zip_file_object(zip_file, args)
    else:
        print(f"Failed to download the repository. Status code: {response.status_code}")
        sys.exit(1)

def process_zip_file(args):
    """Process files from a local .zip file."""
    with zipfile.ZipFile(args.zip_file, 'r') as zip_file:
        process_zip_file_object(zip_file, args)

def process_zip_file_object(zip_file, args):
    """Process files from a local .zip file."""
    file_extensions = [f".{lang}" for lang in args.lang]
    with open(args.output_file, "w", encoding="utf-8") as outfile:
        for file_path in zip_file.namelist():
            if (file_path.endswith("/")
                or not is_file_type(file_path, args.lang)
                or not any(is_likely_useful_file(file_path, lang, args) for lang in args.lang)
                or should_exclude_file(file_path, args.exclude)):
                continue

            if args.include:
                confirm_include = any(include in file_path for include in args.include)
                if not confirm:
                    logging.debug(f"Skipping file: {file_path}")
                    continue
            if not confirm_include:
                pass

            file_content = zip_file.read(file_path).decode("utf-8")

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


def process_folder(args):
    """Process files from a local folder."""
    for root, _, files in os.walk(args.folder):
        for file in files:
            file_path = os.path.join(root, file)
            if (not is_file_type(file_path, args.lang)
                or not any(is_likely_useful_file(file_path, lang, args) for lang in args.lang)
                or should_exclude_file(file_path, args)):
                continue

            if inclusion_violate(file_path, args):
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            if any(is_test_file(file_content, lang) for lang in args.lang) or not has_sufficient_content(file_content):
                continue
            if "python" in args.lang and not args.keep_comments:
                try:
                    file_content = remove_comments_and_docstrings(file_content)
                except SyntaxError:
                    continue

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
    parser.add_argument('--branch_or_tag', type=str, help='The branch or tag of the repository to download', default="master")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--include', type=str, help='Comma-separated list of subfolders/patterns to focus on')
    parser.add_argument('--exclude', type=str, help='Comma-separated list of file patterns to exclude')
    parser.add_argument('--excluded_dirs', type=str, help='Comma-separated list of directories to exclude',
                        default="docs,examples,tests,test,scripts,utils,benchmarks")
    parser.add_argument('repo_url', type=str, help='The URL of the GitHub repository',
                        default="", nargs='?')
    parser.add_argument('--name_append', type=str, help='Append this string to the output file name')
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
    parser = create_argument_parser()
    args = parser.parse_args(args)
    args.lang = [lang.strip() for lang in args.lang.split(',')]
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

    if args.debug:
        print("Debug logging enabled")
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Debug logging enabled")
        logging.debug(f"Arguments: {args}")
        input("Press Enter to continue...")
    else:
        # Enable info logging
        logging.basicConfig(level=logging.INFO)

    try:
        if args.repo_url:
            args.output_file = f"{args.repo_url.split('/')[-1]}_{','.join(args.lang)}.txt"
            download_repo(args)
        elif args.zip_file:
            args.output_file = f"{os.path.splitext(os.path.basename(args.zip_file))[0]}_{','.join(args.lang)}.txt"
            process_zip_file(args)
        elif args.folder:
            # Find the git repo name from the folder path
            args.folder = os.path.abspath(
                os.path.expanduser(args.folder))
            gitfolder = extract_git_folder(args.folder)
            check_for_include_override(args.folder.split('/'), args.exclude)
            check_for_include_override(args.folder.split('/'), args.excluded_dirs)
            if not gitfolder:
                print("No git folder found in the path")
                sys.exit(1)
            if args.name_append:
                args.output_file = f"{gitfolder}_{args.name_append}_{','.join(args.lang)}.txt"
            else:
                args.output_file = f"{gitfolder}_{','.join(args.lang)}.txt"
            process_folder(args)
        else:
            parser.print_help()
            sys.exit(1)

        if os.path.exists(args.output_file):
            print(f"Combined {', '.join(args.lang).capitalize()} source code saved to {args.output_file}")
        else:
            print("No source code found to save -- check the input arguments")

    except argparse.ArgumentError as e:
        print(str(e))
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()


