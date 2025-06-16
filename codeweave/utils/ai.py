"""
AI integration utilities for CodeWeave command generation.
Supports OpenRouter, OpenAI, and Anthropic for natural language to CLI command translation.
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel


def is_natural_language_input(input_text: str) -> bool:
    """
    Detect if input string is natural language rather than a file path.
    
    Args:
        input_text: The input string to analyze
        
    Returns:
        True if input appears to be natural language, False if likely a path
    """
    if not input_text or not input_text.strip():
        return False
        
    input_text = input_text.strip()
    
    # Strong indicators it's natural language
    natural_language_indicators = [
        # Question words
        r'\b(what|how|which|where|when|why|can|could|should|would|will)\b',
        # Action words
        r'\b(extract|analyze|process|download|get|find|show|list|include|exclude)\b',
        # Descriptive phrases
        r'\b(all|every|only|just|without|excluding|including)\b',
        # Spaces in the middle (not typical for paths)
        r'\w+\s+\w+',
        # Common natural language patterns
        r'\b(from|to|with|for|in|on|at|by)\b',
    ]
    
    # Strong indicators it's a file path
    path_indicators = [
        # Starts with path-like characters
        r'^[\.\/~]',
        # Contains typical path separators without spaces
        r'^[^\s]*\/[^\s]*$',
        # File extensions
        r'\.(py|js|ts|java|cpp|c|h|md|txt|pdf|zip)$',
        # GitHub URLs
        r'github\.com',
        r'https?://',
        # Windows paths
        r'^[A-Za-z]:\\',
    ]
    
    # Check for path indicators first (more specific)
    for pattern in path_indicators:
        if re.search(pattern, input_text, re.IGNORECASE):
            return False
    
    # Check for natural language indicators
    natural_score = 0
    for pattern in natural_language_indicators:
        if re.search(pattern, input_text, re.IGNORECASE):
            natural_score += 1
    
    # If it has multiple natural language indicators or contains spaces, likely natural language
    return natural_score >= 2 or (' ' in input_text and not any(re.search(p, input_text, re.IGNORECASE) for p in path_indicators))


def get_ai_config() -> Dict[str, str]:
    """
    Get AI provider configuration from environment variables.
    
    Returns:
        Dictionary with AI configuration
    """
    return {
        'provider': os.getenv('CODEWEAVE_AI_PROVIDER', 'openrouter'),
        'api_key': os.getenv('CODEWEAVE_API_KEY') or os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'),
        'model': os.getenv('CODEWEAVE_AI_MODEL', 'openai/gpt-4'),
        'base_url': os.getenv('CODEWEAVE_AI_BASE_URL', 'https://openrouter.ai/api/v1'),
    }


def generate_codeweave_command(prompt: str, provider: str = 'openrouter', model: str = None) -> Optional[str]:
    """
    Generate a CodeWeave command from natural language description using AI.
    
    Args:
        prompt: Natural language description of desired action
        provider: AI provider to use (openrouter, openai, anthropic)
        model: Specific model to use
        
    Returns:
        Generated CodeWeave command string or None if failed
    """
    console = Console()
    
    # Try LiteLLM first (preferred for multi-provider support)
    try:
        import litellm
        use_litellm = True
    except ImportError:
        use_litellm = False
        # Fall back to OpenAI SDK
        try:
            import openai
        except ImportError:
            console.print(Panel(
                "[red]No AI SDK found![/red]\n\n"
                "Install one of:\n"
                "• LiteLLM (recommended): [cyan]pip install litellm[/cyan]\n"
                "• OpenAI SDK: [cyan]pip install openai[/cyan]",
                title="Missing Dependencies",
                border_style="red"
            ))
            return None
    
    config = get_ai_config()
    
    if not config['api_key']:
        console.print(Panel(
            "[red]No AI API key found![/red]\n\n"
            "Set one of these environment variables:\n"
            "• CODEWEAVE_API_KEY (preferred)\n"
            "• OPENROUTER_API_KEY\n"
            "• OPENAI_API_KEY\n"
            "• ANTHROPIC_API_KEY",
            title="Configuration Error",
            border_style="red"
        ))
        return None
    
    # Determine model and setup based on provider
    if use_litellm:
        # LiteLLM uses model prefixes to determine provider
        if provider == 'openai':
            selected_model = model or 'gpt-4'
        elif provider == 'anthropic':
            selected_model = model or 'claude-3-sonnet-20240229'
        elif provider == 'openrouter':
            selected_model = model or 'openrouter/openai/gpt-4'
        else:
            selected_model = model or config['model']
    else:
        # OpenAI SDK fallback - configure for different providers
        if provider == 'openai':
            config['base_url'] = 'https://api.openai.com/v1'
            selected_model = model or 'gpt-4'
        elif provider == 'anthropic':
            config['base_url'] = 'https://api.anthropic.com/v1'
            selected_model = model or 'claude-3-sonnet-20240229'
        else:  # openrouter or custom
            selected_model = model or config['model']
    
    # Get help text for context
    help_text = _get_codeweave_help()
    
    system_prompt = f"""You are a CodeWeave command generator. Convert natural language descriptions into proper CodeWeave CLI commands.

