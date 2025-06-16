import pytest
from unittest.mock import patch, MagicMock
from codeweave.utils.ai import is_natural_language_input, get_ai_config
from codeweave.main import create_argument_parser


def test_is_natural_language_input():
    """Test natural language detection logic."""
    
    # Should detect as natural language
    natural_inputs = [
        "extract all python files from current directory",
        "process github repo for javascript",
        "get all code excluding tests",
        "download repo and analyze markdown files",
        "show me python files with comments removed",
        "what files are in this project",
        "how can I get typescript code",
    ]
    
    for input_text in natural_inputs:
        assert is_natural_language_input(input_text), f"Should detect '{input_text}' as natural language"
    
    # Should detect as file paths
    path_inputs = [
        ".",
        "./src",
        "/path/to/folder",
        "~/Documents/project",
        "https://github.com/user/repo",
        "project.zip",
        "C:\\Windows\\System32",
        "../parent/folder",
        "/usr/local/bin",
    ]
    
    for input_text in path_inputs:
        assert not is_natural_language_input(input_text), f"Should detect '{input_text}' as a path"


def test_ai_integration_argument_parser():
    """Test that AI arguments are properly added to the parser."""
    parser = create_argument_parser()
    
    # Test explicit prompt mode
    args = parser.parse_args(['--prompt', 'extract python files', '.'])
    assert args.prompt == 'extract python files'
    assert args.ai_provider == 'openrouter'  # default
    assert args.no_confirm is False  # default
    
    # Test AI provider selection
    args = parser.parse_args(['--ai-provider', 'openai', '.'])
    assert args.ai_provider == 'openai'
    
    # Test AI model specification
    args = parser.parse_args(['--ai-model', 'gpt-4', '.'])
    assert args.ai_model == 'gpt-4'
    
    # Test no-confirm flag
    args = parser.parse_args(['--no-confirm', '.'])
    assert args.no_confirm is True


def test_get_ai_config():
    """Test AI configuration retrieval from environment."""
    with patch.dict('os.environ', {
        'CODEWEAVE_API_KEY': 'test-key',
        'CODEWEAVE_AI_PROVIDER': 'openai',
        'CODEWEAVE_AI_MODEL': 'gpt-4',
    }):
        config = get_ai_config()
        assert config['api_key'] == 'test-key'
        assert config['provider'] == 'openai'
        assert config['model'] == 'gpt-4'


def test_get_ai_config_fallback_keys():
    """Test that fallback API keys work."""
    with patch.dict('os.environ', {
        'OPENROUTER_API_KEY': 'openrouter-key',
    }, clear=True):
        config = get_ai_config()
        assert config['api_key'] == 'openrouter-key'
    
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'openai-key',
    }, clear=True):
        config = get_ai_config()
        assert config['api_key'] == 'openai-key'


@patch('codeweave.utils.ai.Console')
def test_generate_command_no_api_key(mock_console):
    """Test error handling when no API key is provided."""
    from codeweave.utils.ai import generate_codeweave_command
    
    with patch.dict('os.environ', {}, clear=True):
        result = generate_codeweave_command("test prompt")
        assert result is None
        # Should display error message
        mock_console.return_value.print.assert_called()


@patch('codeweave.utils.ai.Console')
def test_generate_command_no_sdk(mock_console):
    """Test error handling when no AI SDK is available."""
    from codeweave.utils.ai import generate_codeweave_command
    
    with patch.dict('os.environ', {'CODEWEAVE_API_KEY': 'test-key'}):
        # Mock both imports to fail
        with patch('builtins.__import__', side_effect=ImportError):
            result = generate_codeweave_command("test prompt")
            assert result is None
            # Should display error message about missing dependencies
            mock_console.return_value.print.assert_called()


def test_edge_cases_natural_language_detection():
    """Test edge cases for natural language detection."""
    
    # Empty/None inputs
    assert not is_natural_language_input("")
    assert not is_natural_language_input(None)
    assert not is_natural_language_input("   ")
    
    # Ambiguous cases (these could go either way, testing current behavior)
    ambiguous_cases = [
        "test",  # Could be folder name or command
        "project",  # Could be folder name or description
    ]
    
    # These should be treated as paths (single words without clear NL indicators)
    for case in ambiguous_cases:
        assert not is_natural_language_input(case)
    
    # Clear natural language patterns
    clear_nl_cases = [
        "get all files",  # Multiple NL indicators
        "extract files from project",  # Prepositions and action words
        "what is in this folder",  # Question word
        "show me everything",  # Pronouns and action
    ]
    
    for case in clear_nl_cases:
        assert is_natural_language_input(case)