import os
import sys
import pytest
import logging
from unittest.mock import patch, MagicMock
from io import StringIO

from codeweave.main import main, create_argument_parser


def test_summarize_flag_in_argument_parser():
    """Test that the --summarize flag is properly added to the argument parser."""
    parser = create_argument_parser()
    args = parser.parse_args(['--summarize', '--folder', 'test'])
    assert args.summarize is True
    assert args.fabric_args == 'literal'  # default value


def test_summarize_with_custom_fabric_args():
    """Test that custom fabric args are properly parsed."""
    parser = create_argument_parser()
    args = parser.parse_args(['--summarize', '--fabric_args', 'analyze', '--folder', 'test'])
    assert args.summarize is True
    assert args.fabric_args == 'analyze'


@patch('os.system')
@patch('os.path.exists')
def test_summarize_command_construction(mock_exists, mock_system):
    """Test that the fabric command is constructed correctly."""
    # Mock that the output file exists
    mock_exists.return_value = True
    
    # Set up to capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Run with summarize flag
    args = ['--folder', 'test', '--lang', 'python', '--summarize']
    
    try:
        # Redirect stdout to avoid actual output during test
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        
        output_file = main(args)
        summary_file = f"{os.path.splitext(output_file)[0]}_summary.txt"
        
        # Check that the os.system call was made with the right command
        expected_cmd = f'cat "{output_file}" | fabric --literal > "{summary_file}"'
        mock_system.assert_called_with(expected_cmd)
        
        # The fabric feature uses console.print, not logging
        # So we just verify the os.system call was made correctly
        # Log output will contain debug info but not the user messages
        
    finally:
        # Restore stdout
        sys.stdout = original_stdout
        # Remove the log handler
        logging.getLogger().removeHandler(handler)


@patch('os.system')
@patch('os.path.exists')
def test_summarize_with_custom_fabric_args_command(mock_exists, mock_system):
    """Test that custom fabric args are properly used in the command."""
    # Mock that the output file exists
    mock_exists.return_value = True
    
    # Run with summarize flag and custom fabric args
    args = ['--folder', 'test', '--lang', 'python', '--summarize', '--fabric_args', 'analyze create_summary']
    
    # Redirect stdout to avoid actual output during test
    original_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        output_file = main(args)
        summary_file = f"{os.path.splitext(output_file)[0]}_summary.txt"
        
        # Check that the os.system call was made with the right command
        expected_cmd = f'cat "{output_file}" | fabric --analyze create_summary > "{summary_file}"'
        mock_system.assert_called_with(expected_cmd)
    finally:
        # Restore stdout
        sys.stdout = original_stdout


@patch('os.system')
@patch('os.path.exists')
def test_fabric_not_found_error_handling(mock_exists, mock_system):
    """Test error handling when fabric command fails."""
    # Mock that the output file exists
    mock_exists.return_value = True
    
    # Mock os.system to raise an exception
    mock_system.side_effect = Exception("Command 'fabric' not found")
    
    # Set up to capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.ERROR)
    
    # Run with summarize flag
    args = ['--folder', 'test', '--lang', 'python', '--summarize']
    
    try:
        # Redirect stdout to avoid actual output during test
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        
        main(args)
        
        # The error handling uses console.print, not logging
        # Verify that os.system was called (which triggered the exception)
        mock_system.assert_called_once()
        
    finally:
        # Restore stdout
        sys.stdout = original_stdout
        # Remove the log handler
        logging.getLogger().removeHandler(handler)