CodeWeave is a tool for aggregating source code from repositories, directories, or zip files.

Available options:
{help_text}

Rules:
1. Generate ONLY the command, no explanation
2. Use appropriate flags based on the user's description
3. If they mention specific languages, use --lang
4. If they want to exclude directories, use --excluded_dirs
5. If they want file trees, use --tree
6. For GitHub repos, detect URLs or assume they mean a repo
7. Use . for current directory if no path specified
8. Always provide a complete, runnable command starting with 'codeweave'

Examples:
Input: "extract all python files from current directory"
Output: codeweave . --lang python

Input: "process github repo for javascript and typescript with tree"
Output: codeweave <repo_url> --lang js,typescript --tree

Input: "get python code excluding tests and virtual environments"
Output: codeweave . --lang python --excluded_dirs tests,test,.venv,venv
"""

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        if use_litellm:
            # Use LiteLLM for unified interface
            import litellm
            
            # Set API keys for LiteLLM
            if provider == 'openai' or selected_model.startswith('gpt'):
                litellm.openai_key = config['api_key']
            elif provider == 'anthropic' or selected_model.startswith('claude'):
                litellm.anthropic_key = config['api_key']
            elif provider == 'openrouter' or selected_model.startswith('openrouter'):
                litellm.openrouter_key = config['api_key']
            
            response = litellm.completion(
                model=selected_model,
                messages=messages,
                max_tokens=200,
                temperature=0.1,
            )
            
            generated_command = response.choices[0].message.content.strip()
            
        else:
            # Use OpenAI SDK as fallback
            import openai
            
            client = openai.OpenAI(
                api_key=config['api_key'],
                base_url=config['base_url'] if provider != 'openai' else None
            )
            
            response = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                max_tokens=200,
                temperature=0.1,
            )
            
            generated_command = response.choices[0].message.content.strip()
        
        # Clean up the command
        if generated_command.startswith('```'):
            generated_command = generated_command.split('\n')[1]
        if generated_command.startswith('$ '):
            generated_command = generated_command[2:]
        if not generated_command.startswith('codeweave'):
            generated_command = f"codeweave {generated_command}"
            
        return generated_command
        
    except Exception as e:
        logging.error(f"Error generating command with AI: {e}")
        console.print(f"[red]Error generating command: {e}[/red]")
        return None


def confirm_and_execute_command(command: str, no_confirm: bool = False) -> bool:
    """
    Display generated command and ask for user confirmation.
    
    Args:
        command: The generated command to display
        no_confirm: Skip confirmation if True
        
    Returns:
        True if user confirms or no_confirm is True, False otherwise
    """
    console = Console()
    
    # Display the generated command
    console.print(Panel(
        f"[bold cyan]{command}[/bold cyan]",
        title="Generated Command",
        border_style="cyan"
    ))
    
    if no_confirm:
        console.print("[yellow]Running command automatically (--no-confirm specified)[/yellow]")
        return True
    
    # Ask for confirmation
    return Confirm.ask("Run this command?", default=True)


def _get_codeweave_help() -> str:
    """Get abbreviated help text for AI context."""
    return """
Input Sources:
  input                 A GitHub repository URL, a local .zip file, or a local folder
  --repo REPO           The name of the GitHub repository
  --zip ZIP             Path to the local .zip file  
  --folder FOLDER       Path to the local folder

File Selection & Filtering:
  --lang LANG           Programming language(s) (comma-separated, e.g., python,pdf)
  --include INCLUDE     Comma-separated list of subfolders/patterns to focus on
  --exclude EXCLUDE     Comma-separated list of file patterns to exclude
  --excluded_dirs DIRS  Comma-separated list of directories to exclude

Content Processing:
  --keep-comments       Keep comments and docstrings in source code
  --tree                Prepend a file tree to the output file
  --topN TOPN           Show top N lines of each file as preview

Output Options:
  --name_append TEXT    Append string to output file name
  --pbcopy              Copy output to clipboard (macOS only)
"""