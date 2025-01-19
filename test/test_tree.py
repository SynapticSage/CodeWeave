import os
import subprocess
import tempfile
import glob

def test_tree_option(tmp_path):
    """
    Test that running g2f on the current folder with the --tree flag
    prepends a file tree to the output file.
    """

    # Ensure we are in the repository folder.
    cwd = os.getcwd()

    # Set up a temporary working directory and output directory.
    # Note that the script creates an "outputs" folder relative to the current working directory.
    outputs_dir = os.path.join(cwd, "outputs")

    # Remove the outputs folder if it already exists, so the test starts clean
    if os.path.exists(outputs_dir):
        # Remove all files inside; you might want to adjust this if you have real files!
        for filename in os.listdir(outputs_dir):
            filepath = os.path.join(outputs_dir, filename)
            os.remove(filepath)
        os.rmdir(outputs_dir)

    # Construct the command.
    # This assumes that the CLI entry point is available via "g2f" command.
    # If you run the tests via python -m pytest, you might need to execute it like:
    #   python -m g2f ... or call the g2f script specifically.
    command = [
        "python", os.path.join("github2file", "g2f.py"),  # Adjust if your entry point script is named differently or on PATH.
        ".",
        "--tree",
        "--tree_flags", "-L 2",
        "--lang", "python"
    ]

    # Run the command.
    result = subprocess.run(command, capture_output=True, text=True)
    # For debugging purposes you can print result.stderr if the test fails.
    assert result.returncode == 0, f"g2f command failed with error: {result.stderr}"

    # The script should have generated an output file inside the outputs folder.
    assert os.path.exists(outputs_dir), "The outputs directory was not created"

    # Assuming the output file is named something like "<folder>_<lang>.txt", get the file.
    output_files = glob.glob(os.path.join(outputs_dir, "*.txt"))
    assert len(output_files) > 0, "No output file was generated in the outputs directory"

    # Read the contents of the output file.
    output_file = output_files[0]
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Check that the content starts with a file tree.
    # Here we check that there is at least one common tree symbol (this may vary based on your 'tree' command output).
    tree_indicators = ("├──", "└──", ".")
    found = any(ind in content for ind in tree_indicators)
    assert found, "The output file does not appear to contain a prepended file tree"

    # # Cleanup: Optionally remove the generated output file.
    # os.remove(output_file)
    # os.rmdir(outputs_dir)
