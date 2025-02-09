import os
import subprocess
from pathlib import Path


def print_header(message):
    print(f"\033[44;30m{message}\033[0m")  # Blue text on a light black background


# Fails build process
# Params:
# +message+:: error message
def fail_script(message):
    raise RuntimeError(f"Build failed! {message}")


# Fails build process if condition is false
# Params:
# +condition+:: bool value to check
# +message+:: error message
def fail_script_unless(condition, message):
    if not condition:
        fail_script(message)


# Fails build process if file or directory does not exist
# Params:
# +path+:: file path to check
def fail_script_unless_file_exists(path):
    if not path or not (os.path.isdir(path) or os.path.exists(path)):
        fail_script(f"File doesn't exist: '{path}'")


# Returns path if file or directory exists or fails build if does not
# Params:
# +path+:: file path to check
def resolve_path(path):
    # Convert to Path object to normalize separators for the platform
    normalized_path = str(Path(path).resolve())
    fail_script_unless_file_exists(normalized_path)
    return normalized_path


def resolve_path_e(path):
    return os.path.abspath(resolve_path(path))


############################################################

def not_nil(value):
    if value is None:
        fail_script('Value is nil')
    return value


############################################################

def not_empty(value):
    """
    Checks if value is not None and not empty.
    Works with strings, lists, and other container types that support len().
    Raises RuntimeError if value is None or empty.
    """
    if value is None:
        fail_script('Value is nil')
    if hasattr(value, '__len__') and len(value) == 0:
        fail_script('Value is empty')
    return value


############################################################

def read_lines(file):
    with open(file, 'r') as f:
        return [line.strip() for line in f]


############################################################

def exec_shell(command, error_message, options=None):
    if options is None:
        options = {}

    if not options.get('silent', False):
        print(f"Running command: {command}")

    result = subprocess.run(command, shell=True, text=True, capture_output=True)

    if options.get('dont_fail_on_error', False):
        if result.returncode != 0:
            print(error_message)
    else:
        fail_script_unless(result.returncode == 0, f"{error_message}\nShell failed: {command}\n{result.stderr.strip()}")

    return result.stdout.strip()


############################################################

def make_relative_path(first, second):
    first_path = Path(first)
    second_path = Path(second)
    return str(first_path.relative_to(second_path))


############################################################

def list_files(path, filter_func=None):
    result = []
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not filter_func or filter_func(file_path):
                result.append(file_path)
    return result
