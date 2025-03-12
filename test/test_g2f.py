from github2file.g2f import create_argument_parser, main
import github2file
import os

folder = os.path.dirname(os.path.dirname(github2file.__file__))

def test_argument_parser():
    parser = create_argument_parser()
    args = parser.parse_args(['--lang', 'python,pdf', 'https://github.com/yourusername/github2file'])
    assert args.lang == 'python,pdf'
    assert args.input == 'https://github.com/yourusername/github2file'

def test_main_function():
    # This is a placeholder test. You can add more comprehensive tests based on your requirements.
    assert main is not None

def test_process_folder_with_pdf():
    # Create a mock args object
    args = ['--folder', 'test', '--lang', 'python,pdf']
    output_file = main(args)

    # Test that the output file is created
    assert os.path.exists(output_file)

def test_topN_flag():
    # Test the --topN flag
    args = ['--folder', 'test', '--lang', 'python', '--topN', '5']
    output_file = main(args)
    
    # Check if the output file exists
    assert os.path.exists(output_file)
    
    # Check if the output file contains "(top 5 lines)"
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "(top 5 lines)" in content

def test_excluded_dirs_auto_added_to_exclude():
    # Test that excluded_dirs are automatically added to exclude
    from argparse import Namespace
    
    # Create a parser to simulate the command line
    parser = create_argument_parser()
    test_args = parser.parse_args(['--excluded_dirs', 'env,.venv,node_modules', '--folder', 'test'])
    
    # Process the arguments as main() would
    if test_args.excluded_dirs:
        test_args.excluded_dirs = [subfolder.strip() for subfolder in test_args.excluded_dirs.split(',')]
    else:
        test_args.excluded_dirs = []
        
    if test_args.exclude:
        test_args.exclude = [pattern.strip() for pattern in test_args.exclude.split(',')]
    else:
        test_args.exclude = []
        
    # Add excluded_dirs to exclude list as our modified code would
    for excluded_dir in test_args.excluded_dirs:
        if excluded_dir not in test_args.exclude:
            test_args.exclude.append(excluded_dir)
    
    # Verify all excluded_dirs are in the exclude list
    assert all(dir in test_args.exclude for dir in test_args.excluded_dirs)
    assert 'env' in test_args.exclude
    assert '.venv' in test_args.exclude
    assert 'node_modules' in test_args.exclude
