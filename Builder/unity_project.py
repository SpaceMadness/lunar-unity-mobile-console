import json
import tempfile
from pathlib import Path
import subprocess
from typing import Dict, List, Optional, Union
import os

from platform import Platform


class UnityProject:
    """Handles Unity project operations and command execution."""

    def __init__(self, project_dir: str, unity_binary: str) -> None:
        self.project_dir = str(Path(project_dir).resolve())
        self.unity_binary = str(Path(unity_binary).resolve())

    def exec_unity_method(self, method: str, args: Optional[Dict] = None,
                          error_message: Optional[str] = None) -> str:
        """Execute a Unity method with optional arguments."""
        return self.exec_unity_method_opt(
            self.project_dir, method, args or {}, {}, error_message
        )

    def exec_unity_method_opt(self, project: str, method: str,
                              args: Optional[Dict] = None,
                              options: Optional[Dict] = None,
                              error_message: Optional[str] = None) -> str:
        """Execute a Unity method with additional options."""
        args = args or {}
        options = options or {}

        cmd = [self.unity_binary]
        if 'no_quit' not in options:
            cmd.append('-quit')
        if 'no_batch' not in options:
            cmd.append('-batchmode')

        if args:
            for key, value in args.items():
                cmd.append(f'-{key}')
                cmd.append(value)

        cmd.extend([
            f'-executeMethod', method,
            f'-projectPath', project
        ])

        error_msg = error_message or f"Can't execute method: {method}\nProject: {project}"
        return self._execute_unity_command(cmd, error_msg, working_dir=project)

    def exec_unity(self, project, command, error_message=None):
        self.fail_script_unless_file_exists(project)
        cmd = [self.unity_binary, '-quit', '-batchmode', f'-projectPath "{project}"', command]
        self.exec_shell(cmd, error_message or f"Can't execute unit command: {command}\nProject: {project}")

        unity_log = Platform.unity_log()
        self.fail_script_unless_file_exists(unity_log)

        with open(unity_log, 'r') as file:
            result = file.read()

        if not "Exiting batchmode successfully now!" in result:
            raise RuntimeError(f"Unity batch failed\n{result}")

    def export_unity_package(self, output_file: str, assets: List[str]) -> None:
        """Export Unity package with specified assets."""
        package_assets = [
            str(Path(asset).relative_to(self.project_dir))
            for asset in assets
        ]

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        config_file = Path(tempfile.gettempdir()) / 'lunar_console_config.json'
        with open(config_file, 'w') as f:
            json.dump({"assets": package_assets}, f)

        args = {
            'lunarPackagePath': output_file,
            'lunarConfigPath': config_file
        }


        output = self.exec_unity_method(
            'LunarConsoleEditorInternal.PackageExporter.ExportUnityPackage',
            args,
            f"Can't export Unity package: {output_file}"
        )
        if not Path(output_file).is_file():
            raise FileNotFoundError(f"Unity package export failed - output file not found: {output_file}\n{output}")



    def import_package(self, package_file: str) -> str:
        """Import a Unity package."""
        if not Path(package_file).is_file():
            raise FileNotFoundError(f"Required file not found: {package_file}")

        return self._execute_unity_command(
            [self.unity_binary, '-quit', '-batchmode',
             f'-projectPath', self.project_dir,
             f'-importPackage', package_file],
            f"Can't import unity package: {package_file}"
        )


    def open(self, error_message: Optional[str] = None) -> str:
        """Open the Unity project."""
        cmd = [self.unity_binary, f'-projectPath', self.project_dir]
        return self._execute_unity_command(
            cmd,
            error_message or f"Can't open Unity project: {self.project_dir}"
        )


    @staticmethod
    def make_custom_args(args):
        if args:
            pairs = [f"{name}={value}" for name, value in args.items()]
            return f"-customArgs?{'&'.join(pairs)}"

    @staticmethod
    def resolve_path(path: str) -> str:
        return str(Path(path).resolve())

    @staticmethod
    def exec_shell(cmd, error_message):
        try:
            subprocess.run(cmd, check=True, shell=True)
        except subprocess.CalledProcessError:
            raise RuntimeError(error_message)

    @staticmethod
    def fail_script_unless_file_exists(file_path: str) -> None:
        if not Path(file_path).is_file():
            raise FileNotFoundError(f"Required file not found: {file_path}")

    @staticmethod
    def make_relative_path(file_path: str, base_path: str) -> str:
        return str(Path(file_path).relative_to(base_path))


    # TODO: analyse editor output and print more user friendly error messages.
    def _check_unity_log(self) -> str:
        """Check Unity log for common errors and return the log content.
        
        Raises:
            RuntimeError: If another Unity instance is running or batch mode didn't exit successfully
        """
        log_output = self._read_unity_log()
        if "It looks like another Unity instance is running with this project open." in log_output:
            raise RuntimeError(f"Another Unity instance is running with this project open\n{log_output}")
        if "Exiting batchmode successfully now!" not in log_output:
            raise RuntimeError(f"Unity batch failed\n{log_output}")
        return log_output

    def _execute_unity_command(self, cmd: List[str], error_message: str, working_dir: Optional[str] = None) -> str:
        """Execute a Unity command and verify its success."""
        try:
            # Print command for debugging
            print(f"Executing: {' '.join(str(arg) for arg in cmd)}")
            
            # Execute command using subprocess.run with working_dir as cwd
            result = subprocess.run(
                cmd,
                check=True,  # Raises CalledProcessError if command fails
                capture_output=True,  # Capture stdout and stderr
                text=True,  # Return strings instead of bytes
                cwd=working_dir  # Set working directory for subprocess
            )
            
            return self._check_unity_log()
        
        except subprocess.CalledProcessError as e:
            log_output = self._check_unity_log()
            raise RuntimeError(
                f"{error_message}\n"
                f"Command failed with exit code {e.returncode}\n"
                f"stdout: {e.stdout}\n"
                f"stderr: {e.stderr}\n"
                f"Unity log: {log_output}"
            )
        except Exception as e:
            log_output = self._check_unity_log()
            raise RuntimeError(
                f"{error_message}\n"
                f"Command failed: {str(e)}\n"
                f"Unity log: {log_output}"
            )

    def _read_unity_log(self) -> str:
        unity_log = Platform.unity_log()
        if not Path(unity_log).is_file():
            raise FileNotFoundError(f"Required file not found: {unity_log}")

        with open(unity_log, 'r') as file:
            return file.read()
