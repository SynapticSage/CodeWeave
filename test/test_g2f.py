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
